# Future restoration of an ISE 3.4 configuration backup

This is a preparation and execution runbook for a later authorized change.
The project does not read, decrypt, upload, or restore backups. Copy
`examples/restore-plan.example.json` to private storage as a human worksheet.
Its fields are project metadata, not ISE API or ZTP parameters.

## Compatibility decision

Cisco's [ISE 3.5 upgrade process](https://www.cisco.com/c/en/us/td/docs/security/ise/articles/cisco-ise-upgrade-methods-35.html)
allows direct upgrades from 3.2 and later and states that backup/restore remains
supported, while recommending GUI upgrade for releases later than 3.2 patch 2.
This supports planning a 3.4-to-3.5 restore; it does **not** validate an unknown
backup. Record the exact source/target patches, backup type, integrity, applicable
release caveats, and a successful isolated rehearsal before production use.

## Prepare recovery inputs

- Preserve the original encrypted configuration backup and filename in secure
  external storage; verify its recorded digest. A checksum detects change, not
  decryptability or schema compatibility. Do not unpack the backup here.
- Confirm access to the original encryption key through a secret manager. Keep
  the key out of settings, command history, reports, and chat.
- Inventory system certificates, associated private keys, trust chains, and
  internal CA recovery material separately. Configuration backup alone is not a
  complete certificate recovery plan. Cisco documents the separate CA material in
  its [3.5 Basic Setup guide](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/admin_guide/b_ise_admin_3_5/b_ISE_admin_basic_setup.html).
- Document hostname/FQDN, IP, DNS, timezone, persona, node membership, identity
  sources, and integration dependencies privately. Plan how to prevent duplicate
  identities and authentication traffic reaching an unvalidated replacement.
- Choose an appropriately sized administration target and a tested rollback
  path. Avoid making the source environment dependent on the replacement early.

## Later execution gates

First complete fresh-install validation of the 3.5 target and the approved patch
baseline. Isolate the rehearsal network while providing needed infrastructure
services. Establish and test the target's backup repository separately from ZTP.
Use a supported restore repository (for example, an approved SFTP repository).
ZTP patch repositories and backup repositories are different workflows.

Use Cisco's [3.5 restoration procedure](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/admin_guide/b_ise_admin_3_5/b_ISE_admin_maintain_monitor.html)
on a suitable standalone administration node or primary PAN. Restoration can
restart services. The optional CLI `include-adeos` restores ADE-OS configuration;
omitting it restores application configuration only. Keep the worksheet default
false until the identity/network implications are reviewed. Do not blindly
overwrite a newly staged target's operating-system settings.

Apply the documented identity-specific certificate/CA recovery procedure. The
guide discusses automatic CA regeneration as well as recovery steps; select the
branch matching your deployment instead of assuming the original CA survives.
Review repository credentials after a restore to another node and reconcile node
registration/synchronization before resuming service.

Operational/MnT history is a separate backup and restore decision; this project
targets configuration recovery only. Do not silently substitute an operational
backup. Do not use a VMware snapshot as the recovery mechanism.

## Acceptance and rollback

Collect private evidence for successful restore status, expected policy sets,
network-device objects, identity sources, certificate bindings, required personas,
replication, and representative authentications. Test an expected denial as well
as an allowed authentication. Confirm the target is not simply authenticating
through a still-active old node.

Authorize cutover only after these checks. Keep source backup and original
service path intact until acceptance. On failure, stop the migration, isolate the
replacement, and return traffic to the documented source path; do not attempt an
unreviewed downgrade or destructive retry. Resolve incompatible patches or
backup recovery failures with the Cisco guidance/TAC appropriate to the case.
