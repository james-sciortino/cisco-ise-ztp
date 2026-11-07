# Cisco ISE 3.5 ZTP on standalone VMware ESXi

Python automation foundation for a new Cisco ISE 3.5 VM, with a separate future
restore of an existing ISE 3.4 configuration backup. **Current implementation:
read-only preflight and offline planning. Deployment and restore are not implemented.**

The bootstrap contract is Cisco native ZTP: the contents of `ise-ztp.conf`,
Base64-encoded, in the VM advanced parameter `guestinfo.ise.ztp`.
[Cisco ISE 3.5 ZTP documentation](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html)
is authoritative. This project does not substitute cloud-init, VMware guest
customization, or a vCenter deployment service.

## Start locally, with no infrastructure access

Python 3.9+ is supported; use a maintained Python release for operational use.
The offline CLI and tests need only the standard library:

```sh
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --dry-run
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --inventory examples/inventory.example.json --format json
PYTHONPATH=src python3 -m ise_ztp deploy --config examples/preflight.example.json --dry-run
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

These commands neither connect to ESXi nor read credentials. Fixture results are
synthetic; a zero exit status is **not** approval to deploy. Every report explicitly
leaves deployment readiness uncertified. `deploy` without `--dry-run` fails closed.

For an installed CLI, optionally create a virtual environment and install locally:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/ise-ztp --help
```

Dependency installation may access a package registry. Only future live preflight
needs `pip install -e '.[esxi]'`; review [deployment](docs/deployment.md) first.

## What is implemented

| Capability | State |
| --- | --- |
| Strict project JSON validation; reject inline credentials/unknown fields | Implemented |
| Offline config checks and synthetic inventory checks | Implemented, locally tested |
| Direct ESXi SOAP inventory, TLS verification, session cleanup | Implemented, mock-tested; not host-tested |
| Host/version/state, CPU/memory, datastore, standard port group, VM-name checks | Implemented, preliminary checks only |
| Safe event logging, exit codes, non-executable deployment outline | Implemented |
| Media upload/import, VM creation, reservations, ZTP rendering/injection, boot | Future work |
| ISE configuration restore, certificate recovery, cutover | Future work |

## Repository layout

```text
src/ise_ztp/    CLI, settings, pure checks, direct-host adapter, planning
examples/       Synthetic settings, inventory, ZTP example, restore worksheet
tests/          Offline safety and behavior tests
docs/           Operational and architecture documentation
local/          Ignored private working files (create when needed)
```

Copy examples to `local/` before entering any real values. Never customize the
tracked examples in place. Store backups in an access-controlled external
repository and keep encryption keys in a secret manager. Base64 is not encryption.
See [security](docs/security.md) for Git hygiene and bootstrap-secret handling.

## Documentation

- [Architecture and extension boundaries](docs/architecture.md)
- [Prerequisites and sizing](docs/prerequisites.md)
- [Deployment and preflight usage](docs/deployment.md)
- [ISE 3.4 backup restoration](docs/backup-restoration.md)
- [Validation and acceptance criteria](docs/validation.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Security and Git hygiene](docs/security.md)
- [Technical blog: building the automation foundation](docs/technical-blog.md)
- [Sources, discrepancies, and verification gaps](docs/references.md)
