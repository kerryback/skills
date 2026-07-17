"""Upload conversion: render an uploaded PDF deck into an image-per-slide
Quarto reveal deck (+ slide PNGs) plus an initial narration scaffold.

Only PDF decks are accepted. PowerPoint and reveal/Quarto inputs were dropped:
LibreOffice could not faithfully render PowerPoint (image-cropped table cells,
animation builds), and PowerPoint's own "Export to PDF" produces a
pixel-faithful, fully-built PDF. Teachers export to PDF and upload that.

Reuses the vendored PDF converter in backend/converters/.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# backend/ is on sys.path when the app runs; make imports robust regardless.
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from converters import pdf_to_revealjs as pdfconv  # noqa: E402

from . import config  # noqa: E402

PDF_EXTS = {".pdf"}
PPTX_EXTS = {".pptx", ".ppt"}

PPTX_MESSAGE = (
    "PowerPoint files aren't supported directly. In PowerPoint, choose "
    "File ▸ Export ▸ Create PDF/XPS (or Save As ▸ PDF), then "
    "upload the PDF."
)


def detect_source_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in PDF_EXTS:
        return "pdf"
    if ext in PPTX_EXTS:
        raise ValueError(PPTX_MESSAGE)
    raise ValueError("Only PDF slide decks are supported — please upload a .pdf file.")


def _copy_slide_images(deck_dir: Path, slides_dir: Path) -> None:
    slides_dir.mkdir(parents=True, exist_ok=True)
    img_dir = deck_dir / "images"
    if not img_dir.exists():
        return
    for png in sorted(img_dir.glob("slide-*.png")):
        shutil.copyfile(png, slides_dir / png.name)


def _deck_name(source_path: Path) -> str:
    # Sanitize to a safe qmd/html basename.
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", source_path.stem).strip("-") or "deck"
    return stem


def _extract_pdf_text(source_path: Path, n: int) -> list:
    """Per-page {title, slide_text} from the PDF, so Claude Code can draft narration
    from lightweight text instead of rendering every page as an image (which is slow
    and token-heavy for a big deck). Pages with no extractable text — e.g. scanned or
    all-graphic slides — come back empty, and the agent falls back to the page image
    for just those slides."""
    try:
        import fitz  # PyMuPDF
    except Exception:  # pragma: no cover - dependency guaranteed at runtime
        try:
            import pymupdf as fitz
        except Exception:
            return [{"title": "", "slide_text": ""} for _ in range(n)]
    out = []
    try:
        with fitz.open(source_path) as doc:
            for page in doc:
                raw = page.get_text("text") or ""
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                title = lines[0][:80] if lines else ""
                text = re.sub(r"\s+", " ", raw).strip()
                out.append({"title": title, "slide_text": text})
    except Exception:
        return [{"title": "", "slide_text": ""} for _ in range(n)]
    if len(out) < n:
        out += [{"title": "", "slide_text": ""} for _ in range(n - len(out))]
    return out[:n]


def convert(project_id: str, source_path: Path, source_type: str) -> dict:
    """Run conversion; return {"deck_name", "slides":[...]}.

    slides entries: {index, title, slide_text, narration} (narration empty; it
    is drafted later by the narration agent).
    """
    pdir = config.project_dir(project_id)
    deck_dir = pdir / "deck"
    slides_dir = pdir / "slides"
    deck_dir.mkdir(parents=True, exist_ok=True)
    name = _deck_name(source_path)
    out_qmd = deck_dir / f"{name}.qmd"

    if source_type == "pdf":
        images = pdfconv.render_pdf_to_pngs(source_path, deck_dir / "images", dpi=150)
        deck_slides = [{"image": img, "narration": ""} for img in images]
        pdfconv.write_scss(deck_dir)
        pdfconv.build_qmd(deck_slides, out_qmd)
        _copy_slide_images(deck_dir, slides_dir)
        text = _extract_pdf_text(source_path, len(images))
        slides = [{"index": i, "title": text[i]["title"],
                   "slide_text": text[i]["slide_text"], "narration": ""}
                  for i in range(len(images))]
        return {"deck_name": name, "slides": slides}

    raise ValueError(f"Unknown source_type: {source_type}")


def render_qmd(qmd_path: Path) -> Path:
    """quarto render a .qmd to reveal HTML. Returns the .html path."""
    subprocess.run(
        ["quarto", "render", qmd_path.name, "--to", "revealjs"],
        cwd=str(qmd_path.parent), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    html_path = qmd_path.with_suffix(".html")
    if not html_path.exists():
        raise RuntimeError(f"quarto render did not produce {html_path}")
    return html_path


_NOTES_BLOCK = re.compile(r"(::: \{\.notes\}\n)(.*?)(\n:::)", re.DOTALL)


def inject_narration_into_qmd(qmd_path: Path, narrations: list) -> None:
    """Replace the content of each `::: {.notes}` block in order with the
    corresponding narration text. Works for image decks (converter-generated)
    and reveal qmds that carry notes blocks."""
    text = qmd_path.read_text(encoding="utf-8")
    idx = {"i": 0}

    def repl(m):
        i = idx["i"]
        idx["i"] += 1
        narration = (narrations[i] if i < len(narrations) else "").strip()
        return m.group(1) + narration + m.group(3)

    new_text = _NOTES_BLOCK.sub(repl, text)
    qmd_path.write_text(new_text, encoding="utf-8")
