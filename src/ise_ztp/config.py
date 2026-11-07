"""Strict local JSON settings. These are project options, NOT Cisco ZTP keys."""

import ipaddress
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .errors import ConfigError

MAX_JSON_BYTES = 1024 * 1024


def _reject_constant(value):
    raise ConfigError("Non-finite numbers are not valid JSON input.")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("Duplicate JSON keys are not allowed.")
        result[key] = value
    return result


def read_json(path: Path) -> Dict[str, Any]:
    try:
        # O_NONBLOCK prevents a named pipe from hanging before we can reject it.
        # Check the opened descriptor, not a separate path stat (which can race).
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ConfigError("JSON input must be a regular file.")
            raw = stream.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ConfigError("JSON input exceeds the 1 MiB limit.")
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_reject_constant)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise ConfigError("Cannot read valid UTF-8 JSON; check the local file and its syntax.") from None
    if not isinstance(data, dict):
        raise ConfigError("JSON input must be an object.")
    return data


def fields(data, required, optional=()):
    if not isinstance(data, dict) or set(data) - set(required) - set(optional) or set(required) - set(data):
        raise ConfigError("Missing or unknown configuration fields; compare with the example schema.")


def text_value(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 255 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ConfigError("Text fields must be nonempty, at most 255 characters, with no control characters.")


def integer(value, minimum=1, maximum=10000000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ConfigError("An integer field is outside its allowed range.")


@dataclass(frozen=True, repr=False)
class Config:
    mcp: Dict[str, Any]
    esxi: Dict[str, Any]
    vm: Dict[str, Any]
    policy: Dict[str, Any]


def load_config(path: Path) -> Config:
    data = read_json(path)
    fields(data, ("schema_version", "mcp", "esxi", "vm", "policy"))
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise ConfigError("Only schema_version 2 is supported; migrate direct-host settings to MCP.")
    esxi, vm, policy = data["esxi"], data["vm"], data["policy"]
    mcp = data["mcp"]
    fields(esxi, ("host",))
    fields(mcp, ("host", "port", "user", "identity_file", "known_hosts_file", "host_key_sha256", "timeout_seconds"))
    for host in (esxi["host"], mcp["host"]):
        hostname_value(host)
    if mcp["user"] != "svc-mcp":
        raise ConfigError("This transport is restricted to the reviewed svc-mcp runtime account.")
    integer(mcp["port"], 1, 65535)
    integer(mcp["timeout_seconds"], 5, 120)
    if not isinstance(mcp["host_key_sha256"], str) or not re.fullmatch(r"SHA256:[A-Za-z0-9+/]{43}", mcp["host_key_sha256"]):
        raise ConfigError("A separately verified Ed25519 server SHA256 fingerprint is required.")
    for key in ("identity_file", "known_hosts_file"):
        text_value(mcp[key])
        value = Path(mcp[key]).expanduser()
        if not value.is_absolute():
            raise ConfigError("SSH identity and host-pin paths must be absolute.")
        if any(c in str(value) for c in '%$"\\'):
            raise ConfigError("SSH paths must not contain expansion tokens, quotes or backslashes.")
        mcp[key] = str(value)
    if mcp["identity_file"] == mcp["known_hosts_file"]:
        raise ConfigError("SSH identity and host-pin files must be distinct.")
    fields(vm, ("name", "datastore", "port_group", "vcpus", "memory_gib", "disk_gib", "cpu_reservation_mhz"))
    for key in ("name", "datastore", "port_group"):
        text_value(vm[key])
    for key in ("vcpus", "memory_gib", "disk_gib", "cpu_reservation_mhz"):
        integer(vm[key])
    fields(policy, ("allowed_esxi_versions", "datastore_headroom_gib"))
    versions = policy["allowed_esxi_versions"]
    if not isinstance(versions, list) or not versions or any(v not in ("7.0", "8.0", "9.0") for v in versions):
        raise ConfigError("Version policy must select reviewed ISE 3.5 ESXi families: 7.0, 8.0, or 9.0.")
    integer(policy["datastore_headroom_gib"], 0)
    return Config(mcp, esxi, vm, policy)


def hostname_value(value):
    text_value(value)
    try:
        ipaddress.ip_address(value)
    except ValueError:
        hostname = value.removesuffix(".")
        labels = hostname.split(".")
        valid_label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        if (len(hostname) > 253 or all(c in "0123456789." for c in hostname)
                or not all(re.fullmatch(valid_label, label) for label in labels)):
            raise ConfigError("Endpoint must be a hostname or IP address, not a URL or credentials.") from None
