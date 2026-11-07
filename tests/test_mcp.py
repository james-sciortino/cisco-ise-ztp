from datetime import datetime, timedelta, timezone
import io
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch

from ise_ztp.audit import Audit
from ise_ztp.cli import main
from ise_ztp.config import load_config, read_json
from ise_ztp.errors import ConfigError, PreflightError
from ise_ztp.mcp_client import (TOOLS, collect_inventory, decode_result, query_session,
                               ssh_arguments, verify_local_trust, verify_tools)
from ise_ztp.preflight import run_preflight

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'examples/preflight.example.json'


def discovery():
    return NS(nextCursor=None, tools=[NS(name=name, annotations=NS(readOnlyHint=True, destructiveHint=False),
                                       inputSchema={'type': 'object', 'properties': {}}) for name in TOOLS])


def responses():
    timestamp = datetime.now(timezone.utc).isoformat()
    data = [
        {'hosts': [{'name': 'esxi.example.invalid', 'version': 'VMware ESXi 8.0.3 build-12345',
                    'connection_state': 'connected', 'power_state': 'poweredOn', 'maintenance_mode': False,
                    'overall_status': 'gray', 'memory_capacity_bytes': 128 * 2**30, 'memory_used_mib': 16384}]},
        {'count': 1, 'vms': [{'name': 'unrelated-example-vm'}]},
        {'datastores': [{'name': 'example-datastore', 'accessible': True, 'free_bytes': 2**41}]},
        {'count': 0, 'snapshots': [], 'complete': True, 'skipped_vms': []},
    ]
    return {tool: dict(row, observed_at=timestamp) for tool, row in zip(TOOLS, data)}


class FakeSession:
    def __init__(self):
        self.discovery = discovery()
        self.responses = responses()
        self.calls = []

    async def initialize(self):
        return NS()

    async def list_tools(self):
        return self.discovery

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return NS(isError=False, structuredContent=self.responses[name], content=[])


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = load_config(CONFIG)
        self.session = FakeSession()
        self.audit = Mock()

    async def test_exact_calls_and_missing_capabilities_remain_unknown(self):
        inventory = await query_session(self.session, self.config, self.audit)
        self.assertEqual(self.session.calls, [(tool, {}) for tool in TOOLS])
        for field in ('api_type', 'cpu_threads', 'cpu_mhz', 'networks'):
            self.assertIsNone(inventory[field])
        self.assertIsNone(inventory['datastores'][0]['maintenance_mode'])
        report = run_preflight(self.config, inventory, 'live')
        states = {c.id: c.status for c in report.checks}
        for field in ('endpoint', 'cpu_count', 'cpu_frequency', 'port_group', 'datastore_maintenance'):
            self.assertEqual(states[field], 'SKIP')
        self.assertEqual(states['host_health'], 'WARN')
        self.assertFalse(report.to_dict()['deployment_ready'])
        self.assertEqual(report.to_dict()['status'], 'incomplete')

    async def test_wrong_host_stops_before_inventory_queries(self):
        self.session.responses[TOOLS[0]]['hosts'][0]['name'] = 'wrong.invalid'
        with self.assertRaises(PreflightError):
            await query_session(self.session, self.config, self.audit)
        self.assertEqual(self.session.calls, [(TOOLS[0], {})])

    async def test_ambiguous_host_stops(self):
        self.session.responses[TOOLS[0]]['hosts'] *= 2
        with self.assertRaises(PreflightError):
            await query_session(self.session, self.config, self.audit)
        self.assertEqual(len(self.session.calls), 1)

    async def test_stale_response_stops_before_other_queries(self):
        self.session.responses[TOOLS[0]]['observed_at'] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        with self.assertRaises(PreflightError):
            await query_session(self.session, self.config, self.audit)
        self.assertEqual(len(self.session.calls), 1)

    async def test_added_tool_stops_before_any_query(self):
        self.session.discovery.tools.append(NS(name='esxi_delete_vm'))
        with self.assertRaises(PreflightError):
            await query_session(self.session, self.config, self.audit)
        self.assertEqual(self.session.calls, [])

    async def test_count_mismatch_rejected(self):
        self.session.responses[TOOLS[1]]['count'] = 2
        with self.assertRaises(PreflightError):
            await query_session(self.session, self.config, self.audit)

    async def test_incomplete_snapshots_warn(self):
        self.session.responses[TOOLS[3]].update(complete=False, skipped_vms=[{'name': 'offline-example'}])
        inventory = await query_session(self.session, self.config, self.audit)
        self.assertFalse(inventory['snapshots_complete'])
        report = run_preflight(self.config, inventory)
        self.assertIn(('snapshots', 'WARN'), [(c.id, c.status) for c in report.checks])

    async def test_inaccessible_datastore_discards_capacity(self):
        self.session.responses[TOOLS[2]]['datastores'][0]['accessible'] = False
        inventory = await query_session(self.session, self.config, self.audit)
        self.assertIsNone(inventory['datastores'][0]['free_bytes'])
        self.assertTrue(run_preflight(self.config, inventory).failed)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG)

    def test_discovery_rejects_pagination_annotations_and_parameters(self):
        variants = []
        d = discovery(); d.nextCursor = 'more'; variants.append(d)
        d = discovery(); d.tools[0].annotations.readOnlyHint = False; variants.append(d)
        d = discovery(); d.tools[0].annotations.destructiveHint = True; variants.append(d)
        d = discovery(); d.tools[0].inputSchema['properties'] = {'command': {'type': 'string'}}; variants.append(d)
        for item in variants:
            with self.subTest(item=item), self.assertRaises(PreflightError):
                verify_tools(item)

    def test_ssh_ignores_shared_config_agent_and_remote_commands(self):
        args = ssh_arguments(self.config.mcp)
        self.assertEqual(args[:3], ['-F', '/dev/null', '-T'])
        self.assertEqual(args[-1], self.config.mcp['host'])
        for option in ('StrictHostKeyChecking=yes', 'IdentityAgent=none', 'IdentitiesOnly=yes',
                       'ClearAllForwardings=yes', 'ProxyCommand=none', 'ProxyJump=none',
                       'HostKeyAlgorithms=ssh-ed25519', 'ControlPath=none'):
            self.assertIn(option, args)
        self.assertNotIn('-L', args)
        self.assertNotIn('-R', args)

    def test_pin_and_file_permissions_checked_before_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            for key in ('identity_file', 'known_hosts_file'):
                p = Path(directory) / key
                p.write_text('synthetic')
                p.chmod(0o600)
                self.config.mcp[key] = str(p)
            fingerprint = self.config.mcp['host_key_sha256']
            ok = NS(returncode=0, stdout=f'256 {fingerprint} example (ED25519)\n')
            with patch('ise_ztp.mcp_client.subprocess.run', return_value=ok):
                verify_local_trust(self.config.mcp)
                Path(self.config.mcp['identity_file']).chmod(0o644)
                with self.assertRaises(PreflightError):
                    verify_local_trust(self.config.mcp)
                Path(self.config.mcp['identity_file']).chmod(0o600)
                ok.stdout = '256 SHA256:wrong example (ED25519)\n'
                with self.assertRaises(PreflightError):
                    verify_local_trust(self.config.mcp)

    def test_timeout_is_scrubbed_and_not_retried(self):
        collect = AsyncMock(side_effect=TimeoutError('SENSITIVE_SENTINEL'))
        with patch('ise_ztp.mcp_client.verify_local_trust'), patch('ise_ztp.mcp_client._collect', collect):
            with self.assertRaises(PreflightError) as caught:
                collect_inventory(self.config, Mock())
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))
        self.assertEqual(collect.await_count, 1)

    def test_untrusted_error_content_never_echoed(self):
        result = NS(isError=True, structuredContent=None, content=[NS(type='text', text='SENSITIVE_SENTINEL')])
        with self.assertRaises(PreflightError) as caught:
            decode_result(result, datetime.now(timezone.utc))
        self.assertNotIn('SENSITIVE_SENTINEL', str(caught.exception))

    def test_oversized_and_duplicate_response_rejected(self):
        for text in ('x' * (1024 * 1024 + 1), '{"a":1,"a":2}'):
            result = NS(isError=False, structuredContent=None, content=[NS(type='text', text=text)])
            with self.assertRaises((PreflightError, ConfigError)):
                decode_result(result, datetime.now(timezone.utc))

    def test_live_requires_audit_before_transport(self):
        with patch('ise_ztp.cli.collect_inventory') as collect, patch('sys.stdout', new=io.StringIO()):
            self.assertEqual(main(['preflight', '--config', str(CONFIG), '--live']), 2)
            collect.assert_not_called()


class AuditTests(unittest.TestCase):
    def test_private_evidence_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            audit = Audit(Path(directory).resolve())
            audit.event('tool_requested', tool=TOOLS[0])
            audit.write('report.json', {'deployment_ready': False})
            self.assertEqual(stat.S_IMODE(audit.path.stat().st_mode), 0o700)
            for path in audit.path.iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                audit.write('report.json', {})
            with self.assertRaises(PreflightError):
                audit.write('../arbitrary.json', {})

    def test_rejects_checkout_and_public_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / '.git').mkdir()
            with self.assertRaises(PreflightError):
                Audit(root)
            (root / '.git').rmdir()
            root.chmod(0o755)
            with self.assertRaises(PreflightError):
                Audit(root)
