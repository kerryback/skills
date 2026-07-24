"""Render the canonical JSONL into readable per-round transcripts (MD + HTML).

Both formats come straight from events.jsonl (never HTML-from-Markdown), so each
is optimized: Markdown for grep/skim, HTML for the rich read. Outputs land in
<project>/.coauthor/logs/transcripts/ and are gitignored with the rest of logs/.

Usage:
    python -m coauthor.render --project /path/to/project --round 3
    python -m coauthor.render --project /path/to/project           # all rounds
"""
from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path


def _load(project_root: Path) -> list[dict]:
    f = project_root / ".coauthor" / "logs" / "events.jsonl"
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]


def _by_round(events: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = defaultdict(list)
    for e in events:
        out[e.get("round_id", 0)].append(e)
    return out


def _md_round(rnd: int, events: list[dict]) -> str:
    lines = [f"# Round {rnd}", ""]
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


def _html_round(rnd: int, events: list[dict]) -> str:
    parts = [
        "<!doctype html><meta charset='utf-8'>",
        f"<title>Round {rnd}</title>",
        "<style>body{font:15px/1.5 -apple-system,system-ui,sans-serif;max-width:900px;"
        "margin:2rem auto;padding:0 1rem;color:#111}"
        "h1{border-bottom:2px solid #333}details{margin:.5rem 0}"
        ".seat{background:#f4f6f8;border-left:4px solid #4a6;padding:.4rem .8rem;margin-top:1.5rem}"
        "pre{background:#0d1117;color:#c9d1d9;padding:1rem;overflow-x:auto;border-radius:6px}"
        ".meta{color:#666;font-size:.85em}</style>",
        f"<h1>Round {rnd}</h1>",
    ]
    for e in events:
        seat = html.escape(str(e.get("seat") or e.get("kind", "event")))
        parts.append(f"<div class='seat'><b>{seat}</b> · {html.escape(str(e.get('model','')))} "
                     f"<span class='meta'>{html.escape(str(e.get('ts','')))}</span></div>")
        if e.get("kind") == "debate_call":
            brief = next((m["content"] for m in e.get("request_messages", []) if m["role"] == "user"), "")
            parts.append("<details><summary>Brief</summary><pre>"
                         + html.escape(brief.strip()) + "</pre></details>")
            parts.append("<pre>" + html.escape(json.dumps(e.get("response_parsed", {}), indent=2)) + "</pre>")
        else:
            parts.append("<pre>" + html.escape(json.dumps(e, indent=2)) + "</pre>")
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--round", type=int, default=None)
    args = ap.parse_args()

    root = Path(args.project).resolve()
    out = root / ".coauthor" / "logs" / "transcripts"
    out.mkdir(parents=True, exist_ok=True)

    rounds = _by_round(_load(root))
    targets = [args.round] if args.round is not None else sorted(rounds)
    for rnd in targets:
        ev = rounds.get(rnd, [])
        (out / f"round-{rnd:03d}.md").write_text(_md_round(rnd, ev), encoding="utf-8")
        (out / f"round-{rnd:03d}.html").write_text(_html_round(rnd, ev), encoding="utf-8")
        print(f"rendered round {rnd}: {len(ev)} events -> {out}")


if __name__ == "__main__":
    main()
