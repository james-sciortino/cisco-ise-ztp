# Validation

## Local verification

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --dry-run
PYTHONPATH=src python3 -m ise_ztp preflight --config examples/preflight.example.json --inventory examples/inventory.example.json --format json
PYTHONPATH=src python3 -m ise_ztp deploy --config examples/preflight.example.json --dry-run
```

Tests use synthetic fixtures, fake MCP sessions and temporary files; they never
contact a host. Coverage includes offline defaults, explicit mode selection,
blocked deployment, host mismatch, unexpected tools/parameters, stale responses,
count/completeness inconsistencies, SSH restrictions and pins, private audit
placement, unknown capabilities, capacity failures and scrubbed errors.

An authorized live run verifies exact discovery and calls the four current tools
once each. Preserve timestamps and results privately. Successful reads validate
that transport and the current responses, not ESXi RBAC, runtime code provenance,
complete inventory coverage or ISE installation. Native client tool loading is
separate from the CLI protocol test. Do not run live tests in ordinary CI.

## Interpretation of reports

| Status | Meaning |
| --- | --- |
| PASS | One limited predicate was satisfied by the supplied data |
| FAIL | A prerequisite predicate failed; stop |
| WARN | Manual evidence remains necessary |
| SKIP | Not evaluated in this mode or not implemented |

The memory check is an instantaneous estimate, not a reservation guarantee. CPU
count is not available CPU capacity. Datastore capacity does not measure IOPS,
latency, provisioning suitability, or storage health. Port-group existence does
not validate VLAN, uplinks, DNS/NTP, or guest reachability. VM-name absence is only
meaningful if read permissions cover all inventory. A fresh check is needed
before future writes; inventory is not reserved by preflight.

## Later deployment acceptance

Have an operator verify media integrity, guest hardware, reservations, disk and
NIC mapping, serial console, network/time services, and completed installation.
Check `show version` and `show application status ise` as described in
[Cisco installation verification](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_installciscoise.html).
Evaluate required processes for the intended personas; optional services need
not all be running. Confirm HTTPS administration, password rotation, correct
identity/address/time, and expected alarms/licensing state.

Record installation and restoration acceptance separately. Use the
[restore runbook](backup-restoration.md) for policy, certificate, identity-source,
and authentication checks. Host preflight cannot certify either guest outcome.
