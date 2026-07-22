"""Configuration and cross-platform paths.

Phase 1 needs almost no configuration; sensible defaults let the tool run with
zero setup. A ``config.toml`` (searched in the data dir, then the LITDB_CONFIG
path) can override the database location and, in later phases, the embedding
provider. Everything here is standard library so the core has no dependencies.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for 3.10
    tomllib = None  # type: ignore


APP_NAME = "litdb"


def data_dir() -> Path:
    """Return litdb's per-user home directory.

    Everything litdb owns lives here: the managed virtualenv (``.venv``), the
    database, ``preferences.json``, and the ``.onboarded`` marker. A single fixed
    home (``~/.litdb``) means the runtime does not depend on any project/repo
    folder that a user might delete. Override with LITDB_HOME (used by tests).
    Cross-platform: ``~/.litdb`` works on macOS, Linux, and Windows alike.
    """
    override = os.environ.get("LITDB_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".litdb"


def db_path() -> Path:
    override = os.environ.get("LITDB_DB")
    if override:
        return Path(override).expanduser()
    return data_dir() / "litdb.db"


_DEFAULTS: dict = {
    "embedding": {
        "provider": "ollama",          # ollama | fastembed | voyage | openai
        "model": "nomic-embed-text",
        "dim": 768,
    },
    "policy": {
        "confidential_stay_local": True,
        "local_provider": "ollama:nomic-embed-text",
    },
    "zotero": {
        # Zotero local API (Zotero 7+); used with --local when BBT is absent.
        "local_api": "http://localhost:23119/api/users/0/items",
        # Better BibTeX JSON-RPC; preferred automatically when reachable (adds
        # citation keys). Requires Zotero running with the Better BibTeX add-on.
        "bbt_rpc": "http://localhost:23119/better-bibtex/json-rpc",
    },
    "external": {
        # OpenAlex asks for an email in the "polite pool"; recommended, optional.
        "openalex_mailto": "",
        # Semantic Scholar works without a key; a key raises rate limits.
        "s2_api_key_env": "S2_API_KEY",
        "default_source": "openalex",   # openalex | s2
        "timeout": 20,
    },
}


def _config_file() -> Path | None:
    override = os.environ.get("LITDB_CONFIG")
    if override and Path(override).expanduser().is_file():
        return Path(override).expanduser()
    candidate = data_dir() / "config.toml"
    return candidate if candidate.is_file() else None


def load_config() -> dict:
    """Return defaults deep-merged with any user config.toml, plus preferences.

    config.toml holds technical settings the app needs to run (embedding
    provider, endpoints). Preferences hold the user's behavioral/workflow choices
    (uses_tex, use_better_bibtex, …) and are managed by `litdb prefs`, never
    hand-edited. Both are surfaced here so callers read one config object;
    ``cfg["preferences"]`` is the behavioral layer.
    """
    cfg = {k: dict(v) for k, v in _DEFAULTS.items()}
    path = _config_file()
    if path and tomllib is not None:
        with path.open("rb") as fh:
            user = tomllib.load(fh)
        for section, values in user.items():
            if isinstance(values, dict):
                cfg.setdefault(section, {}).update(values)
            else:
                cfg[section] = values
    cfg["preferences"] = load_prefs()
    return cfg


# --------------------------------------------------------------------------- #
# preferences (per-user behavioral settings) and the onboarding marker
# --------------------------------------------------------------------------- #

def prefs_path() -> Path:
    return data_dir() / "preferences.json"


def load_prefs() -> dict:
    p = prefs_path()
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def save_prefs(prefs: dict) -> None:
    p = prefs_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(prefs, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_pref(key: str, default=None):
    return load_prefs().get(key, default)


def set_pref(key: str, value) -> dict:
    prefs = load_prefs()
    prefs[key] = value
    save_prefs(prefs)
    return prefs


def onboarded_marker() -> Path:
    return data_dir() / ".onboarded"


def is_onboarded() -> bool:
    return onboarded_marker().exists()


def mark_onboarded() -> None:
    p = onboarded_marker()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")


def reset_onboarded() -> bool:
    p = onboarded_marker()
    if p.exists():
        p.unlink()
        return True
    return False
