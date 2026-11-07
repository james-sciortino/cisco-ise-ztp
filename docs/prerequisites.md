# Prerequisites

## Workstation and host access

Use Python 3.11+ and the reviewed optional MCP SDK for live reads. The workstation
needs only a dedicated restricted SSH key and verified host pin for the MCP server.
Keep the ESXi read credential and CA trust on that server. Use schema 2 settings;
there is no direct workstation-to-ESXi adapter or credential-loading fallback.

Verify the fixed command, root-controlled server files, source-restricted key,
disabled forwarding/TTY, and effective ESXi read-only role through the approved
administrator. Check inventory visibility: a successful read does not prove that
all objects are visible. Record the transport approval and private evidence outside Git.

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

## Readiness decisions

Use the [readiness checklist](readiness.md) for exact media/build, licensing,
certificate, guest-network and backup decisions. CPU and memory reservations must
be checked against Cisco's [VM size recommendations](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_2/r_vmware_appliance_size_recommendations.html).
The current MCP tools cannot make that admission decision. No final profile is
selected by this repository.
