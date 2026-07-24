"""Locate where coauthor is active and load the debate-voice roster.

coauthor is a skill any directory can use — there is no special "project" type and
no marker file to create by hand. coauthor is simply *active* in a directory when a
`.coauthor/` folder exists there (created by `/coauthor:init`). Everything coauthor
owns lives inside `.coauthor/`; the only thing it puts at the repo root is the
analyst's `workspace/`.

The roster — which OpenRouter model backs each debate seat — lives in
`.coauthor/config.toml`, falling back to the plugin's `config.example.toml`.
Roster is config, not code: adding or swapping a voice is a one-line edit there.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]  # .../plugins/coauthor
CHARTERS_DIR = PLUGIN_ROOT / "charters"
DEFAULT_ROSTER = PLUGIN_ROOT / "config.example.toml"


def find_project_root(start: str | Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) to the nearest dir containing a
    `.coauthor/` folder — that is where coauthor is active."""
    p = Path(start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / ".coauthor").is_dir():
            return cand
    # Fall back to cwd so logging still works before init during dev.
    return Path.cwd().resolve()


def load_roster(project_root: str | Path | None = None) -> dict:
    root = Path(project_root) if project_root else find_project_root()
    cfg = root / ".coauthor" / "config.toml"
    path = cfg if cfg.exists() else DEFAULT_ROSTER
    with path.open("rb") as fh:
        return tomllib.load(fh)


def charter_text(role: str) -> str:
    f = CHARTERS_DIR / f"{role}.md"
    if not f.exists():
        raise FileNotFoundError(f"No charter for role '{role}' at {f}")
    return f.read_text(encoding="utf-8")
