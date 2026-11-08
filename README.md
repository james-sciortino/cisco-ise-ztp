# Cisco ISE 3.5 ZTP on standalone ESXi

A manual guide to Cisco's native Zero Touch Provisioning using the VM advanced
setting `guestinfo.ise.ztp`. Prepare a configuration, encode it locally, and supply
it to the powered-off ISE VM before booting. No Python package, MCP server, or
vCenter is required for this workflow.

**Status: instructions prepared; end-to-end installation and restoration have not
been validated in this project.** The blog remains a draft until that work succeeds.

## Start here

1. Follow the [deployment steps](docs/deployment.md).
2. Copy the [sanitized configuration example](examples/ise-ztp.conf.example) into
   ignored `local/ise-ztp.conf` and enter your own settings and password privately.
3. Complete the [validation and restoration checklist](docs/validation.md).

[README.txt](README.txt) is a plain-text version for macOS TextEdit.
[References](docs/references.md) identify Cisco's installation procedure and the
supplementary Cisco-authored configuration syntax.

## Keep private data private

Only fictional settings and password placeholders belong in tracked examples.
Actual configurations, Base64 values, backups, keys, certificates, inventories,
and installation media must remain outside Git. `local/` is ignored. Base64 is
not encryption; an encoded ZTP value contains the bootstrap password.

The earlier ESXi/MCP automation work has been deferred. Its committed version
remains in Git history; the unfinished local work was preserved separately in
an ignored local archive. It is not part of this manual deployment guide.

Changes are reviewed on `codex/` branches. Each commit and push requires owner
approval. Publishing documentation does not authorize infrastructure changes.
