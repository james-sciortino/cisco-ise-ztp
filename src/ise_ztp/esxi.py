"""Direct-host SOAP inventory only. No infrastructure mutation methods."""

import logging
import os
import ssl

from .errors import PreflightError

LOG = logging.getLogger("ise_ztp")


def collect_inventory(config):
    # Imports and credential access occur only inside explicitly selected live mode.
    try:
        from pyVim.connect import Disconnect, SmartConnect
        from pyVmomi import vim
    except ImportError:
        raise PreflightError("Live preflight requires the optional esxi dependency.") from None
    settings = config.esxi
    username = os.environ.get(settings["username_env"])
    password = os.environ.get(settings["password_env"])
    if not username or not password:
        raise PreflightError("Set the configured credential environment variables before live preflight.")
    try:
        context = ssl.create_default_context(cafile=settings.get("ca_file"))
    except (OSError, ssl.SSLError):
        raise PreflightError("Cannot load TLS trust; verify the configured CA file.") from None
    service = None
    try:
        service = SmartConnect(host=settings["host"], port=settings["port"],
                               user=username, pwd=password, sslContext=context,
                               httpConnectionTimeout=settings["timeout_seconds"])
        content = service.RetrieveContent()
        if content.about.apiType != "HostAgent":
            raise PreflightError("A direct ESXi HostAgent endpoint is required; vCenter is not supported.")
        # Traverse existing inventory. Do not create even a temporary ContainerView.
        def hosts(entity):
            if isinstance(entity, vim.HostSystem):
                return [entity]
            if isinstance(entity, vim.Folder):
                return [h for child in entity.childEntity for h in hosts(child)]
            if isinstance(entity, vim.Datacenter):
                return hosts(entity.hostFolder)
            if isinstance(entity, vim.ComputeResource):
                return list(entity.host)
            return []
        found = hosts(content.rootFolder)
        if len(found) != 1:
            raise PreflightError("Expected exactly one visible ESXi host; verify endpoint and read permissions.")
        host = found[0]
        summary = host.summary
        hardware, runtime = summary.hardware, summary.runtime
        networks = []
        for network in host.network:
            net_summary = network.summary
            networks.append({"name": network.name, "accessible": net_summary.accessible,
                             # OpaqueNetwork also extends Network. Only the exact
                             # base managed-object type represents our scope.
                             "standard": type(network) is vim.Network})
        datastores = []
        for datastore in host.datastore:
            ds = datastore.summary
            datastores.append({"name": ds.name, "accessible": ds.accessible,
                               # The SDK does not guarantee freeSpace when
                               # accessible is false; do not retain that value.
                               "free_bytes": ds.freeSpace if ds.accessible else None,
                               "maintenance_mode": ds.maintenanceMode or "unknown"})
        return {"api_type": content.about.apiType, "version": content.about.version,
                "connection_state": str(runtime.connectionState),
                "maintenance_mode": runtime.inMaintenanceMode,
                "cpu_threads": hardware.numCpuThreads, "cpu_mhz": hardware.cpuMhz,
                "memory_bytes": hardware.memorySize,
                "memory_used_mb": summary.quickStats.overallMemoryUsage,
                "datastores": datastores, "networks": networks,
                "vm_names": [vm.name for vm in host.vm]}
    except PreflightError:
        raise
    except ssl.SSLCertVerificationError:
        raise PreflightError("TLS verification failed; verify certificate trust and endpoint identity.") from None
    except Exception:
        # SDK fault strings may contain usernames, endpoints, or session material.
        raise PreflightError("ESXi inventory failed; check TLS, connectivity, timeout, credentials, and read permissions. Raw fault suppressed.") from None
    finally:
        if service is not None:
            try:
                Disconnect(service)
            except Exception:
                LOG.warning("Session cleanup failed; server-side session expiry may be required.")
