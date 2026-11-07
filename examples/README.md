# Example files

All addresses and inventory names are synthetic. Copy to ignored `local/` before
editing. Project JSON fields are not passed to Cisco and are not ZTP parameters.

| File | Consumer / meaning |
| --- | --- |
| `preflight.example.json` | CLI settings; illustrative small SNS 3615-style resources, not a sizing recommendation |
| `inventory.example.json` | Local test fixture; never evidence of an actual host |
| `ise-ztp.conf.example` | Minimal on-premises bootstrap illustration; never consumed by this CLI |
| `restore-plan.example.json` | Human worksheet only; never consumed by this CLI or ISE |

`esxi.username_env` and `password_env` name environment variables; they contain
no credential values. Optional `esxi.ca_file` identifies a private CA bundle,
resolved relative to the settings file (or an absolute path). TLS verification
cannot be disabled. `timeout_seconds` bounds SOAP requests after API negotiation;
pyVmomi's initial version discovery does not use this setting. It is not a total
run deadline (including DNS). `vm` names select the intended host objects and new VM name.
Numeric resource fields describe intent. `cpu_reservation_mhz` is recorded for
future planning; preflight does not validate resource-pool admission or apply it.

Sizes are GiB in this project's JSON. Headroom is an operator-selected allowance
for VM overhead and other storage use; 80 GiB is an example, not a Cisco rule.
`allowed_esxi_versions` is a local approval list, initially 7.0/8.0. Adding 9.0
requires a media/build compatibility review. No other schema fields are accepted.

Input must be a regular UTF-8 JSON file of at most 1 MiB. Duplicate keys and
non-JSON numeric constants (`NaN`/`Infinity`) are rejected. Inventory fixtures may
use `null` for unavailable datastore `free_bytes`; a selected accessible datastore
with unknown capacity fails its capacity check. An inaccessible datastore's
capacity is never used, even if the fixture contains a number.

The ZTP example uses the on-premises spellings corroborated in Cisco's authored
[ZTP article, “ISE 3.2 and newer”](https://community.cisco.com/t5/security-knowledge-base/ise-zero-touch-provisioning-ztp/ta-p/4541606).
The authoritative 3.5 installation guide names required settings but its current
HTML does not present the full key/value template. Confirm the example against
your exact 3.5 media before using it; this scaffold does not claim syntax validation.
Optional services, patch options, management-interface values, and restore keys
are deliberately absent. See [reference decisions](../docs/references.md).
