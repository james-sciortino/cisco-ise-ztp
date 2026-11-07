# Cisco ISE 3.5 ZTP through a restricted MCP interface

Python automation foundation for Cisco ISE 3.5 on standalone ESXi, with a
separate future restore of an ISE 3.4 configuration backup. **Implemented:
read-only MCP preflight and offline planning. Deployment and restore are not implemented.**

The supported installation contract is Cisco native ZTP using
`guestinfo.ise.ztp`, described in the
[Cisco ISE 3.5 installation guide](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html).
MCP is the controlled operations interface; it does not replace Cisco's procedure.

## Local use

Use Python 3.11+. Offline commands and tests use only the standard library:

```sh
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --dry-run
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --inventory examples/inventory.example.json --format json
PYTHONPATH=src python3 -m ise_ztp deploy --config examples/preflight.example.json --dry-run
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

These commands do not connect or read keys. A zero exit status means no evaluated
check failed; it is not deployment approval. Every report sets
`deployment_ready: false`. Synthetic fixture timestamps are not live evidence.

For installation, create a private virtual environment and install `-e .`.
Only explicitly authorized live operations require the reviewed optional
`-e '.[mcp]'` extra. Package installation may contact a package registry.
See [deployment and live usage](docs/deployment.md).

## Current boundary

```text
Workstation CLI → pinned SSH / fixed MCP command → read-only ESXi identity → standalone ESXi
```

ESXi credentials and TLS trust stay on the MCP server. The workstation uses a
new dedicated SSH key and a separately verified host pin. There is no direct
ESXi adapter, general remote shell, configurable MCP command, or write tool.
Schema version 2 deliberately rejects the old direct-host credential settings.

| Capability | State |
| --- | --- |
| Strict settings, offline fixtures, dry-run outline | Implemented |
| Exact four-tool discovery and parameterless read calls | Implemented; live transport validated |
| Host identity/version/state, memory estimate, visible VM-name collision, datastore free space, snapshot summary | Implemented with explicit limitations |
| CPU topology, reservations, network inventory, datastore maintenance, media and license facts | Unavailable from current tools; reported as unresolved |
| Private per-run audit, error suppression, client deadlines | Implemented |
| VM creation/import, ZTP rendering/injection, power operations, restore | Not implemented |

Live evidence, inventories, keys, certificates and media stay outside Git.
Tracked examples use fictional values. Keep real settings in ignored `local/`;
never edit examples to contain site details. The new MCP client was exercised
through the existing server without installing changes there. Native Codex tool
loading is a separate client check from this CLI's verified protocol transport.

## Documentation

- [Architecture](docs/architecture.md) and [MCP tool boundaries](docs/mcp-boundaries.md)
- [Prerequisites](docs/prerequisites.md) and [readiness gates](docs/readiness.md)
- [Deployment](docs/deployment.md) and [backup restoration](docs/backup-restoration.md)
- [Validation](docs/validation.md), [troubleshooting](docs/troubleshooting.md), [security](docs/security.md)
- [Technical blog](docs/technical-blog.md) and [authoritative references](docs/references.md)

Develop on `codex/` branches. Review and obtain approval for each commit and push.
Publication and server deployment are separate decisions; neither authorizes an
infrastructure change.
