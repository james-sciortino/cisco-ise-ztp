# Deployment workflow and preflight usage

## Offline work

Preflight defaults to offline behavior. `--dry-run`, `--inventory` and `--live`
are mutually exclusive, and abbreviated flags cannot enable access.

```sh
umask 077
mkdir -p local
cp examples/preflight.example.json local/preflight.json
```

Schema 2 uses MCP hostname/SSH port, the `svc-mcp` runtime user, absolute paths to
a dedicated key and pinned known-host file, the separately verified Ed25519
fingerprint, and a timeout. The ESXi section contains only the expected inventory
hostname. There are no ESXi usernames, passwords, CA files or environment-variable
credential references on the workstation. Do not reuse another consumer's key.

## Authorized read-only preflight

Install the reviewed `mcp` extra into the project's virtual environment. Set up
the restricted server-side public-key entry through the approved administrator
procedure; no installation or remote administration is performed by this CLI.
Both local SSH files must be owned regular files, mode 600. The audit parent must
already exist, have mode 700, and be outside Git. Example on macOS/Linux:

```sh
umask 077
mkdir -p "$HOME/.local/state/ise-ztp"
.venv/bin/ise-ztp preflight --config local/preflight.json \
  --live --audit-dir "$HOME/.local/state/ise-ztp" --format json
```

The output report is scrubbed of inventory identifiers. The log gives the private
run directory containing `events.jsonl`, `inventory.json` and `report.json`.
Treat these files as private operational evidence. They are not approval records
or immutable server audit logs. Missing evidence or failed checks block readiness.

Exit codes: 0 = no evaluated failures (readiness can still be incomplete),
1 = one or more failed predicates, 2 = configuration/operational failure,
130 = interruption. Client deadlines and remote cleanup limits are described in
[architecture](architecture.md). For errors, use approved administrator diagnostics;
no shell escape or insecure TLS/SSH option is provided.

## Future deployment

1. Resolve [readiness gates](readiness.md), including exact media/build and placement.
2. Review bounded MCP write tools and a separate ESXi writer identity. Obtain approval
   for its exact permissions and any server deployment identity before establishing access.
3. Create an immutable approved plan containing enrolled VM identity, approved datastore,
   standard network, media checksum, resource limits, expiry and operation sequence.
4. At execution, verify the plan and fresh capacity; claim it once, track ESXi task IDs,
   audit each transition, and refuse changes to unrelated VMs.
5. Follow Cisco's new-VM installation procedure. Set a locally encoded, private
   `ise-ztp.conf` in `guestinfo.ise.ztp` only on that approved VM, then validate boot,
   required services and first-login credential rotation.

[Cisco's ZTP chapter](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html)
governs bootstrap behavior. No renderer or writer is implemented. The dry-run
outline is not an immutable executable plan and cannot authorize infrastructure work.

After acceptance, separately approve removal of bootstrap secrets and private
artifacts. On failure, stop and preserve task/audit evidence; do not automatically
delete or rebuild anything. Restore/cutover follow [their own runbook](backup-restoration.md).
