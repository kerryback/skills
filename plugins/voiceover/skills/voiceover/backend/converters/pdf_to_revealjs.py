"""Convert a PDF slide deck into an image-per-slide Quarto reveal.js deck.

Renders each PDF page to a PNG and emits:
  <out>/images/slide-NNN.png        one PNG per page (1-based, zero-padded)
  <out>/<name>.qmd                  a full-bleed image-per-slide Quarto deck,
                                    each slide carrying an (initially empty)
                                    `::: {.notes}` block for narration
  <out>/revealjs-style.scss         the shared full-bleed image style
  <out>/narration.stub.json         {"slides": [{index, image, narration}, ...]}
                                    a scaffold the MODEL fills in by viewing
                                    each PNG (that is the point — use vision).

Narration itself is NOT written here; the agent running the skill views each
slide PNG and authors the spoken narration, then re-runs this script with
--narration to bake the text into the .qmd notes, or edits the .qmd directly.
After that: `quarto render <name>.qmd`, then generate_audio.py.

Reveal slide index == page order (0-based); no separate title slide is emitted,
so page k maps to reveal index k, which is what generate_audio.py will assign.

Usage:
  python3 pdf_to_revealjs.py deck.pdf --out ../deck --dpi 150
  python3 pdf_to_revealjs.py deck.pdf --out ../deck --narration narration.stub.json
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCSS = SCRIPT_DIR / "assets" / "revealjs-style.scss"

FALLBACK_SCSS = """/*-- scss:defaults --*/
$body-bg: #000000;
/*-- scss:rules --*/
.reveal .slides section h1:empty,
.reveal .slides section h2:empty { display: none; margin: 0; padding: 0; height: 0; }
.reveal .slides section { height: 100%; padding: 0; }
.reveal aside.notes { font-size: 0.6em; line-height: 1.4; }
"""


def render_pdf_to_pngs(pdf_path: Path, img_dir: Path, dpi: int) -> list:
    """Render each PDF page to a PNG. Returns a list of relative image paths."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.exit("PyMuPDF (pymupdf) is required: pip install pymupdf")

    img_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    images = []
    for i, page in enumerate(doc):
        name = f"slide-{i + 1:03d}.png"
        pix = page.get_pixmap(matrix=matrix)
        pix.save(str(img_dir / name))
        images.append(f"images/{name}")
    doc.close()
    return images


def write_scss(out_dir: Path) -> None:
    if SHARED_SCSS.exists():
        shutil.copyfile(SHARED_SCSS, out_dir / "revealjs-style.scss")
    else:
        (out_dir / "revealjs-style.scss").write_text(FALLBACK_SCSS, encoding="utf-8")


def build_qmd(slides: list, out_qmd: Path) -> None:
    """slides: [{"image": "images/slide-001.png", "narration": ""}, ...]"""
    parts = [
        "---",
        "format:",
        "  revealjs:",
        "    theme: [default, revealjs-style.scss]",
        "    width: 1920",
        "    height: 1080",
        "    margin: 0",
        "    controls: true",
        "    progress: true",
        "    slide-number: false",
        "    transition: fade",
        "---",
        "",
    ]
    for s in slides:
        img = s["image"]
        narration = (s.get("narration") or "").strip()
        parts.append(
            f'## {{background-image="{img}" background-size="contain" '
            f'background-color="black"}}'
        )
        parts.append("")
        parts.append("::: {.notes}")
        parts.append(narration)  # empty string => empty notes block to fill in
        parts.append(":::")
        parts.append("")
    out_qmd.write_text("\n".join(parts), encoding="utf-8")


def write_stub(slides: list, stub_path: Path) -> None:
    data = {
        "slides": [
            {"index": i, "image": s["image"], "narration": s.get("narration", "")}
            for i, s in enumerate(slides)
        ]
    }
    stub_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", help="input PDF deck")
    ap.add_argument("--out", default="deck", help="output deck directory (default: deck)")
    ap.add_argument("--name", default=None, help="output .qmd basename (default: from PDF)")
    ap.add_argument("--dpi", type=int, default=150, help="render resolution (default: 150)")
    ap.add_argument("--narration", default=None,
                    help="filled narration JSON (rebuild .qmd notes; skip re-rendering "
                         "PNGs if they already exist)")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.exit(f"PDF not found: {pdf_path}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = out_dir / "images"
    name = args.name or pdf_path.stem
    out_qmd = out_dir / f"{name}.qmd"

    # Narration-injection mode: reuse existing PNGs, overlay narration by slide
    # index. The narration file only needs [{index, narration}, ...] (or bare
    # positional order); images come from disk, so any narration.json — the stub,
    # a hand-authored list, or generate_audio.py's output — works.
    if args.narration:
        # Re-render PNGs only if missing.
        if not img_dir.exists() or not any(img_dir.glob("*.png")):
            render_pdf_to_pngs(pdf_path, img_dir, args.dpi)
        images = sorted(f"images/{p.name}" for p in img_dir.glob("*.png"))

        narr = json.loads(Path(args.narration).read_text(encoding="utf-8"))
        entries = narr.get("slides", narr) if isinstance(narr, dict) else narr
        by_index = {}
        for pos, e in enumerate(entries):
            idx = e.get("index", pos) if isinstance(e, dict) else pos
            text = e.get("narration", "") if isinstance(e, dict) else str(e)
            by_index[idx] = text

        slides = [{"image": img, "narration": by_index.get(i, "")}
                  for i, img in enumerate(images)]
        write_scss(out_dir)
        build_qmd(slides, out_qmd)
        print(f"Rebuilt {out_qmd} with narration for {len(slides)} slides.")
        return 0

    # Scaffold mode: render PNGs, emit empty-notes qmd + stub.
    images = render_pdf_to_pngs(pdf_path, img_dir, args.dpi)
    slides = [{"image": img, "narration": ""} for img in images]
    write_scss(out_dir)
    build_qmd(slides, out_qmd)
    stub_path = out_dir / "narration.stub.json"
    write_stub(slides, stub_path)

    print(f"Rendered {len(images)} pages -> {img_dir}")
    print(f"Wrote {out_qmd} (empty .notes per slide)")
    print(f"Wrote {stub_path}")
    print("Next: view each slide PNG, author narration, then either edit the .qmd "
          "notes or fill the stub and re-run with --narration; then `quarto render`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
