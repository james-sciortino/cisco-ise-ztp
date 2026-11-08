# Validation and backup restoration

These are checks to perform, not claims of completed testing.

## Initial installation

- [ ] Confirm the expected ISE version, hostname and IP address.
- [ ] Confirm ISE application services are running.
- [ ] Validate DNS resolution, time synchronization and network reachability.
- [ ] Complete the first GUI login and required bootstrap password change.
- [ ] Confirm VM sizing/reservations and applicable licensing.

## Restore an existing configuration

- [ ] Check Cisco's target-version backup/restore compatibility and patch guidance.
- [ ] Apply the reviewed ISE 3.5 patch and verify it completed before restoration.
- [ ] Confirm the backup is current, intact and available through a supported
      ISE repository. Retain its original filename and encryption key securely.
- [ ] Restore the native configuration backup using Cisco's documented procedure.
- [ ] Restore service certificates/private keys and internal CA material as needed.
- [ ] Review restored identity/network settings before reconnecting dependencies.

Patch numbers are release-specific; a 3.4 Patch 6 backup does not imply a need
for 3.5 Patch 6. Certificate/CA recovery must be planned separately. VM snapshots
are not substitutes for ISE native backups.

## Acceptance and recovery

- [ ] Verify administration access, certificates, trust chains and licensing.
- [ ] Test representative successful and denied authentications and integrations.
- [ ] Record actual results, versions and deviations privately, without secrets.
- [ ] Retain recovery materials until the replacement is accepted.

If the source VM has been deleted, recovery requires reinstalling its release
and patch and restoring its backup/certificates; do not assume instant rollback.

Only after successful deployment and validation should the blog be rewritten
as an account of a completed installation. See [Cisco references](references.md).
