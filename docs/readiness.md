# ISE 3.5 readiness gates

Reviewed against Cisco's current installation documentation on 2026-11-07.
This is a versioned checklist, not a live inventory. Runtime evidence is stored
privately outside Git. No exact media build, patch, digest, persona mix or backup
patch is selected by the examples.

| Gate | Current implementation / evidence needed |
| --- | --- |
| Supported deployment method | Cisco native `guestinfo.ise.ztp`; exact ISO/OVA filename, build, patch, entitled download and publisher checksum still required |
| Hypervisor | Reported version family can be compared with the reviewed allowlist; verify exact media/build compatibility and standalone HostAgent identity separately |
| Sizing | Select persona/load/retention profile; verify physical CPU topology, clock and CPU/memory reservation admission; current tools expose only memory summary |
| Storage | One adequately sized disk on one approved datastore, provisioning, free capacity plus headroom, sector format and performance; no automatic reclaim or overcommit |
| Network | Select a standard port group, VLAN, unique guest identity/address, routing and required ports; validate forward/reverse DNS and NTP from the guest network |
| Certificates | Verify ESXi trust on MCP, and plan ISE service certificates, chains, SANs, keys and internal CA recovery; no certificate material in Git |
| Licensing | Confirm ISE VM and applicable feature entitlements and the ESXi license/API limits; successful inventory access proves neither |
| ZTP | Confirm exact-media on-premises key syntax, serial-console/boot behavior and first-login steps; project JSON is never a guest payload |
| Restore | Record exact ISE 3.4 source patch, backup identity/integrity, key reference, target patch and certificate recovery; rehearse isolated restore separately |
| Operations | Review gray/unknown health, visibility gaps, immutable approval/execution design, audit retention and recovery before writes |

## Installation references

The [native ZTP procedure](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html)
supports the user-data path on ESXi 7.0 and later. Bootstrap data is sensitive even
when encoded. The tracked key/value example remains illustrative until reviewed
against the selected media; no unsupported keys have been added.

Cisco's [persona-specific disk table](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_2/r_disk_space_requirements.html)
lists 600 GB minimum production disks for standalone ISE and PAN/MnT profiles,
and 300 GB for PSN-only or pxGrid-only. The project's example chooses 600 GiB plus
80 GiB operational headroom; that extra allowance is local policy, not a Cisco
requirement. Do not add free space across separate datastores to claim a single
virtual disk fits. Cisco's [disk guidelines](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_2/r_disk_space_guidelines.html)
require a single disk and call for fresh installation when expanding its size.

For networking, [Cisco setup requirements](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_3/t_runthesetupprogram.html)
require DNS/NTP connectivity during installation. Management-host reachability is
not proof of guest-network readiness. Review subscriptions and VM entitlements
against the [Cisco licensing guide](https://www.cisco.com/c/en/us/products/collateral/security/identity-services-engine/ise-licensing-guide-og.html).

The current tools leave the exact media, topology, guest network, licenses and
restore compatibility unverified. `deployment_ready` remains false in every report.
