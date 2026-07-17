"""Deck narration parser for the narrated-deck player.

Parses a rendered Quarto reveal.js deck, extracting each slide's narration from
its <aside class="notes"> in reveal order plus the visible slide text. This is
the parsing half only; TTS synthesis lives in builderlib/audio_gen.py (ElevenLabs).

Outputs (when run as a CLI):
  narration.json   {"slides": [{"index", "title", "narration", "slide_text"}, ...]}

Usage:
  python3 generate_audio_ref.py --dry-run    # extract + print narration, write narration.json
  python3 generate_audio_ref.py --self-test  # run the parser against synthetic HTML
"""

import argparse
import json
import sys
import re
from pathlib import Path

from bs4 import BeautifulSoup

DECK_HTML = Path(__file__).parent / "deck" / "5_security.html"
NARRATION_JSON = Path(__file__).parent / "narration.json"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def enumerate_slides(html: str):
    """Return the deck's slides in reveal.js linear order.

    Quarto revealjs normally emits a flat list of <section> elements inside
    <div class="slides">. Some decks nest one level (a top-level <section>
    wrapping child <section>s); in that case reveal treats each child as its
    own slide, so we flatten one level.

    Returns a list of BeautifulSoup <section> tags.
    """
    soup = BeautifulSoup(html, "html.parser")
    slides_div = soup.find("div", class_="slides")
    if slides_div is None:
        raise ValueError("Could not find <div class='slides'> - is this a reveal.js deck?")

    slides = []
    for top in slides_div.find_all("section", recursive=False):
        children = top.find_all("section", recursive=False)
        if children:
            slides.extend(children)
        else:
            slides.append(top)
    return slides


def extract_slide(section) -> dict:
    """Extract narration and visible text from one <section>."""
    narration = ""
    aside = section.find("aside", class_="notes")
    if aside is not None:
        narration = normalize_ws(aside.get_text(" "))
        # Remove the aside so it doesn't leak into slide_text.
        aside.extract()

    slide_text = normalize_ws(section.get_text(" "))
    title = ""
    heading = section.find(re.compile(r"^h[1-6]$"))
    if heading is not None:
        title = normalize_ws(heading.get_text(" "))

    return {"title": title, "narration": narration, "slide_text": slide_text}


def parse_deck(html: str) -> list:
    """Parse deck HTML into [{'index', 'title', 'narration', 'slide_text'}, ...]."""
    out = []
    for i, section in enumerate(enumerate_slides(html)):
        info = extract_slide(section)
        info["index"] = i
        out.append(info)
    return out


# ---------------------------------------------------------------------------
# Main (parse only; no TTS)
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="extract and print narration; write narration.json")
    parser.add_argument("--self-test", action="store_true",
                        help="run the parser against synthetic HTML and exit")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if not DECK_HTML.exists():
        print(f"Deck not found: {DECK_HTML}", file=sys.stderr)
        print("Render the deck first (see README), or run --self-test to check the parser.",
              file=sys.stderr)
        return 1

    slides = parse_deck(DECK_HTML.read_text(encoding="utf-8"))
    total_words = sum(len(s["narration"].split()) for s in slides)
    narrated = [s for s in slides if s["narration"]]

    print(f"Parsed {len(slides)} slides; {len(narrated)} have narration; "
          f"{total_words} narration words total (~{total_words / 150:.0f} min of audio).")

    NARRATION_JSON.write_text(
        json.dumps({"slides": slides}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Wrote {NARRATION_JSON}")

    for s in slides:
        print(f"\n--- slide {s['index']:03d}  [{s['title'] or 'untitled'}] "
              f"({len(s['narration'].split())} words)")
        print(s["narration"] or "(no narration)")
    return 0


# ---------------------------------------------------------------------------
# Self-test (no deck, no API)
# ---------------------------------------------------------------------------
FLAT_HTML = """
<html><body><div class="reveal"><div class="slides">
  <section id="title-slide"><h1>AI Security</h1><p>Kerry Back</p></section>
  <section id="s1"><h2>Prompt Injection</h2><p>Attacks   embed instructions.</p>
    <aside class="notes">Prompt injection is the top risk. It hides instructions in data.</aside>
  </section>
  <section id="s2"><h2>No Notes Here</h2><p>Body only.</p></section>
</div></div></body></html>
"""

NESTED_HTML = """
<html><body><div class="reveal"><div class="slides">
  <section id="title-slide"><h1>Title</h1></section>
  <section>
    <section id="a"><h2>A</h2><aside class="notes">Notes for A.</aside></section>
    <section id="b"><h2>B</h2><aside class="notes">Notes for B.</aside></section>
  </section>
  <section id="c"><h2>C</h2><aside class="notes">Notes for C.</aside></section>
</div></div></body></html>
"""


def self_test() -> int:
    flat = parse_deck(FLAT_HTML)
    assert len(flat) == 3, f"expected 3 flat slides, got {len(flat)}"
    assert flat[0]["narration"] == "", "title slide should have no narration"
    assert flat[0]["title"] == "AI Security"
    assert flat[1]["narration"].startswith("Prompt injection is the top risk.")
    assert "hides instructions" in flat[1]["narration"]
    assert "Prompt injection is the top risk" not in flat[1]["slide_text"], \
        "notes leaked into slide_text"
    assert "Attacks embed instructions." in flat[1]["slide_text"], "whitespace not normalized"
    assert flat[2]["narration"] == ""

    nested = parse_deck(NESTED_HTML)
    assert len(nested) == 4, f"expected 4 flattened slides, got {len(nested)}"
    assert [s["title"] for s in nested] == ["Title", "A", "B", "C"]
    assert nested[1]["narration"] == "Notes for A."
    assert nested[2]["narration"] == "Notes for B."
    assert nested[3]["narration"] == "Notes for C."

    print("self-test: all assertions passed (flat + one-level-nested decks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
