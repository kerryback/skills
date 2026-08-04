"""Canonical event log: append-only JSONL, secret-redacted.

This is the single sink every seat feeds, and the complete record of a project:
debate calls log through here directly, and Agent-SDK / subagent tool activity is
captured by the PostToolUse hook, which also calls append_event. Nothing renders
or summarizes it — read it directly (it is line-delimited JSON) when you need it.

Logs live under <root>/.coauthor/logs/log-<run>.jsonl and are gitignored — they
grow past what GitHub accepts, and `state.md` + litdb notes are the committed
record. The run stamp (`<user>-<date>-<time>`, see runid.py) keeps two coauthors
in a shared repo from ever writing the same file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .runid import current_run_id

# Redaction: never let a secret reach disk. One place, enforced for all seats.
_REDACTIONS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "sk-<redacted>"),
    (re.compile(r"sk-or-[A-Za-z0-9_\-]{16,}"), "sk-or-<redacted>"),
    (re.compile(r"(?i)(api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"), r"\1=<redacted>"),
    # database connection strings and .pgpass-style host:port:db:user:pw
    (re.compile(r"postgres(?:ql)?://[^\s\"']+"), "postgresql://<redacted>"),
    (re.compile(r"(?m)^([^:\s]+:\d+:[^:]+:[^:]+):[^:\s]+$"), r"\1:<redacted>"),
]


def redact(text: str) -> str:
    if not isinstance(text, str):
        text = json.dumps(text, default=str)
    for pat, repl in _REDACTIONS:
        text = pat.sub(repl, text)
    return text


def _redact_obj(obj):
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: _redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    return obj


def append_event(project_dir: str | Path, event: dict) -> None:
    """Append one fully-formed event record (already carrying its own ids/ts).

    `project_dir` is the root where coauthor is active; logs live in
    `.coauthor/logs/` so nothing lands at the repo root. The run stamp is added
    to the record as well as the filename, so events stay attributable even if
    the files are later renamed or concatenated.
    """
    logs = Path(project_dir) / ".coauthor" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    run = event.get("run_id") or current_run_id(project_dir)
    record = _redact_obj({"run_id": run, **event})
    with (logs / f"log-{run}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
