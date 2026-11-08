# Draft outline: Cisco ISE 3.5 ZTP on standalone ESXi

**On hold until the installation and restoration have been validated.**
This is an outline, not a report of a successful deployment or a publication-ready
article. The subject is manual native ISE ZTP, not MCP or ESXi automation.

Planned article:

1. The objective: bootstrap an ISE VM with Cisco's native VM-user-data method.
2. Prerequisites: supported sizing, networking, DNS/NTP and recovery materials.
3. A sanitized `ise-ztp.conf`, including optional secondary/tertiary DNS.
4. Local Base64 encoding and the distinction between encoding and encryption.
5. Importing the OVA, setting `guestinfo.ise.ztp` before boot, and monitoring ZTP.
6. Verifying the downloaded archive without browser decompression changing it.
7. Patching, configuration restoration, certificate recovery and validation.
8. Observed results and lessons, added only after the actual work succeeds.

Use fictional addresses and placeholders. Never publish the real configuration,
Base64 payload, secrets, certificates, inventories or internal infrastructure
names. Separate documented Cisco requirements from any lab sizing exceptions.
Link to the [official references](references.md) and state what was actually tested.
