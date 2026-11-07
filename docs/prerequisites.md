# Prerequisites

## Workstation and host access

Use Python 3.9+ (a maintained release for operations), a private working directory,
and an approved package source for the optional pyVmomi dependency. Offline mode
requires no third-party runtime packages. Live mode later requires network access
to the ESXi HTTPS port, trusted certificate chain, and a certificate matching the
configured hostname/IP. A private CA can be supplied with `esxi.ca_file`.

Use a dedicated ESXi account with read-only access propagated over the complete
host inventory. Hidden objects can make absence checks misleading. Review access
coverage manually; preflight does not establish that credentials see everything.
Lockdown, licensing, or access policy may prevent direct-host access. Resolve
these through the host owner; do not weaken host security to make the tool pass.

## ISE media and resources

Obtain entitled ISE 3.5 ISO or OVA media from Cisco, record its exact build and
vendor checksum privately, and select a sizing profile for the planned personas,
endpoint load, and retention. The example is a small SNS 3615-style profile:
16 vCPUs, 32 GiB memory, 16,000 MHz CPU reservation, and a 600 GiB disk.
Review actual requirements rather than treating example values as universal.
Extra Small is PSN-only, unsuitable for the administration-node restore target.
Reserve memory and CPU per the selected profile. Use a single adequately sized
disk; Cisco does not support VM snapshots for ISE backup.
[Cisco hardware and virtual appliance requirements](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_systemrequirements/r_hardwareandvirtualappliancerequirements.html).

The same current HTML requirements list ESXi 7.0, 8.0, and 9.0. The project defaults
to a narrower 7.0/8.0 allowlist. Match the exact media, host build, virtual hardware,
and current Cisco compatibility guidance before extending it; see
[reference discrepancies](references.md). API accessibility alone is not product
support or a supported lifecycle determination.

For a future ISO-built VM, review guest OS type, firmware, disk provisioning,
controller, NIC, reservations, and serial-console setup in
[Cisco's VMware instructions](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/c_vmware_virtual_machine-1.html).
These hardware choices are not checked or applied by this scaffold.

## Network and recovery planning

Have the network owner reserve a unique address and hostname and review forward
and reverse DNS, gateway, VLAN/port group, DNS reachability, NTP synchronization,
administration access, and required service ports from the **guest network**.
A host management connection cannot establish any of those guest properties.

Plan identity reuse and isolation before restoring the existing 3.4 backup.
Record the source version/patch, personas, hostname/FQDN, timezone, certificates,
backup encryption-key reference, and intended target identities privately.
Arrange capacity for an isolated rehearsal and a rollback/cutover decision with
the service owner. Preserve the functioning source environment.
