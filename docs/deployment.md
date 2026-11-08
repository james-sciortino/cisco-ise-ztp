# Manual ISE ZTP deployment

## Prepare

Use Cisco's [ISE 3.5 installation procedure](references.md) and confirm the selected
OVA, ESXi compatibility, persona sizing, reservations, disk provisioning, storage
capacity, licensing, network mapping, DNS and NTP before starting. The example
addresses are fictional and will not work unchanged.

Cisco's production standalone/PAN/MnT disk guidance calls for at least 600 GB.
Availability of a 300 GB OVA does not make that disk size appropriate for every
persona. Select the supported profile for the intended role and workload.

For a replacement, retain a current off-host native ISE backup, its encryption
key, certificate/private-key and CA recovery exports, and the original release
and patch media. Review the outage and recovery plan before retiring the source.
Stopping a VM does not reclaim its disk space. This guide includes no deletion
procedure. Never run old and new nodes with the same IP address simultaneously.

## Create the private file

Copy `examples/ise-ztp.conf.example` to `local/ise-ztp.conf`. Use a plain-text editor.
In macOS TextEdit, choose **Format > Make Plain Text**, disable smart quotes, and
keep the `.conf` filename without an added `.txt` extension.

Set the short lowercase hostname and domain separately. Supply the IP, mask,
gateway, DNS servers, NTP server, timezone, SSH preference and administrator
credentials. Secondary and tertiary DNS entries are optional; remove unused
entries. Use real reachable servers. Replace the entire password placeholder,
including angle brackets, with an ISE-compliant password. Do not add quotes.

The private file may be moved elsewhere; update the encoding command accordingly.
Keep it private and out of Git. This configuration bootstraps ISE only: it does
not install a patch or restore a backup automatically.

## Encode locally on macOS

In Terminal, replace the example path below with the absolute path to your file:

```sh
base64 -i "/absolute/path/to/ise-ztp.conf" | tr -d '\r\n' | pbcopy
```

This puts one Base64 string on your clipboard. Repeat after every edit. Do not
encode this guide or the unchanged example. Do not use an online encoder:
Base64 is reversible and includes the password.

## Configure ESXi

1. In the standalone ESXi Host Client, import the approved ISE OVA. Disable
   automatic power-on and select the appropriate deployment profile.
2. While powered off, verify CPU, memory and reservations, disk/datastore, and
   management NIC port-group mapping. Review each NIC's connect state explicitly.
3. Open **Edit settings > VM Options > Advanced > Edit Configuration** (the UI
   may group this under **Configuration Parameters**).
4. Add the parameter `guestinfo.ise.ztp`. Paste the encoded string as its value
   and save. This is the file's encoded contents, not its filename or path.
5. Configure serial-console monitoring according to Cisco's procedure. Confirm
   the source node is off if reusing its identity, then power on the replacement.
6. Monitor ZTP through the serial console. Cisco documents VM-console monitoring
   once the setup prompt appears. DNS and NTP must work from the guest network.

No ZTP configuration image is needed for this VM-user-data method. ESXi does not
need access to the original configuration file. Do not apply cloud-specific ZTP
key names to this on-premises configuration.

## After setup

Complete the initial GUI password change and [validation checklist](validation.md).
For a backup/restore migration, apply the reviewed patch for the target release
before restoring the native backup. Keep patch downloads in their original
format and verify the publisher checksum before use; Safari can automatically
expand `.tar.gz` downloads if “Open safe files after downloading” is enabled.

After successful bootstrap and credential rotation, arrange removal of the
sensitive VM parameter and unnecessary local/encoded copies. Replace clipboard
contents with harmless text. Keep credentials out of screenshots and logs.

## If setup fails

Check the serial-console error and validate IP/mask/gateway, network mapping,
forward/reverse DNS and NTP. Do not bypass checks to hide a connectivity issue.
For incorrect user data, follow Cisco's retry procedure: power off, correct the
private file, regenerate Base64, replace the VM parameter and restart. Escalate
unexplained errors with the specific installer messages, excluding secrets.
