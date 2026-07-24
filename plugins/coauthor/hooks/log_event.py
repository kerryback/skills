#!/usr/bin/env python3
"""PostToolUse hook: append tool-call I/O to the project's canonical JSONL.

Captures the hands-on activity of the Claude subagents (Verifier/Analyst/
Replicator) and the Coordinator into the same events.jsonl the debate voices
feed, so render.py can weave a complete per-round transcript. Debate-voice
prompts/responses are logged separately by debate.py; Claude Code also keeps its
own full session transcript natively.

Safe by construction: only writes when coauthor is active (a `.coauthor/` folder
at or above cwd), never raises into the tool loop, and redacts secrets. Round
number is read from <root>/.coauthor/round if present.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REDACT = [
    (re.compile(r"sk-(?:or-)?[A-Za-z0-9_\-]{16,}"), "sk-<redacted>"),
    (re.compile(r"(?i)(api[_-]?key|authorization|bearer)\s*[:=]\s*\S+"), r"\1=<redacted>"),
    (re.compile(r"postgres(?:ql)?://[^\s\"']+"), "postgresql://<redacted>"),
]


def redact(obj):
    if isinstance(obj, str):
        for pat, repl in _REDACT:
            obj = pat.sub(repl, obj)
        return obj
    if isinstance(obj, dict):
        return {k: redact(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


def project_root() -> Path | None:
    p = Path.cwd().resolve()
    for cand in [p, *p.parents]:
        if (cand / ".coauthor").is_dir():
            return cand
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    root = project_root()
    if root is None:
        return  # coauthor not active here; stay silent
    rnd_file = root / ".coauthor" / "round"
    rnd = int(rnd_file.read_text().strip()) if rnd_file.exists() else 0

    record = redact({
        "ts": datetime.now(timezone.utc).isoformat(),
        "project_id": root.name,
        "round_id": rnd,
        "kind": "tool_use",
        "tool": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "tool_response": payload.get("tool_response"),
    })
    logs = root / ".coauthor" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never break the tool loop
