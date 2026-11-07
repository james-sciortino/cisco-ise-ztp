# Security and Git hygiene

Treat the original bootstrap file, its Base64 value, VM advanced configuration,
and any console capture as sensitive. Encoding is reversible. Never send a real
payload to a public encoding service or log it. This initial CLI does not load
ZTP content, so it cannot accidentally render it in a plan.

Store all environment-specific settings and captured inventory under ignored
`local/`, with restrictive directory/file permissions. Use a secret manager for
ESXi credentials, ISE bootstrap passwords, backup keys, and certificate keys.
Export credentials only for the lifetime of a later authorized live operation;
do not include them in command-line arguments or shell history.

The adapter verifies TLS with the system trust store or an explicit CA bundle.
There is no insecure bypass. Its credential object and inventory are not logged.
Normal output is an allowlist of static check messages and mode/status flags.
Raw JSON parsing errors and SDK fault text are suppressed, because they can
contain sensitive values. This is data minimization, not a general-purpose
redaction guarantee for future code or third-party debug logging.

The local JSON reader limits the bytes it actually reads and rejects pipes and
device files. Strict hostname/IP checks reject malformed names before live mode
can use them. CLI flag abbreviations cannot enable remote access. These checks
do not establish ownership of an endpoint: review the full private configuration
and TLS identity before authorizing live access.

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
