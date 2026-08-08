#!/usr/bin/env python3
"""Read and write a slide deck's speaker notes, for .qmd and .pptx decks.

Claude Code uses this to draft narration. A .qmd is plain text and can also just
be edited directly; a .pptx is a zip of XML and cannot, which is what this is
for. Both go through the same commands so the skill has one instruction.

  # every slide's title, text and current notes, as JSON
  python3 scripts/deck_notes.py read lecture-3.pptx

  # set notes on specific slides (0-based indexes), leaving the rest alone
  python3 scripts/deck_notes.py write lecture-3.pptx --notes notes.json
  echo '{"0": "Opening line…", "3": "…"}' | python3 scripts/deck_notes.py write lecture-3.pptx

Writing edits the deck in place. The .pptx round-trip goes through python-pptx,
which rewrites the file — slides, layouts and media are preserved, but it is
still someone's deck, so keep a copy if the deck is precious.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))


def _sources():
    try:
        from builderlib import sources
        return sources
    except ImportError as e:
        raise SystemExit(
            f"Could not import the deck reader ({e}). Run this with the app's "
            "Python: ~/.voiceover/venv/bin/python scripts/deck_notes.py …")


def cmd_read(args):
    sources = _sources()
    slides = sources.read_slides(Path(args.deck).expanduser())
    out = [{"index": s["index"], "title": s["title"],
            "slide_text": s["slide_text"], "notes": s["notes"]}
           for s in slides]
    json.dump({"deck": str(args.deck), "slides": out}, sys.stdout,
              indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def cmd_write(args):
    sources = _sources()
    raw = (Path(args.notes).read_text(encoding="utf-8") if args.notes
           else sys.stdin.read())
    data = json.loads(raw)
    # Accept either {"0": "…"} or {"slides": [{"index": 0, "notes": "…"}]}.
    if isinstance(data, dict) and "slides" in data:
        notes = {int(s["index"]): s.get("notes", "") for s in data["slides"]}
    else:
        notes = {int(k): v for k, v in data.items()}
    deck = Path(args.deck).expanduser()
    changed = sources.write_notes(deck, notes)
    print(f"Wrote notes on {changed} slide{'' if changed == 1 else 's'} of {deck.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("read", help="print slides + notes as JSON")
    r.add_argument("deck", help="path to a .qmd or .pptx")
    r.set_defaults(func=cmd_read)

    w = sub.add_parser("write", help="set notes on given slides, in place")
    w.add_argument("deck", help="path to a .qmd or .pptx")
    w.add_argument("--notes", help="JSON file of {index: notes}; default stdin")
    w.set_defaults(func=cmd_write)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
