"""Settings for the polls app.

There is very little here. Polls need no relay and no credentials -- answers are
short bits of text and numbers going one way over the same connection that
served the page -- so the only thing worth keeping between launches is a fixed
room code.

    ~/.polls/config.json

    {"code": "4271"}
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any

HOME_DIR = Path(os.environ.get("POLLS_HOME", Path.home() / ".polls"))
CONFIG_PATH = HOME_DIR / "config.json"


def load() -> dict[str, Any]:
    try:
        with CONFIG_PATH.open() as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def room_code(cfg: dict[str, Any] | None = None) -> str:
    cfg = load() if cfg is None else cfg
    fixed = str(cfg.get("code") or "").strip()
    return fixed or f"{secrets.randbelow(9000) + 1000}"
