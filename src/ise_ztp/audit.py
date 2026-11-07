"""Private local evidence; never store runtime observations inside a Git checkout."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile

from .errors import PreflightError


def now():
    return datetime.now(timezone.utc).isoformat()


class Audit:
    def __init__(self, root):
        root = Path(root).expanduser()
        if not root.is_absolute() or not root.is_dir() or root.is_symlink():
            raise PreflightError("Audit root must be an existing absolute private directory outside Git.")
        root = root.resolve()
        info = root.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PreflightError("Audit root must be owned by the current user with mode 700.")
        if any((p / ".git").exists() for p in (root, *root.parents)):
            raise PreflightError("Live audit records and inventory must be outside Git checkouts.")
        self.path = Path(tempfile.mkdtemp(prefix="ise-preflight-", dir=root))
        self.event("run_started")

    def event(self, event, **values):
        # Call sites supply only fixed event/tool names and counts, never fault text.
        fd = os.open(self.path / "events.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a") as stream:
            stream.write(json.dumps({"at": now(), "event": event, **values}) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def write(self, name, data):
        if name not in {"inventory.json", "report.json"}:
            raise PreflightError("Unsupported audit artifact.")
        fd = os.open(self.path / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write("\n")
