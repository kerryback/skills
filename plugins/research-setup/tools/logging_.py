"""The event log: append-only JSONL, secret-redacted, one file per run.

This is the exhaustive record of what a session actually did. Two things feed
it: the PostToolUse/UserPromptSubmit hook in `tools/log_event.py` (every prompt
and every tool call, Coordinator and subagents alike) and `tools/debate/debate.py`
(every voice call, prompt and response). Nothing renders it and nothing curates
it — read the JSONL directly when you need a slice of it.

It is NOT memory. `project/global/state.md` is the curated truth and
`project/<author>/session.md` the handoff; those are committed and rewritten.
The event log is written once, never read forward as context, and gitignored: a
real project's runs reach tens of megabytes, dominated by tool payloads, which
is more than GitHub will take and more than a context window should ever see.

Logs live at `project/<author>/logs/events-<run>.jsonl`. Naming by RUN rather
than by round is what keeps two coauthors in a shared clone from ever writing
the same file — a round counter is per-machine, so both of them have a "round
3", but `<author>-<date>-<time>` says who ran it and when and cannot collide.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .runid import author_dir, current_run_id

# Redaction happens in one place, for every writer, so no seat can leak a key to
# disk by forgetting. Patterns are deliberately broad: a false positive costs a
# line of log, a false negative costs a credential.
_REDACTIONS = [
    (re.compile(r"sk-or-[A-Za-z0-9_\-]{16,}"), "sk-or-<redacted>"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{16,}"), "sk-<redacted>"),
    (re.compile(r"(?i)(api[_-]?key|secret|token|authorization|bearer)\s*[:=]\s*\S+",),
     r"\1=<redacted>"),
    (re.compile(r"postgres(?:ql)?://[^\s\"']+"), "postgresql://<redacted>"),
    # .pgpass-style host:port:db:user:password
    (re.compile(r"(?m)^([^:\s]+:\d+:[^:]+:[^:]+):[^:\s]+$"), r"\1:<redacted>"),
]


def redact(text: str) -> str:
    if not isinstance(text, str):
        text = json.dumps(text, default=str)
    for pat, repl in _REDACTIONS:
        text = pat.sub(repl, text)
    return text


def redact_obj(obj):
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    return obj


def append_event(project_dir: str | Path, event: dict) -> None:
    """Append one fully-formed event (it carries its own timestamp and ids).

    The run stamp goes into the record as well as the filename, so events stay
    attributable if the files are later concatenated or renamed.
    """
    run = event.get("run_id") or current_run_id(project_dir)
    record = redact_obj({"run_id": run, **event})
    path = author_dir(project_dir) / "logs" / f"events-{run}.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def read_events(project_dir: str | Path, run: str | None = None):
    """Yield the events of one run (default: the current one), in order.

    Provided so reading a slice does not mean writing an ad-hoc parser each
    time. Filter what this yields — by `kind`, by `tool`, by a time span —
    rather than loading a whole log into context.
    """
    run = run or current_run_id(project_dir)
    path = author_dir(project_dir) / "logs" / f"events-{run}.jsonl"
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # a truncated last line beats losing the file


def main() -> None:
    """`python3 -m tools.logging_ [--run <id>] [--kind tool_use] [--tool Bash]`"""
    import argparse

    ap = argparse.ArgumentParser(description="read a slice of the event log")
    ap.add_argument("--project", default=".", help="project root")
    ap.add_argument("--run", help="run id (default: the current run)")
    ap.add_argument("--kind", help="filter by event kind, e.g. PostToolUse")
    ap.add_argument("--tool", help="filter by tool name, e.g. Bash")
    ap.add_argument("--limit", type=int, default=0, help="last N matching events")
    args = ap.parse_args()

    rows = [
        e for e in read_events(args.project, args.run)
        if (not args.kind or e.get("kind") == args.kind)
        and (not args.tool or e.get("tool") == args.tool)
    ]
    if args.limit:
        rows = rows[-args.limit:]
    for e in rows:
        print(json.dumps(e, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
