"""Render the canonical JSONL into readable per-run Markdown transcripts.

Markdown only: it greps, diffs, and reads fine in any editor, and it is what the
Coordinator skims. Outputs land in <project>/.coauthor/logs/transcripts/ and ARE
committed — the run-stamped names make that safe in a shared repo, and Markdown
is what reviews in a diff. The raw JSONL beside them stays gitignored.

Files are named by RUN, not by round number: `<user>-<YYYYMMDD>-<HHMMSS>.md`.
A round counter is per-machine, so in a shared repo two coauthors both produce a
"round 3"; a run stamp says who ran it and when and can never collide. Each
`/coauthor:round` stamps a fresh run (see runid.py).

Usage:
    python -m coauthor.render --project /path/to/project              # every run
    python -m coauthor.render --project /path/to/project --current    # this run only
    python -m coauthor.render --project /path/to/project --run kerry-back-20260803-142530
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .runid import current_run_id


def _load(project_root: Path) -> dict[str, list[dict]]:
    """Read every `events-<run>.jsonl` and group by run.

    The run comes from the record when present and from the filename otherwise,
    so logs copied in from a collaborator group correctly either way. A bare
    `events.jsonl` from before the rename is picked up under "legacy".
    """
    logs = project_root / ".coauthor" / "logs"
    out: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(logs.glob("events*.jsonl")):
        run = f.stem[len("events-"):] if f.stem.startswith("events-") else "legacy"
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            out[e.get("run_id") or run].append(e)
    for events in out.values():
        events.sort(key=lambda e: e.get("ts", ""))
    return out


def _title(run: str, events: list[dict]) -> str:
    """`<run>` plus the rounds it covers, so the number stays readable inside."""
    rounds = sorted({e.get("round_id", 0) for e in events} - {0})
    if not rounds:
        return run
    span = str(rounds[0]) if len(rounds) == 1 else f"{rounds[0]}–{rounds[-1]}"
    return f"{run}  ·  round {span}"


def _md_run(run: str, events: list[dict]) -> str:
    lines = [f"# {_title(run, events)}", ""]
    for e in events:
        seat = e.get("seat") or e.get("kind", "event")
        lines.append(f"## {seat}  ·  {e.get('model', '')}  ·  {e.get('ts', '')}")
        if e.get("kind") == "debate_call":
            brief = next((m["content"] for m in e.get("request_messages", []) if m["role"] == "user"), "")
            lines += ["", "### Brief", "", "```", brief.strip(), "```", ""]
            lines += ["### Response", "", "```json", json.dumps(e.get("response_parsed", {}), indent=2), "```", ""]
        else:
            lines += ["", "```json", json.dumps(e, indent=2), "```", ""]
        u = e.get("usage") or {}
        if u:
            lines.append(f"_tokens: {u.get('total_tokens', '?')}  ·  latency: {e.get('latency_s', '?')}s_")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--run", default=None, help="run id, e.g. kerry-back-20260803-142530")
    ap.add_argument("--current", action="store_true", help="just the run in .coauthor/run")
    args = ap.parse_args()

    root = Path(args.project).resolve()
    out = root / ".coauthor" / "logs" / "transcripts"
    out.mkdir(parents=True, exist_ok=True)

    runs = _load(root)
    if args.run:
        targets = [args.run]
    elif args.current:
        targets = [current_run_id(root)]
    else:
        targets = sorted(runs)
    for run in targets:
        ev = runs.get(run, [])
        (out / f"{run}.md").write_text(_md_run(run, ev), encoding="utf-8")
        print(f"rendered {run}: {len(ev)} events -> {out / (run + '.md')}")


if __name__ == "__main__":
    main()
