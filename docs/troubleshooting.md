# Troubleshooting

| Symptom | Investigation / next step |
| --- | --- |
| Input error, exit 2 | Compare with example JSON; remove unknown fields, duplicate keys, inline credentials, and invalid types. Raw values are intentionally not echoed. |
| Offline result has SKIP checks | Expected. Use fixtures for local testing; request separate authorization before live access. |
| Missing optional dependency | Install the `esxi` extra in the selected virtual environment only when live testing is needed. |
| Missing credentials | Populate the configured environment variables securely; the tool does not load `.env` files. |
| TLS failure | Check CA trust, hostname/SAN match, certificate expiry, and CA file location. Do not disable verification. |
| Generic inventory error | Review host reachability, HTTPS port, timeout, credentials, lockout, read permissions, and SDK/host compatibility through approved diagnostics. Raw SDK faults are suppressed. |
| Wrong endpoint | Supply the host directly. A vCenter endpoint is deliberately rejected. |
| Insufficient capacity | Review sizing and competing workloads. No remediation is attempted. |
| Missing datastore/port group | Check exact private names, accessibility, account visibility, and standard-switch scope. Distributed port groups are outside this implementation. |
| Existing VM name | Choose a new deployment identity or separately review the existing VM. The scaffold never overwrites it. |
| Cleanup warning | Check host session expiry/session inventory through approved administration. Avoid repeated logins. |
| Discovery stalls despite timeout | The SDK does not apply the configured SOAP timeout to initial API-version discovery. Interrupt the supervised run; check DNS/connectivity through approved diagnostics. |
| `deploy` fails without dry-run | Expected. The writer has not been implemented. |

For future ZTP failures, compare the exact guestinfo key and the locally decoded
payload privately; check media/boot flow and serial console output against the
[Cisco ZTP troubleshooting procedure](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html).
Investigate DNS, NTP, and routing from the guest network. Do not solve failures by
inventing alternate keys or disabling installation checks by default.

If restoration later fails, preserve sanitized status/log evidence, verify
repository access, backup integrity, original key, and exact version/patch path.
Follow [backup restoration](backup-restoration.md) before retrying. Avoid placing
payloads, private console captures, backups, or full running configuration into
Git issues. Internal failure details should be inspected only through an approved
private troubleshooting channel.
