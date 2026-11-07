# Security and Git hygiene

Treat the original bootstrap file, its Base64 value, VM advanced configuration,
and any console capture as sensitive. Encoding is reversible. Never send a real
payload to a public encoding service or log it. This initial CLI does not load
ZTP content, so it cannot accidentally render it in a plan.

Keep real settings in ignored `local/`. Keep runtime inventories and audit records
in an owner-only directory outside every Git checkout. The CLI enforces that
location for live evidence. Store all keys, certificates and media outside Git.
ESXi credentials and its CA trust remain on MCP; the client never loads them.

Use a new dedicated SSH key, not another consumer's key, a revoked identity or a
personal administrator credential. Verify the server fingerprint independently.
The CLI requires owner-only regular key/pin files, ignores shared SSH settings,
disables agents, forwarding, terminal and connection reuse, and sends no remote
command. Restrict the server key to the observed source and a root-owned fixed
command. Server-side forced command and ESXi RBAC enforce the real boundary.

The JSON reader rejects special files, excess size, duplicate fields and non-finite
numbers. Live mode is explicit and cannot be enabled by flag abbreviation. The
four-tool catalog must match exactly before any call; the target host must match
before other inventory calls. Returned names are untrusted data, never commands.
Static report messages avoid inventory identifiers. Raw SDK/protocol exceptions
and stderr are suppressed; audit events use fixed names. These protections are
not a general redaction guarantee or an SDK streaming-memory bound.

Audit records use 700 directories and 600 files and contain private inventory.
They are locally mutable evidence, not tamper-resistant approval or server audit
records. The current server lacks per-success client attribution; a future
bounded endpoint needs server-side request IDs, audit retention and operator
review. Local client timeouts do not guarantee remote session termination.

The `.gitignore` excludes private directories, actual `.conf` and Base64 files,
credentials, key/certificate formats, backups, installation media, VM artifacts,
logs, and captures. It permits only the named sanitized ZTP example. Ignore rules
do not prevent forced adds, remove already tracked files, or recognize secrets
embedded in arbitrary source/Markdown files. Before any future commit, inspect:

```sh
git status --short
git diff --cached --stat
git diff --cached
git check-ignore local/preflight.json local/ise-ztp.conf local/payload.b64 backups/example.tar.gpg
```

Review staged content privately and use organizational secret scanning before
publishing. Do not use `git add -f` for ignored material. If a secret enters Git,
rotate it and follow the organization's history-removal process; merely adding
an ignore pattern is insufficient. No Git hooks are silently installed and no
commit or push is performed by the project CLI.
