"""Load a deck: speaker notes from the source file, slide images from the PDF.

A deck is a pair of files that live in the instructor's own folder — the deck
they wrote (`.qmd` or `.pptx`) and the PDF they exported from it. Neither is
copied into the app; the deck folder stores only paths, rendered page images and
generated audio, so re-reading picks up whatever is on disk now.

The pairing is checked, not assumed: if the source says 24 slides and the PDF
has 31 pages, every slide after the first divergence would narrate the wrong
picture. That is a refusal with a message, not a warning.
"""
import re
from pathlib import Path

from . import sources

DPI = 150


def resolve_pdf(source_path: Path) -> Path:
    """The PDF that goes with a deck: same folder, same stem, `.pdf`."""
    return Path(source_path).with_suffix(".pdf")


def deck_slug(name: str) -> str:
    """Filesystem-safe, human-readable deck id/folder name from a filename."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "deck")).strip("-.") or "deck"


def page_count(pdf_path: Path) -> int:
    fitz = _fitz()
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def render_pdf(pdf_path: Path, out_dir: Path, progress=None) -> int:
    """Render every PDF page to `slide-NNN.png` (1-based). Returns the count.

    Stale PNGs from a previous, longer deck are removed, so a deck that lost
    slides doesn't leave orphans for the video renderer to find.
    """
    fitz = _fitz()
    out_dir.mkdir(parents=True, exist_ok=True)
    zoom = DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    with fitz.open(pdf_path) as doc:
        total = doc.page_count
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=matrix)
            pix.save(out_dir / f"slide-{i + 1:03d}.png")
            if progress:
                progress(i + 1, total, "Rendering slides")
    for png in out_dir.glob("slide-*.png"):
        try:
            if int(png.stem.split("-")[1]) > total:
                png.unlink()
        except (IndexError, ValueError):
            continue
    return total


def _fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        import pymupdf
        return pymupdf


def load(source_path: Path, pdf_path: Path, slides_dir: Path,
         progress=None) -> dict:
    """Read notes from the source, render the PDF, and check they agree.

    Returns {"slides", "source_type", "pages"}. Raises ValueError with a
    diagnosis when the two files describe different decks.
    """
    source_path = Path(source_path)
    pdf_path = Path(pdf_path)
    if not source_path.is_file():
        raise ValueError(f"Deck source not found: {source_path}")
    if not pdf_path.is_file():
        raise ValueError(
            f"No PDF found at {pdf_path}. Export {source_path.name} to PDF and "
            "save it next to the deck with the same name.")

    source_type = sources.detect(source_path)
    slides = sources.read_slides(source_path)
    pages = render_pdf(pdf_path, slides_dir, progress=progress)

    if len(slides) != pages:
        raise ValueError(_mismatch_message(source_path, pdf_path, source_type,
                                           len(slides), pages))
    return {"slides": slides, "source_type": source_type, "pages": pages}


def _mismatch_message(source_path: Path, pdf_path: Path, source_type: str,
                      n_slides: int, n_pages: int) -> str:
    """Say which file claims what, and name the usual cause — the count alone
    doesn't tell anyone what to go fix."""
    head = (f"{source_path.name} has {n_slides} slide"
            f"{'' if n_slides == 1 else 's'} but {pdf_path.name} has {n_pages} "
            f"page{'' if n_pages == 1 else 's'}, so notes and slides can't be "
            "lined up.")
    if source_type == "qmd" and n_pages > n_slides:
        return (head + " A reveal deck exports one page per fragment step unless "
                "`pdf-separate-fragments: false` is set under `format: revealjs:` "
                "— that is the usual cause when the PDF has more pages. Otherwise "
                "re-export the PDF from the current deck.")
    if source_type == "pptx" and n_pages < n_slides:
        hidden = sources.count_hidden_pptx(source_path)
        if hidden:
            return (head + f" The deck has {hidden} hidden slide"
                    f"{'' if hidden == 1 else 's'}, which PowerPoint leaves out "
                    "of an exported PDF — unhide them or delete them.")
    return head + " Re-export the PDF from the current deck and reload."
