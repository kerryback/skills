#!/usr/bin/env python3
"""Claude Code hook: write every prompt and every tool call to the event log.

Registered in this repo's `.claude/settings.json`, so it runs for sessions in
THIS project and nowhere else, and it travels with the clone — every coauthor
gets the same record without installing anything.

What it captures, per run:
  - SessionStart / SessionEnd  — when a session began and how it ended
  - UserPromptSubmit           — what the human actually asked for
  - PostToolUse                — every tool call and its result, Coordinator and
                                 subagents alike

That is the whole hands-on record of a session. It writes itself; you never
curate it and never read it forward as context (`state.md` and `session.md` are
for that). Read a slice of it when a specific question needs one:

    python3 -m tools.logging_ --tool Bash --limit 20

Safe by construction: it never raises into the tool loop, never prints (stdout
from a hook is fed back to the model), redacts secrets before anything reaches
disk, and exits 0 whatever happens.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# The hook runs with no PYTHONPATH and from whatever cwd the session is in, so
# locate the repo from this file rather than from the process. Importing the
# real module beats duplicating redaction into a second place that drifts.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.logging_ import append_event  # noqa: E402
from tools.runid import current_run_id, user_slug  # noqa: E402

# Carried as named fields; everything else in the payload goes under "data" so a
# new hook field is recorded the day it appears rather than silently dropped.
_LIFTED = {"session_id", "cwd", "hook_event_name", "tool_name"}
# The transcript path names one machine's home directory and Claude Code already
# keeps that file — logging it adds noise and a stale pointer.
_DROPPED = {"transcript_path"}


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return
    if not isinstance(payload, dict):
        return

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "project_id": REPO.name,
        "author": user_slug(),
        "run_id": current_run_id(REPO),
        "kind": payload.get("hook_event_name") or "unknown",
        "session_id": payload.get("session_id"),
        "cwd": payload.get("cwd"),
        "tool": payload.get("tool_name"),
        "data": {k: v for k, v in payload.items()
                 if k not in _LIFTED and k not in _DROPPED},
    }
    append_event(REPO, event)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a logging failure must never break the session
