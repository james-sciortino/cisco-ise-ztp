CISCO ISE 3.5 ZTP ON STANDALONE ESXi
===================================
Status: guide prepared; end-to-end deployment not yet validated.

This repository contains a manual native-ZTP workflow, not an automation tool.

1. Copy examples/ise-ztp.conf.example to local/ise-ztp.conf.
2. Open the copy as plain text in TextEdit. Enter your real settings and replace
   the password placeholder. Do not add .txt to the configuration filename.
   For a replacement, match the backup hostname/domain capitalization exactly.
   Do not automatically convert an existing hostname to lowercase.
3. In Terminal, replace the path below and run this as one line:

base64 -i "/absolute/path/to/ise-ztp.conf" | tr -d '\r\n' | pbcopy

4. Import the ISE OVA in the ESXi Host Client. Disable automatic power-on.
   Verify supported sizing, reservations, storage and each NIC's mapping.
5. While powered off, open Edit settings > VM Options > Advanced >
   Edit Configuration. Add:

   Name:  guestinfo.ise.ztp
   Value: paste the encoded contents from your clipboard

6. Configure serial-console monitoring. Confirm working guest-network DNS/NTP.
   If reusing the source IP/hostname, ensure the old VM is off before booting
   the new one. This guide does not instruct you to delete the source VM.
7. Power on, monitor ZTP and verify ISE services. Verify hostname capitalization
   in both the CLI and Deployment page before patching/restoring. Complete the first-login
   password change. For migration, patch the target release before restoring
   the native backup and applicable certificate/CA material.
8. Validate authentication, integrations, certificates and licensing.

Repeat the encoding command after every configuration edit.
Base64 is NOT encryption. Keep the configuration and encoded value private.
Do not use an online encoder. Actual settings, backups and media stay out of Git.
Retain off-host backup/key/certificate exports and source recovery media.
Keep patch archives in their original downloaded format and verify checksums.

Detailed steps: docs/deployment.md
Validation/restoration checklist: docs/validation.md
Cisco references: docs/references.md
Blog outline (deferred until validation): docs/technical-blog.md

The previous MCP development has been preserved privately for a future ESXi
automation project. No MCP installation is needed for this procedure.

TROUBLESHOOTING NOTES
---------------------
NTP: Bootstrap stopped at synchronization while configured for pool.ntp.org.
The next retry choice was the setup prompt's default, time.nist.gov:
primary_ntpserver=time.nist.gov
This does not establish the root cause or prove a server change fixes it.
Verify DNS and UDP 123/return traffic from the ISE network. Do not skip NTP checks.
After editing, regenerate Base64 and replace guestinfo.ise.ztp while powered off.

Hostname: Restore rejected a capitalization difference. A case-only CLI rename
changed the running configuration but left the GUI lowercase; restore still
failed. Verify both identities before retrying. A rebuild with matching case
has been proposed but is not validated. Do not modify the backup to bypass the
check, and do not delete/rebuild without a separate recovery decision.
