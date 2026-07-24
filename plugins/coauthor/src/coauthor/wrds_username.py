"""Resolve the WRDS username portably — no hardcoding, works for any user.

The wrds library needs the username passed to `wrds.Connection(wrds_username=...)`
(it never reads it from ~/.pgpass). To keep the skill reusable across users, never
hardcode it — resolve it at runtime, first hit wins:

  1. $WRDS_USER environment variable (explicit override).
  2. ~/.wrds — first non-comment line, or a `WRDS_USER=<id>` line.
  3. ~/.pgpass — field 4 (username) of the line whose host contains "wrds".
     Zero extra setup: anyone who has WRDS working already has this.

Use it in an Analyst script (self-contained — copy the function so the script
stays re-runnable without this package on the path), or run as a tool:
    python -m coauthor.wrds_username     # prints the resolved username
"""
from __future__ import annotations

import os
from pathlib import Path


def wrds_username() -> str:
    u = os.environ.get("WRDS_USER")
    if u and u.strip():
        return u.strip()

    wrds_file = Path.home() / ".wrds"
    if wrds_file.exists():
        for line in wrds_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().startswith("WRDS_USER"):
                return line.split("=", 1)[1].strip()
            return line  # a bare username line

    pgpass = Path.home() / ".pgpass"
    if pgpass.exists():
        for line in pgpass.read_text(encoding="utf-8").splitlines():
            parts = line.split(":")
            if len(parts) >= 5 and "wrds" in parts[0].lower():
                return parts[3]

    raise SystemExit(
        "WRDS username not found. Set $WRDS_USER, create ~/.wrds with your WRDS id, "
        "or ensure ~/.pgpass has a wrds line (host:port:db:USERNAME:password)."
    )


if __name__ == "__main__":
    print(wrds_username())
