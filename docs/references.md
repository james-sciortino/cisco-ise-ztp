# References and implementation decisions

Reviewed 2026-11-07. Cisco's official ISE 3.5 installation documentation is the
authority for installation behavior. Upgrade/administration references govern
restoration; Broadcom references govern SDK mechanics. Local project policies
are not Cisco requirements.

| Source | Applied to |
| --- | --- |
| [Cisco ISE 3.5: Zero Touch Provisioning](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html) | Native VM user-data transport, bootstrap behavior |
| [Cisco ISE 3.5: Hardware and virtual appliance requirements](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_systemrequirements/r_hardwareandvirtualappliancerequirements.html) | Supported hosts and sizing |
| [Cisco ISE 3.5: VMware virtual machine](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/c_vmware_virtual_machine-1.html) | Manual VM construction prerequisites |
| [Cisco ISE 3.5 installation PDF](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35.pdf) | Cross-check; retrieved edition has older host-version wording |
| [Cisco ISE 3.5: Upgrade process](https://www.cisco.com/c/en/us/td/docs/security/ise/articles/cisco-ise-upgrade-methods-35.html) | Backup/restore migration support and method choice |
| [Cisco ISE 3.5: Maintain and Monitor](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/admin_guide/b_ise_admin_3_5/b_ISE_admin_maintain_monitor.html) | Restore target, repository, ADE-OS, identity and recovery behavior |
| [Cisco ISE 3.5: Basic Setup](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/admin_guide/b_ise_admin_3_5/b_ISE_admin_basic_setup.html) | Certificate/CA recovery material |
| [Cisco-authored ZTP article](https://community.cisco.com/t5/security-knowledge-base/ise-zero-touch-provisioning-ztp/ta-p/4541606) | Supplementary on-premises key spellings in “ISE 3.2 and newer”; not a replacement for the 3.5 guide |
| [Broadcom HostSystem SOAP API](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest/vim.HostSystem.html) | Host inventory properties |
| [Broadcom pyVmomi connection code](https://github.com/vmware/pyvmomi/blob/master/pyVim/connect.py) | Direct-host connection and TLS parameters |
| [Broadcom OpaqueNetwork](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest/vim.OpaqueNetwork.html) | Network subclass that must not be accepted as a standard port group |
| [Broadcom DatastoreSummary](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest/vim.Datastore.Summary.html) | Free capacity is only valid for an accessible datastore |

## Resolved discrepancies and open gates

- Current HTML ZTP guidance says ESXi 7.0+; the retrieved older PDF says 6.5+.
  The current requirements chapter lists 7.0/8.0/9.0. This scaffold rejects 6.x
  and defaults to 7.0/8.0; review exact media compatibility before allowing 9.0.
- The current HTML ZTP chapter describes required fields but omits a complete
  key/value template. The minimal example uses the Cisco-authored supplementary
  on-premises format. Exact-media confirmation remains a deployment gate; no
  automated payload validation or rendering is claimed.
- `management_interface` is mentioned in the 3.5 guide, but this repository does
  not infer VM-specific values from the attribute's presence. It is omitted.
- Skip-check flags, optional service keys, and patch options are not needed for
  this first phase. Their omission avoids expanding the untested payload surface.
- The upgrade page's older “limited to 3.2 patch 2” wording is qualified by its
  explicit statement that backup/restore remains supported for later releases.
  The restore runbook preserves exact patch/backup validation as a separate gate.
- Authorized MCP reads have been exercised separately from local tests. Effective
  host privileges, license limits, media integrity, guest boot and restore outcomes
  remain unverified. Private runtime results are not committed to this document.
- The workstation now uses MCP, not pyVmomi. The reviewed existing server's SDK
  negotiation/logout limitations still apply: a local request timeout cannot
  certify remote cancellation or immediate logout.
- [Broadcom ManagedEntityStatus](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest/vim.ManagedEntity.Status.html)
  defines gray as unknown; no hardware-fault cause is inferred.
- [Cisco's persona disk table](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_2/r_disk_space_requirements.html)
  distinguishes administration/monitoring/standalone sizing from PSN-only sizing.
  See [readiness](readiness.md); the example is not a selected deployment profile.
- [Cisco setup requirements](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/b_ise_InstallationGuide_chapter_3/t_runthesetupprogram.html)
  and the [licensing guide](https://www.cisco.com/c/en/us/products/collateral/security/identity-services-engine/ise-licensing-guide-og.html)
  govern network/time and entitlement review. These facts are not supplied by host inventory.
