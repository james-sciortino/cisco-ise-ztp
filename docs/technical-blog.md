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

## Read the host directly

A standalone host has a narrower operational context than a vCenter-managed
automation platform. The adapter connects directly with pyVmomi and checks the
endpoint type before traversing existing inventory. It never relies on Content
Library, a vCenter REST deployment endpoint, or cluster placement.

The useful first checks are deliberately modest: host version/state, basic
compute capacity, datastore availability/free space, a standard port group, and
VM-name collision. Their limitations matter. An existing port group cannot prove
that the guest can synchronize its clock. Physical memory cannot prove that a
resource reservation will be admitted. The report preserves those unknowns.

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
without creating a VM. The live adapter is mock-tested separately, including TLS
verification, endpoint rejection, exception privacy, and logout on failure.

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

## What this first phase demonstrates

The result is a small, runnable foundation with explicit boundaries. It provides
local feedback today and a constrained read-only adapter for an authorized host
test later. It does not claim a completed installation or restoration. The next
engineering milestone is a real-host validation of the adapter, followed by a
reviewed direct-host deployment implementation and an isolated restore rehearsal.
