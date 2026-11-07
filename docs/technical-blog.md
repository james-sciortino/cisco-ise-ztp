# Building a Cisco ISE ZTP project around evidence and safe defaults

Automating an ISE installation starts before a VM is powered on. The first useful
deliverable is a way to establish what the host can offer and what remains
unknown. This repository takes that approach for ISE 3.5 on standalone ESXi,
while keeping an eventual ISE 3.4 configuration restoration in view.

## Establish the bootstrap contract

The implementation targets Cisco's native `guestinfo.ise.ztp` path, described in
the [ISE 3.5 installation guide](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html).
That contract defines the future integration boundary. It does not make a Python
configuration file an ISE payload, and it does not make every familiar cloud
bootstrap option valid on premises.

The project therefore uses separate files for automation intent, a synthetic host
inventory, an illustrative guest bootstrap file, and a restoration worksheet.
Only the first two are read by the CLI. This separation makes review easier:
changes to a datastore threshold cannot silently change a guest administrator
password, and a restore key cannot become an unrecognized installer option.

The exact example syntax has its provenance documented. Optional settings stay
out until their meaning and applicability are established. A plausible-looking
configuration is not enough evidence to ship a renderer.

## Put the credential boundary on MCP

A standalone host does not supply vCenter-only deployment services. The controlled
path is a fixed MCP runtime that holds the ESXi read credential and verifies TLS.
The workstation authenticates with its own source-restricted SSH key and verified
host pin. It receives a small read-only tool surface instead of a general shell.

Before querying inventory, the client checks the exact tool list, annotations and
empty input schemas. It identifies the expected host, then reads VM names,
datastore usage and snapshot status. Unavailable CPU topology, network and
reservation facts remain unresolved. A successful request is useful evidence,
but it is not proof that an ISE installation fits or that every object is visible.

Troubleshooting must preserve that distinction. An SSH connection may work while
the MCP-to-ESXi HTTPS path is blocked. A firewall object can retain an old address
even when its label looks right. Read-only inspection of actual object values and
ordered rules can isolate that mismatch; the owner applies a separately reviewed
change. Runtime addresses and inventory belong in private evidence, not this article.

## Make offline behavior the normal path

A new contributor can execute the full check engine against a synthetic fixture
without credentials. Omitting flags never initiates a host connection. `--live`
is explicit and cannot be combined with `--dry-run` or fixture input.

```sh
PYTHONPATH=src python3 -m ise_ztp preflight \
  --config examples/preflight.example.json \
  --inventory examples/inventory.example.json
```

This makes error paths reproducible: remove the port group, reduce free storage,
or add the intended VM name to the fixture. Tests can verify those decisions
without creating a VM. The live adapter is mock-tested separately, including host-pin
verification, unexpected-tool rejection, stale observations and exception privacy.

Dry-run deployment currently returns an outline. It cannot create an object or
be switched into an undocumented apply mode. That limitation is visible in both
the output and the code. A future writer needs its own review and live validation.

## Keep restoration a separate operation

The goal of installing the new guest is to reach a healthy, known baseline.
Restoration then introduces an existing policy database, identities, and trust
relationships. Combining these stages would make failures harder to diagnose
and increase the risk of bringing an unvalidated replacement onto the network.

Cisco's [3.5 upgrade guidance](https://www.cisco.com/c/en/us/td/docs/security/ise/articles/cisco-ise-upgrade-methods-35.html)
supports planning the backup/restore migration. The repository translates that
into preparation gates: identify the backup and patches, retain its key securely,
plan certificate recovery, rehearse in isolation, and validate representative
authentication behavior before cutover. None of those gates is satisfied by a
successful ESXi login.

## What this phase demonstrates

The project now uses the existing four-tool interface and retains timestamped
private evidence. A report can show that reads work while leaving deployment
blocked by capacity or missing facts. That is a useful outcome: it prevents a
working transport from being mistaken for a supported installation plan.

The next extension should expose only the missing approved facts. Preserve Home
AI consumers, review any new server endpoint and identity, and keep deployment
approval separate from source publication. A future writer requires its own ESXi
identity, immutable approved parameters, duplicate-execution protection, task
tracking, post-validation and recovery. Backup restoration remains a later,
independently validated operation.
