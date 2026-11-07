# MCP boundaries and proposed extensions

## Existing, validated surface

The existing Home AI service has four parameterless read-only tools. The ISE
client verifies that exact contract and sends no arbitrary command, Python,
ESXi method, URL, path or property selector. ESXi credentials stay on the server.
The existing server and Home AI consumers were not changed for this project.

Maintain the current dedicated ESXi read identity and reviewed read-only role,
with propagated visibility only over the approved standalone host inventory.
The administrator must verify the effective assignment, denied writes, TLS trust
and file ownership. Tool success does not prove least privilege or complete visibility.
No privilege expansion is proposed for the current four tools.

## Proposed next read-only surface — not implemented or installed

| Proposed bounded tool | Output and constraints | Evidence it would add |
| --- | --- | --- |
| `ise_esxi_preflight_facts()` | Fixed approved host; HostAgent API identity, CPU sockets/cores/threads/frequency, supported hardware facts, resource reservation summary | CPU and reservation feasibility without assuming a vCenter API |
| `ise_esxi_placement_catalog()` | Only server-enrolled datastores and standard port groups; stable IDs, capacity, maintenance, VLAN/accessibility | Placement and network inventory; not guest reachability |
| `ise_media_catalog()` | Only administrator-enrolled media IDs, size and previously verified vendor digest; fixed approved locations | Media selection; no arbitrary file browse/read/upload |
| `ise_enrolled_vm_facts()` | Only project-enrolled VM identities; selected hardware and resource fields | Verify future project VMs without exposing unrelated VM data |

Exclude arbitrary extraConfig, especially `guestinfo.ise.ztp`, credentials, guest
files, console content, bulk datastore listings and arbitrary managed-object IDs.
Null/unsupported properties must remain explicit. Reads that need extra privileges
must first be justified individually against the ESXi API; do not grant broad roles
because a tool returns an error. Media checksum computation is a separate bounded
administrator operation if catalog metadata is insufficient.

The original endpoint's four-tool contract must remain stable. Prefer a separately
versioned ISE endpoint after reviewing its runtime identity and transport; changing
the original tool list would deliberately fail this client's discovery check and
could disrupt existing consumers. No endpoint or account is created in this change.

## Development and deployment

Codex can develop and test source locally. No administrator key is supplied to a
model-facing tool. If installation needs automation, propose a separate deployment
identity restricted to installing a reviewed release in fixed directories and
performing specified service checks. Obtain approval for the actual permissions,
targets, artifact digest, validation and rollback before establishing that identity.
For now, the owner can install an approved release through their existing session.
Never restore revoked access or borrow another consumer's private key.

Before installation, test the old contract with its consumers, validate ownership
and credential isolation, stage the new endpoint, and record rollback to the
previous release. Keep publication, server deployment and ESXi changes separate.

## Future write boundary

No ESXi writer privileges are requested now. Before implementing writes, present
an exact privilege matrix verified for standalone ESXi and its license. Use a
separate ESXi identity. Limit tools to approved project VM identities, placement,
media and resource ceilings enforced on the server. Require an immutable,
human-approved plan, expiry, parameter binding, durable single-execution claim,
preflight, task tracking, audit, post-validation and recovery. Do not expose
arbitrary API invocation. Deletion, rebuilding and unrelated VM modifications
require separate authorization and must not be automatic failure recovery.
