# Deployment workflow and preflight usage

## Current phase: offline only

Run the README commands against the supplied examples. The default preflight
mode is offline, identical to `--dry-run`. Option abbreviations are rejected;
only the full `--live` flag opts into remote access. `--inventory` evaluates local JSON
instead of contacting a host. These flags and `--live` are mutually exclusive.

Prepare private settings only when needed:

```sh
umask 077
mkdir -p local
cp examples/preflight.example.json local/preflight.json
```

Edit that private copy. Do not put usernames or passwords into it; use the named
environment variables later. `ca_file`, if present, is relative to this settings
file unless absolute. No `.env` file is automatically loaded.

## Later: explicitly authorized read-only access

The following is a future operator procedure, not part of repository setup.
Install the optional dependency into a virtual environment, obtain credentials
through an approved secret manager into `ESXI_USERNAME` / `ESXI_PASSWORD`, and
review the scope of the read-only account. Avoid plaintext shell assignments or
command-line password arguments. Then, only when live access is authorized:

```sh
.venv/bin/ise-ztp preflight --config local/preflight.json --live --format json
```

This uses the direct ESXi SOAP endpoint, not vCenter. The application does not
retry failed logins. Treat any FAIL as blocking. WARN and
SKIP require manual evidence. Even an all-PASS subset is not deployment approval.
Reports contain check messages, not inventory values. They go to stdout; event
logs go to stderr. Redirect only into private ignored storage if retention is
needed. Exit codes: 0 = no evaluated failures, 1 = failed checks, 2 = input or
operational error, 130 = interruption.

The configured timeout covers SOAP requests, but pyVmomi's initial API-version
discovery uses its own default socket behavior. DNS and the entire inventory run
also have no application-enforced deadline. Keep a future live run supervised
and interrupt a stalled discovery. Do not treat this scaffold as an unattended
bounded-duration job; an overall deadline is a future runner requirement.

## Future deployment implementation

1. Verify preflight and manual prerequisites against the precise media/build.
2. Review a direct-host create/import mechanism and host license/API support.
   Create a **new, powered-off** VM with the reviewed sizing and guest network.
3. Review the private `ise-ztp.conf` against Cisco's on-premises syntax. The example
   is not an input to the project CLI and no renderer/validator is implemented.
4. Encode the file locally as one Base64 value and set `guestinfo.ise.ztp` through
   the VM's advanced configuration. Do not use an online encoder for secrets.
5. Start the installation with the reviewed console/boot configuration, then
   validate guest service health. Cisco directs ZTP monitoring to the serial
   console. Follow its first-login password-change flow.

The transport and bootstrap behavior in steps 3–5 follow
[Cisco's ISE 3.5 ZTP chapter](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html).
Do not confuse project JSON with the guest's key/value file or add generic
`guestinfo.userdata` settings. Do not invent keys for backup restoration.

After acceptance, plan explicit removal of the guestinfo secret and any private
plaintext/encoded temporary files, plus rotation of bootstrap credentials.
Removal is project security policy, not an automated feature or a claim that
Cisco removes the value itself. Preserve only approved, sanitized evidence.

The `deploy --dry-run` command prints this future sequence without reading media,
ZTP, backup files, or credentials. It never calls a writer. There is no `--apply`
option. Restore and cutover follow their own reviewed runbook.
