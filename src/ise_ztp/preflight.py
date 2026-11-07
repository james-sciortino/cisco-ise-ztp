"""Pure checks shared by offline fixtures and the live read-only adapter."""

import re
from dataclasses import asdict, dataclass
from typing import List

from .config import Config, fields, integer, text_value
from .errors import ConfigError

GIB = 1024 ** 3


@dataclass(frozen=True)
class Check:
    id: str
    status: str
    message: str


@dataclass
class Report:
    mode: str
    checks: List[Check]

    @property
    def failed(self):
        return any(check.status == "FAIL" for check in self.checks)

    def to_dict(self):
        return {"mode": self.mode, "infrastructure_modified": False,
                "deployment_ready": False, "failed": self.failed,
                "checks": [asdict(check) for check in self.checks]}


def validate_inventory(data):
    fields(data, ("api_type", "version", "connection_state", "maintenance_mode",
                  "cpu_threads", "cpu_mhz", "memory_bytes", "memory_used_mb",
                  "datastores", "networks", "vm_names"))
    for key in ("api_type", "version", "connection_state"):
        text_value(data[key])
    if type(data["maintenance_mode"]) is not bool:
        raise ConfigError("Inventory maintenance_mode must be boolean.")
    for key in ("cpu_threads", "cpu_mhz", "memory_bytes"):
        integer(data[key], 1, 2 ** 60)
    if data["memory_used_mb"] is not None:
        integer(data["memory_used_mb"], 0, 2 ** 60)
    for key in ("datastores", "networks", "vm_names"):
        if not isinstance(data[key], list):
            raise ConfigError("Inventory collections must be lists.")
    for ds in data["datastores"]:
        fields(ds, ("name", "accessible", "free_bytes", "maintenance_mode"))
        text_value(ds["name"])
        text_value(ds["maintenance_mode"])
        if type(ds["accessible"]) is not bool:
            raise ConfigError("Datastore accessible must be boolean.")
        if ds["free_bytes"] is not None:
            integer(ds["free_bytes"], 0, 2 ** 60)
    for net in data["networks"]:
        fields(net, ("name", "accessible", "standard"))
        text_value(net["name"])
        if any(type(net[k]) is not bool for k in ("accessible", "standard")):
            raise ConfigError("Network flags must be boolean.")
    for name in data["vm_names"]:
        text_value(name)


def run_preflight(config: Config, inventory=None, mode="offline") -> Report:
    checks = [Check("config", "PASS", "Local project settings passed schema checks; sizing is not certified.")]
    if inventory is None:
        checks.append(Check("esxi_inventory", "SKIP", "No connection attempted; host checks require explicit live mode or a fixture."))
    else:
        validate_inventory(inventory)
        def check(key, condition, message):
            checks.append(Check(key, "PASS" if condition else "FAIL", message))
        check("endpoint", inventory["api_type"] == "HostAgent", "Endpoint must be a direct ESXi HostAgent.")
        version = re.fullmatch(r"(\d+\.\d+)(?:\.\d+)*", inventory["version"])
        check("version", bool(version and version[1] in config.policy["allowed_esxi_versions"]), "Host version family must match the locally reviewed allowlist.")
        check("host_state", inventory["connection_state"] == "connected" and not inventory["maintenance_mode"], "Host must be connected and outside maintenance mode.")
        check("cpu_count", inventory["cpu_threads"] >= config.vm["vcpus"], "Host logical CPU count must accommodate the proposed vCPU count; this is not admission control.")
        check("cpu_frequency", inventory["cpu_mhz"] >= 2000, "Host CPU frequency must meet the documented 2 GHz baseline.")
        check("memory_total", inventory["memory_bytes"] >= config.vm["memory_gib"] * GIB, "Physical memory must cover proposed VM memory.")
        used = inventory["memory_used_mb"]
        if used is None:
            checks.append(Check("memory_available", "WARN", "Host memory usage unavailable; capacity remains unverified."))
        else:
            available = inventory["memory_bytes"] - used * 1024 ** 2
            check("memory_available", available >= config.vm["memory_gib"] * GIB, "Observed unused memory must cover the proposed VM; reservations and overhead still require review.")
        stores = [ds for ds in inventory["datastores"] if ds["name"] == config.vm["datastore"]]
        check("datastore", len(stores) == 1 and stores[0]["accessible"] and stores[0]["maintenance_mode"] == "normal", "Exactly one matching accessible datastore outside maintenance is required.")
        if len(stores) == 1 and stores[0]["accessible"] and stores[0]["free_bytes"] is not None:
            needed = (config.vm["disk_gib"] + config.policy["datastore_headroom_gib"]) * GIB
            check("storage_capacity", stores[0]["free_bytes"] >= needed, "Datastore free capacity must cover the disk plus configured headroom.")
        elif len(stores) == 1 and stores[0]["accessible"]:
            checks.append(Check("storage_capacity", "FAIL", "Selected datastore free capacity is unavailable; capacity cannot be verified."))
        else:
            checks.append(Check("storage_capacity", "SKIP", "No unique accessible datastore; capacity figures cannot be trusted."))
        networks = [net for net in inventory["networks"] if net["name"] == config.vm["port_group"]]
        check("port_group", len(networks) == 1 and networks[0]["accessible"] and networks[0]["standard"], "Exactly one accessible standard port group is required by this standalone-host framework.")
        check("vm_name", config.vm["name"] not in inventory["vm_names"], "Proposed VM name must not already exist in visible inventory.")
    checks.extend([
        Check("sizing_and_reservations", "WARN", "Review persona sizing, CPU/memory reservations, storage performance, overhead, licensing, and complete inventory permissions manually."),
        Check("guest_network", "SKIP", "Guest VLAN, DNS, NTP, routing, IP conflicts, and firewall reachability are not tested."),
        Check("media_and_ztp", "SKIP", "Media integrity, VM hardware, Cisco ZTP syntax, and boot success are not tested."),
        Check("restore", "SKIP", "ISE 3.4 backup compatibility, encryption key, certificates, and restoration are not tested."),
    ])
    return Report(mode, checks)
