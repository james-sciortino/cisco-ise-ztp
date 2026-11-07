import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from ise_ztp.cli import main, parser
from ise_ztp.config import MAX_JSON_BYTES, load_config, read_json
from ise_ztp.errors import ConfigError, PreflightError, ProjectError
from ise_ztp.planning import deployment_plan
from ise_ztp.preflight import run_preflight

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "examples/preflight.example.json"
INVENTORY = ROOT / "examples/inventory.example.json"


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG)
        self.inventory = read_json(INVENTORY)

    def test_fixture_is_successful_but_not_deployment_ready(self):
        report = run_preflight(self.config, self.inventory, "fixture")
        self.assertFalse(report.failed)
        self.assertFalse(report.to_dict()["deployment_ready"])
        self.assertTrue(any(c.status == "SKIP" for c in report.checks))
        self.assertTrue(any(c.status == "WARN" for c in report.checks))

    def test_offline_cannot_claim_host_pass(self):
        report = run_preflight(self.config)
        self.assertEqual([c.id for c in report.checks if c.status == "PASS"], ["config"])
        self.assertEqual(report.mode, "offline")

    def test_bad_host_states_fail(self):
        for key, value in (("api_type", "VirtualCenter"), ("version", "6.7.0"),
                           ("version", "8.01"), ("version", "8.0.invalid"), ("maintenance_mode", True),
                           ("connection_state", "disconnected"), ("cpu_threads", 8),
                           ("cpu_mhz", 1900), ("memory_bytes", 1024),
                           ("memory_used_mb", 125000)):
            with self.subTest(key=key, value=value):
                inventory = copy.deepcopy(self.inventory)
                inventory[key] = value
                self.assertTrue(run_preflight(self.config, inventory).failed)

    def test_missing_memory_metric_is_warning(self):
        self.inventory["memory_used_mb"] = None
        report = run_preflight(self.config, self.inventory)
        self.assertFalse(report.failed)
        self.assertIn(("memory_available", "WARN"), [(c.id, c.status) for c in report.checks])

    def test_storage_and_network_failures(self):
        for section, key, value in (("datastores", "accessible", False),
                                    ("datastores", "free_bytes", 1),
                                    ("datastores", "maintenance_mode", "inMaintenance"),
                                    ("networks", "standard", False),
                                    ("networks", "accessible", False)):
            with self.subTest(section=section, key=key):
                inventory = copy.deepcopy(self.inventory)
                inventory[section][0][key] = value
                self.assertTrue(run_preflight(self.config, inventory).failed)

    def test_missing_and_ambiguous_inventory_fails(self):
        for section in ("datastores", "networks"):
            for items in ([], self.inventory[section] * 2):
                with self.subTest(section=section, count=len(items)):
                    inventory = copy.deepcopy(self.inventory)
                    inventory[section] = items
                    self.assertTrue(run_preflight(self.config, inventory).failed)

    def test_existing_vm_is_never_reused(self):
        self.inventory["vm_names"].append(self.config.vm["name"])
        self.assertTrue(run_preflight(self.config, self.inventory).failed)

    def test_inaccessible_storage_never_passes_capacity_check(self):
        self.inventory["datastores"][0]["accessible"] = False
        report = run_preflight(self.config, self.inventory)
        self.assertTrue(report.failed)
        self.assertIn(("storage_capacity", "SKIP"), [(c.id, c.status) for c in report.checks])

    def test_unknown_selected_capacity_fails(self):
        self.inventory["datastores"][0]["free_bytes"] = None
        report = run_preflight(self.config, self.inventory)
        self.assertIn(("storage_capacity", "FAIL"), [(c.id, c.status) for c in report.checks])

    def test_unrelated_inaccessible_datastore_does_not_abort_preflight(self):
        self.inventory["datastores"].append({"name": "unrelated", "accessible": False,
                                              "free_bytes": None, "maintenance_mode": "unknown"})
        self.assertFalse(run_preflight(self.config, self.inventory).failed)

    def test_inventory_rejects_bad_types_and_unknown_fields(self):
        for key, value in (("maintenance_mode", "false"), ("cpu_threads", True),
                           ("networks", {}), ("password", "SENSITIVE_SENTINEL")):
            inventory = copy.deepcopy(self.inventory)
            inventory[key] = value
            with self.subTest(key=key), self.assertRaises(ConfigError):
                run_preflight(self.config, inventory)

    def test_report_does_not_include_inventory_identifiers(self):
        report = json.dumps(run_preflight(self.config, self.inventory).to_dict())
        for value in (self.config.esxi["host"], self.config.vm["name"], self.config.vm["datastore"]):
            self.assertNotIn(value, report)


class ConfigTests(unittest.TestCase):
    def load_modified(self, modify):
        data = read_json(CONFIG)
        modify(data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(data))
            return load_config(path)

    def test_inline_credentials_and_invalid_settings_rejected(self):
        modifications = [
            lambda d: d["esxi"].update(password="SENSITIVE_SENTINEL"),
            lambda d: d["esxi"].update(host="https://user:password@example.invalid"),
            lambda d: d["esxi"].update(port=True),
            lambda d: d["esxi"].update(timeout_seconds=0),
            lambda d: d["esxi"].update(username_env="a real username"),
            lambda d: d["esxi"].update(password_env="ESXI_USERNAME"),
            lambda d: d["vm"].update(vcpus=-1),
            lambda d: d["vm"].update(name="bad\nname"),
            lambda d: d["policy"].update(allowed_esxi_versions=["6.7"]),
            lambda d: d.update(schema_version=True),
        ]
        for modify in modifications:
            with self.subTest(modify=modify), self.assertRaises(ConfigError) as caught:
                self.load_modified(modify)
            self.assertNotIn("SENSITIVE_SENTINEL", str(caught.exception))

    def test_old_direct_host_configuration_rejected(self):
        with self.assertRaises(ConfigError):
            self.load_modified(lambda d: d["esxi"].update(ca_file="trust.pem"))

    def test_mcp_cannot_select_admin_shell_or_unreviewed_trust(self):
        changes = [
            {"command": "python"}, {"user": "root"}, {"port": True},
            {"timeout_seconds": 0}, {"host": "-oProxyCommand=bad"},
            {"identity_file": "relative-key"}, {"identity_file": "/keys/%h"},
            {"known_hosts_file": "/keys/$USER"}, {"host_key_sha256": "unverified"},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ConfigError):
                self.load_modified(lambda d: d["mcp"].update(change))

    def test_invalid_hostnames_rejected_before_any_connection(self):
        for host in ("esxi..invalid", "esxi.-invalid", "esxi-.invalid", "a" * 64 + ".invalid",
                     "999.1.2.3", "127.1", "esxi\x7f.invalid"):
            with self.subTest(host=host), self.assertRaises(ConfigError):
                self.load_modified(lambda d: d["esxi"].update(host=host))

    def test_valid_hostname_and_ip_forms(self):
        for host in ("esxi", "esxi.example.invalid", "esxi.example.invalid.", "192.0.2.10", "2001:db8::10"):
            with self.subTest(host=host):
                self.assertEqual(self.load_modified(lambda d: d["esxi"].update(host=host)).esxi["host"], host)

    def test_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for value in ("NaN", "Infinity", "-Infinity"):
                path.write_text('{"value":' + value + '}')
                with self.subTest(value=value), self.assertRaises(ConfigError):
                    read_json(path)

    def test_json_read_limit_and_special_file_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_bytes(b" " * (MAX_JSON_BYTES + 1))
            with self.assertRaisesRegex(ConfigError, "1 MiB"):
                read_json(path)
            with self.assertRaises(ConfigError):
                read_json(Path(directory))
        if os.name == "posix":
            with self.assertRaisesRegex(ConfigError, "regular file"):
                read_json(Path(os.devnull))

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Requires POSIX named pipes")
    def test_named_pipe_rejected_without_waiting_for_a_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "input.json"
            os.mkfifo(fifo)
            result = subprocess.run(
                [sys.executable, "-m", "ise_ztp", "preflight", "--config", str(fifo)],
                cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
                text=True, capture_output=True, timeout=5, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("regular file", result.stderr)

    def test_bad_and_duplicate_json_does_not_echo_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for value in ('{"secret":"SENSITIVE_SENTINEL",', '{"a":1,"a":2}', '[]'):
                path.write_text(value)
                with self.assertRaises(ConfigError) as caught:
                    read_json(path)
                self.assertNotIn("SENSITIVE_SENTINEL", str(caught.exception))


class CliSafetyTests(unittest.TestCase):
    def setUp(self):
        patcher = patch("ise_ztp.cli.Audit")
        self.audit = patcher.start()
        self.addCleanup(patcher.stop)

    def invoke(self, arguments):
        output = io.StringIO()
        if "--live" in arguments:
            arguments = arguments + ["--audit-dir", "/private/test-audit"]
        with redirect_stdout(output):
            code = main(arguments)
        return code, output.getvalue()

    def test_offline_modes_never_connect(self):
        cases = [[], ["--dry-run"], ["--inventory", str(INVENTORY)]]
        with patch("ise_ztp.cli.collect_inventory") as collect, patch("socket.create_connection", side_effect=AssertionError("network forbidden")):
            for flags in cases:
                code, output = self.invoke(["preflight", "--config", str(CONFIG), "--format", "json"] + flags)
                self.assertEqual(code, 0)
                self.assertFalse(json.loads(output)["deployment_ready"])
            collect.assert_not_called()

    def test_mutually_exclusive_live_and_offline(self):
        with redirect_stdout(io.StringIO()), patch("sys.stderr", new_callable=io.StringIO):
            for flags in (["--live", "--dry-run"], ["--live", "--inventory", str(INVENTORY)]):
                with self.assertRaises(SystemExit) as caught:
                    parser().parse_args(["preflight", "--config", str(CONFIG)] + flags)
                self.assertEqual(caught.exception.code, 2)

    def test_abbreviated_live_option_cannot_enable_connection(self):
        with patch("ise_ztp.cli.collect_inventory") as collect, patch("sys.stderr", new_callable=io.StringIO):
            for option in ("--l", "--li", "--liv"):
                with self.subTest(option=option), self.assertRaises(SystemExit) as caught:
                    self.invoke(["preflight", "--config", str(CONFIG), option])
                self.assertEqual(caught.exception.code, 2)
            collect.assert_not_called()

    def test_deploy_requires_dry_run_and_never_connects(self):
        with patch("ise_ztp.cli.collect_inventory") as collect:
            code, output = self.invoke(["deploy", "--config", str(CONFIG), "--dry-run"])
            self.assertEqual(code, 0)
            self.assertFalse(json.loads(output)["executable"])
            code, output = self.invoke(["deploy", "--config", "does-not-exist.json"])
            self.assertEqual(code, 2)
            collect.assert_not_called()
        with self.assertRaises(ProjectError):
            deployment_plan(load_config(CONFIG), False)

    def test_live_dispatch_with_mock_only(self):
        with patch("ise_ztp.cli.collect_inventory", return_value=read_json(INVENTORY)) as collect:
            code, output = self.invoke(["preflight", "--config", str(CONFIG), "--live", "--format", "json"])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output)["mode"], "live")
            collect.assert_called_once()

    def test_failed_predicate_exit_one(self):
        inventory = read_json(INVENTORY)
        inventory["maintenance_mode"] = True
        with patch("ise_ztp.cli.collect_inventory", return_value=inventory):
            code, _ = self.invoke(["preflight", "--config", str(CONFIG), "--live"])
            self.assertEqual(code, 1)

    def test_unexpected_exception_is_not_logged_verbatim(self):
        with patch("ise_ztp.cli.collect_inventory", side_effect=RuntimeError("SENSITIVE_SENTINEL")), self.assertLogs("ise_ztp", level="ERROR") as logs:
            code, _ = self.invoke(["preflight", "--config", str(CONFIG), "--live"])
        self.assertEqual(code, 2)
        self.assertNotIn("SENSITIVE_SENTINEL", " ".join(logs.output))


class GitHygieneTests(unittest.TestCase):
    def test_sensitive_paths_ignored_and_example_trackable(self):
        sensitive = ["local/preflight.json", "local/inventory.json", "local/ise-ztp.conf", "ise-ztp.conf",
                     "local/anything.txt", "payload.b64", ".env", ".env.production", "private.key",
                     "backups/original.tar.gpg", "secret.pem", "installer.iso", "vm.ova", "run.log",
                     "payload.base64", "id_ecdsa", "putty.ppk", "private.der", "trust.jks",
                     "codex_ise_mcp_ed25519", "service.pub", "private_known_hosts", "actual-inventory.json"]
        result = subprocess.run(["git", "check-ignore", "--no-index", "--stdin"], input="\n".join(sensitive) + "\n",
                                cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), set(sensitive))
        result = subprocess.run(["git", "check-ignore", "--no-index", "examples/ise-ztp.conf.example"],
                                cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
