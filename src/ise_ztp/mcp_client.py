"""Fixed read-only MCP calls over a pinned SSH transport; no direct ESXi access."""

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import re
import stat
import subprocess

from .config import MAX_JSON_BYTES, _reject_constant, _unique_object
from .errors import PreflightError

TOOLS = ("esxi_host_health", "esxi_vm_inventory", "esxi_datastore_usage", "esxi_snapshot_inventory")


def ssh_arguments(settings):
    options = {
        "UserKnownHostsFile": '"' + settings["known_hosts_file"] + '"', "GlobalKnownHostsFile": "/dev/null",
        "HostKeyAlgorithms": "ssh-ed25519", "StrictHostKeyChecking": "yes",
        "IdentitiesOnly": "yes", "IdentityAgent": "none", "BatchMode": "yes",
        "PasswordAuthentication": "no", "KbdInteractiveAuthentication": "no",
        "ForwardAgent": "no", "ClearAllForwardings": "yes", "ControlMaster": "no",
        "ControlPath": "none", "RequestTTY": "no", "PermitLocalCommand": "no",
        "ProxyCommand": "none", "ProxyJump": "none", "ConnectTimeout": "10",
        "ServerAliveInterval": "15", "ServerAliveCountMax": "2",
    }
    args = ["-F", "/dev/null", "-T", "-i", settings["identity_file"],
            "-p", str(settings["port"]), "-l", settings["user"]]
    for key, value in options.items():
        args += ["-o", key + "=" + value]
    return args + [settings["host"]]  # Deliberately no remote command.


def verify_local_trust(settings):
    for key in ("identity_file", "known_hosts_file"):
        info = Path(settings[key]).lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
            raise PreflightError("SSH key and pinned-host files must be regular, owned files with mode 600.")
    result = subprocess.run(["/usr/bin/ssh-keygen", "-lf", settings["known_hosts_file"], "-E", "sha256"],
                            capture_output=True, text=True, timeout=5, check=False)
    rows = [line.split() for line in result.stdout.splitlines()]
    if (result.returncode or len(rows) != 1 or len(rows[0]) < 3
            or rows[0][1] != settings["host_key_sha256"] or rows[0][-1] != "(ED25519)"):
        raise PreflightError("Pinned host key does not match the separately verified Ed25519 fingerprint.")


def verify_tools(discovered):
    if discovered.nextCursor or len(discovered.tools) != len(TOOLS) or {t.name for t in discovered.tools} != set(TOOLS):
        raise PreflightError("MCP discovery differs from the exact four-tool read-only allowlist.")
    for tool in discovered.tools:
        a, schema = tool.annotations, tool.inputSchema
        if not a or a.readOnlyHint is not True or a.destructiveHint is not False:
            raise PreflightError("MCP tool annotations differ from the reviewed read-only contract.")
        if schema.get("type") != "object" or schema.get("properties", {}) or schema.get("required", []):
            raise PreflightError("MCP tool has unexpected input parameters.")


def decode_result(result, requested_at):
    if result.isError:
        raise PreflightError("MCP read failed; inspect server-side diagnostics through the administrator.")
    if result.structuredContent is not None:
        raw = json.dumps(result.structuredContent, allow_nan=False)
    else:
        if len(result.content) != 1 or result.content[0].type != "text":
            raise PreflightError("Unexpected MCP response format.")
        raw = result.content[0].text
    if len(raw.encode("utf-8")) > MAX_JSON_BYTES:
        raise PreflightError("MCP response exceeds the 1 MiB application limit.")
    data = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    if not isinstance(data, dict):
        raise PreflightError("MCP response must be an object.")
    observed = datetime.fromisoformat(data["observed_at"].replace("Z", "+00:00"))
    if observed.tzinfo is None or observed < requested_at - timedelta(seconds=60) or observed > datetime.now(timezone.utc) + timedelta(seconds=60):
        raise PreflightError("MCP observation is stale or has an invalid clock; verify server time.")
    return data


def require_target(data, expected_host):
    hosts = data.get("hosts")
    if not isinstance(hosts, list) or len(hosts) != 1 or str(hosts[0].get("name", "")).lower().rstrip(".") != expected_host.lower().rstrip("."):
        raise PreflightError("Host-health response does not identify exactly the approved ESXi host.")


def project_inventory(results):
    host = results[TOOLS[0]]["hosts"][0]
    version = re.fullmatch(r"VMware ESXi (\d+\.\d+(?:\.\d+)*) build-\d+", host["version"])
    if not version:
        raise PreflightError("Unrecognized ESXi version response; review before extending the parser.")
    vms, stores, snapshots = results[TOOLS[1]], results[TOOLS[2]], results[TOOLS[3]]
    for data, key in ((vms, "vms"), (stores, "datastores"), (snapshots, "snapshots"), (snapshots, "skipped_vms")):
        if not isinstance(data.get(key), list):
            raise PreflightError("MCP inventory collection is missing or malformed.")
    if type(vms.get("count")) is not int or vms["count"] != len(vms["vms"]):
        raise PreflightError("VM count does not match the returned inventory.")
    if type(snapshots.get("count")) is not int or snapshots["count"] != len(snapshots["snapshots"]):
        raise PreflightError("Snapshot count does not match the returned inventory.")
    if type(snapshots.get("complete")) is not bool or snapshots["complete"] != (not snapshots["skipped_vms"]):
        raise PreflightError("Snapshot completeness metadata is inconsistent.")
    # Project only required fields. Do not invent properties absent from these tools.
    inventory = {
        "host_name": host["name"], "api_type": None, "version": version[1],
        "connection_state": host["connection_state"], "power_state": host["power_state"],
        "maintenance_mode": host["maintenance_mode"], "overall_status": host["overall_status"],
        "cpu_threads": None, "cpu_mhz": None, "memory_bytes": host["memory_capacity_bytes"],
        "memory_used_mb": host["memory_used_mib"], "networks": None,
        "datastores": [{"name": d["name"], "accessible": d["accessible"],
                        "free_bytes": d["free_bytes"] if d["accessible"] is True else None,
                        "maintenance_mode": None} for d in stores["datastores"]],
        "vm_names": [v["name"] for v in vms["vms"]],
        "snapshot_count": snapshots["count"], "snapshots_complete": snapshots["complete"],
        "observed_at": {tool: results[tool]["observed_at"] for tool in TOOLS},
    }
    from .preflight import validate_inventory
    validate_inventory(inventory)
    return inventory


async def query_session(client, config, audit):
    await client.initialize()
    verify_tools(await client.list_tools())
    audit.event("discovery_passed", tool_count=len(TOOLS))
    results = {}
    for tool in TOOLS:
        audit.event("tool_requested", tool=tool)
        requested = datetime.now(timezone.utc)
        data = decode_result(await client.call_tool(tool, {}), requested)
        if tool == TOOLS[0]:
            require_target(data, config.esxi["host"])
        results[tool] = data
        audit.event("tool_succeeded", tool=tool)
    return project_inventory(results)


async def _collect(config, audit):
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        raise PreflightError("Live mode requires the optional mcp dependency.") from None
    params = StdioServerParameters(command="/usr/bin/ssh", args=ssh_arguments(config.mcp),
                                   env={"PATH": "/usr/bin:/bin"}, cwd="/")
    # SDK parsing failures may include raw response text. Suppress third-party
    # logging for this CLI's transport phase; use our fixed audit events instead.
    disabled = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with open(os.devnull, "w") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=config.mcp["timeout_seconds"])) as client:
                    return await query_session(client, config, audit)
    finally:
        logging.disable(disabled)


def collect_inventory(config, audit):
    try:
        verify_local_trust(config.mcp)
        inventory = asyncio.run(asyncio.wait_for(_collect(config, audit), timeout=20 + 5 * config.mcp["timeout_seconds"]))
        audit.write("inventory.json", inventory)
        audit.event("collection_completed")
        return inventory
    except KeyboardInterrupt:
        audit.event("collection_interrupted")
        raise
    except Exception:
        audit.event("collection_failed")
        # Do not log exception groups, SDK errors, SSH stderr, or remote text.
        raise PreflightError("MCP collection failed. Check the reviewed transport, host pin, server clock, tool contract and server-side connectivity. Raw errors suppressed; no automatic retry.") from None
