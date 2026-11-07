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
    esxi: Dict[str, Any]
    vm: Dict[str, Any]
    policy: Dict[str, Any]


def load_config(path: Path) -> Config:
    data = read_json(path)
    fields(data, ("schema_version", "esxi", "vm", "policy"))
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ConfigError("Only schema_version 1 is supported.")
    esxi, vm, policy = data["esxi"], data["vm"], data["policy"]
    fields(esxi, ("host", "port", "username_env", "password_env", "timeout_seconds"), ("ca_file",))
    for key in ("host", "username_env", "password_env"):
        text_value(esxi[key])
    try:
        ipaddress.ip_address(esxi["host"])
    except ValueError:
        hostname = esxi["host"].removesuffix(".")
        labels = hostname.split(".")
        valid_label = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        if (len(hostname) > 253 or all(c in "0123456789." for c in hostname)
                or not all(re.fullmatch(valid_label, label) for label in labels)):
            raise ConfigError("ESXi host must be a hostname or IP address, not a URL or credentials.") from None
    for key in ("username_env", "password_env"):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", esxi[key]):
            raise ConfigError("Credential references must be uppercase environment variable names.")
    if esxi["username_env"] == esxi["password_env"]:
        raise ConfigError("Username and password references must be different.")
    integer(esxi["port"], 1, 65535)
    integer(esxi["timeout_seconds"], 1, 120)
    if "ca_file" in esxi:
        text_value(esxi["ca_file"])
        ca = Path(esxi["ca_file"]).expanduser()
        esxi["ca_file"] = str(ca if ca.is_absolute() else path.resolve().parent / ca)
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
    return Config(esxi, vm, policy)
