# Troubleshooting

| Symptom | Read-only investigation |
| --- | --- |
| Input rejected | Compare schema 2 examples. Old ESXi credentials/CA settings, arbitrary commands and unknown fields are rejected. |
| Missing dependency | Install the reviewed `mcp` extra in a private environment; offline mode needs no SDK. |
| Host pin or SSH failure | Verify the dedicated key, exact source restriction, separately confirmed Ed25519 fingerprint and forced command through the approved administrator. Never accept a replacement pin blindly. |
| Discovery differs | Stop. Review the server release and contract. Do not widen the allowlist automatically. |
| Discovery works, health times out | MCP SSH reachability does not prove server-to-ESXi HTTPS reachability. Check the service's configured destination, DNS result, source address, TCP 443 and firewall objects/rule order through approved diagnostics. Ping/ICMP is not part of the MCP health transport. |
| Health read returns an error | Administrator checks ESXi TLS trust, service credentials, account state and read visibility on MCP; do not copy credentials to the workstation. |
| Wrong host or stale timestamp | Stop; verify server target configuration and clocks before another read. |
| Gray aggregate health | Broadcom defines gray as unknown. It does not diagnose hardware failure; obtain a bounded sensor/alarm read or administrator evidence. |
| Missing CPU/network/maintenance facts | Expected with the existing four tools. Null becomes unresolved, not PASS. See the proposed read extensions. |
| Capacity failure | Review approved storage and workload choices. Do not delete unrelated files/VMs, resize or provision thin disks to bypass the check. |
| Incomplete snapshot inventory | Some VMs were skipped. Neither a complete nor empty list validates backups. |
| Client timeout/interruption | Client closure is not proof of remote SDK cancellation/logout. Administrator checks lingering reads/sessions before retries. |
| Native Codex tools missing | CLI transport validation and Codex tool loading are separate. Check the saved connection in a fresh client session; do not expand runtime privileges. |
| Live audit root rejected | Use an existing owner-only directory outside Git, not a symlink or public/shared path. |
| Deploy requires dry-run | Expected; no writer or restore executor exists. |

[Broadcom health values](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest/vim.ManagedEntity.Status.html)
define the meaning of the aggregate status. Actual fault diagnosis requires more evidence.

For future installation faults, use [Cisco's ZTP procedure](https://www.cisco.com/c/en/us/td/docs/security/ise/3-5/install_guide/b_ise_Installation_Guide_35/g_referenceinformation/t_zerotouchprovisioning.html)
and private serial-console evidence. Validate DNS/NTP from the guest network and
compare payload syntax to the exact media. Do not invent alternate keys, bypass
checks by default, or place payloads/backups/console captures in Git issues.
