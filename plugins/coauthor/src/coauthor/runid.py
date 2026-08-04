"""Per-run identity for log filenames: `<user>-<YYYYMMDD>-<HHMMSS>`.

Shared repos are the reason this exists. A fixed name — one `log.jsonl`, or
anything keyed off a per-machine round counter — means two coauthors write the
same path, and whoever pulls second reconciles interleaved appends by hand.
Every log artifact instead carries who produced it and when, so nothing two
people generate can collide, and the directory listing itself says who ran what.

The current run's stamp lives in `<root>/.coauthor/run` (gitignored, purely
machine-local). `/coauthor:round` stamps a fresh one at the top of each round;
anything that logs outside a round creates one lazily.

Usage (the Coordinator runs this via Bash):
    python -m coauthor.runid --project "$(pwd)" --new   # start a run, print its id
    python -m coauthor.runid --project "$(pwd)"         # print the current id
    python -m coauthor.runid --stamp                    # a fresh stamp, nothing written

`--stamp` is for artifacts written SEVERAL times within one round — the briefs,
which are rewritten each pass of the debate loop. They cannot share the round's
run id or each pass would overwrite the last, so each takes the time it was
written. Everything logged by the run itself uses the run id instead.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path


def user_slug() -> str:
    """Filename-safe identity: git's `user.name`, else the OS login, else `anon`.

    git first because in a shared repo that is the name the collaborators already
    know each other by — the same string that shows up in `git log`.
    """
    name = ""
    try:
        name = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        pass
    name = name or os.environ.get("USER") or os.environ.get("USERNAME") or ""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return slug or "anon"


def new_run_id() -> str:
    # Local time, not UTC: this is a label a human reads against their own clock.
    return f"{user_slug()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def stamp_run(project_dir: str | Path) -> str:
    """Begin a new run and record it. Called at the top of each round."""
    rid = new_run_id()
    d = Path(project_dir) / ".coauthor"
    d.mkdir(parents=True, exist_ok=True)
    (d / "run").write_text(rid + "\n", encoding="utf-8")
    return rid


def current_run_id(project_dir: str | Path) -> str:
    """The run anything logged right now belongs to; created if absent."""
    f = Path(project_dir) / ".coauthor" / "run"
    if f.exists():
        rid = f.read_text(encoding="utf-8").strip()
        if rid:
            return rid
    return stamp_run(project_dir)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--project", help="project root (not needed with --stamp)")
    ap.add_argument("--new", action="store_true", help="start a new run")
    ap.add_argument("--stamp", action="store_true",
                    help="print a fresh <user>-<date>-<time>; writes nothing")
    args = ap.parse_args()
    if args.stamp:
        print(new_run_id())
        return
    if not args.project:
        ap.error("--project is required unless you pass --stamp")
    root = Path(args.project).resolve()
    print(stamp_run(root) if args.new else current_run_id(root))


if __name__ == "__main__":
    main()
