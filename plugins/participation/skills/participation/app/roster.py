"""Read a Banner "Course Roster" PDF.

The format is fixed, so this reader targets it directly rather than guessing at
a layout. One student per table row:

    [thumbnail]  Last, First   S01234567 MGMT 638   1.5  GR  ...
                 ^ leftmost     ^ next column, and everything further right is
                   column         ID, section, credits, level, term, major

The name sits in the column immediately right of the thumbnail, vertically
centred on it, and wraps onto a second line when it is long ("Mohammed," then
"Ryan"). Geometry is measured relative to each thumbnail rather than against
fixed page coordinates, so the reader survives a roster that is shifted or
scaled but still assumes this table shape.

Extraction is still checked, not trusted: the admin screen shows every name for
review, and `Roster.expected` reports the student count read off the ID column
so a mismatch can be flagged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

# Thumbnails are small and square-ish, in the leftmost column of the table.
THUMB_MIN_PT = 20.0
THUMB_MAX_PT = 110.0
THUMB_MAX_ASPECT = 1.35
PHOTO_COLUMN_FRACTION = 0.3

# The name column starts just right of the thumbnail. Lines sharing a left edge
# within COLUMN_TOL_PT are the same column, i.e. a name wrapped onto two lines.
NAME_GAP_PT = 60.0
COLUMN_TOL_PT = 6.0
BAND_PAD_PT = 2.0
MAX_NAME_LINES = 3

# The ID column, used only as a count check against the photos we found.
STUDENT_ID = re.compile(r"\bS\d{7,9}\b")

_JUNK = re.compile(r"^(\d[\d\s\-/]*|.*@.*|[^\w]+)$")


@dataclass
class RosterEntry:
    name: str
    image: bytes | None
    page: int
    row: int


@dataclass
class Roster:
    entries: list[RosterEntry] = field(default_factory=list)
    expected: int | None = None  # distinct student IDs printed in the PDF


def parse(pdf_bytes: bytes) -> Roster:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    entries: list[RosterEntry] = []
    ids: set[str] = set()
    try:
        for page_no in range(doc.page_count):
            page = doc.load_page(page_no)
            entries.extend(_parse_page(doc, page, page_no))
            ids.update(STUDENT_ID.findall(page.get_text()))
    finally:
        doc.close()
    return Roster(entries=entries, expected=len(ids) or None)


def _parse_page(doc: fitz.Document, page: fitz.Page, page_no: int) -> list[RosterEntry]:
    lines = _text_lines(page)
    thumbs = _thumbnails(page)

    return [
        RosterEntry(
            name=_name_beside(rect, lines),
            image=_render(doc, xref),
            page=page_no,
            row=int(rect.y0),
        )
        for rect, xref in thumbs
    ]


def _thumbnails(page: fitz.Page) -> list[tuple[fitz.Rect, int]]:
    """Student photos, top to bottom, one per table row."""
    limit = page.rect.x0 + page.rect.width * PHOTO_COLUMN_FRACTION
    found: list[tuple[fitz.Rect, int]] = []

    for info in page.get_images(full=True):
        xref = info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            continue
        for raw in rects:
            rect = fitz.Rect(raw)
            if rect.x0 > limit:
                continue  # not in the photo column
            if not THUMB_MIN_PT <= rect.height <= THUMB_MAX_PT:
                continue
            if not THUMB_MIN_PT <= rect.width <= THUMB_MAX_PT:
                continue
            if rect.width > rect.height * THUMB_MAX_ASPECT:
                continue  # the page banner, not a headshot
            found.append((rect, xref))

    found.sort(key=lambda pair: (pair[0].y0, pair[0].x0))
    return _dedupe(found)


def _dedupe(thumbs: list[tuple[fitz.Rect, int]]) -> list[tuple[fitz.Rect, int]]:
    """Collapse images stacked on one spot into a single student.

    The "no photo available" placeholder is stored under more than one xref, and
    each copy reports every slot it fills, so one photoless student would
    otherwise appear several times.
    """
    kept: list[tuple[fitz.Rect, int]] = []
    for rect, xref in thumbs:
        if not any(_same_spot(rect, seen) for seen, _ in kept):
            kept.append((rect, xref))
    return kept


def _same_spot(a: fitz.Rect, b: fitz.Rect, tol: float = 3.0) -> bool:
    return (
        abs(a.x0 - b.x0) <= tol
        and abs(a.y0 - b.y0) <= tol
        and abs(a.x1 - b.x1) <= tol
        and abs(a.y1 - b.y1) <= tol
    )


def _name_beside(rect: fitz.Rect, lines: list[tuple[fitz.Rect, str]]) -> str:
    """The name column entry for the row this thumbnail sits in."""
    lo, hi = rect.y0 - BAND_PAD_PT, rect.y1 + BAND_PAD_PT

    candidates = []
    for lrect, text in lines:
        mid_y = (lrect.y0 + lrect.y1) / 2
        if not lo <= mid_y <= hi:
            continue  # a different table row
        if not rect.x1 - 2 <= lrect.x0 <= rect.x1 + NAME_GAP_PT:
            continue  # left of the photo, or a column further right
        if _JUNK.match(text):
            continue
        candidates.append((lrect.x0, mid_y, text))

    if not candidates:
        return ""

    # Everything right of the name column is ID, section, credits and so on.
    column_x = min(c[0] for c in candidates)
    column = [c for c in candidates if c[0] - column_x <= COLUMN_TOL_PT]
    column.sort(key=lambda c: c[1])

    return _clean(" ".join(c[2] for c in column[:MAX_NAME_LINES]))


def _text_lines(page: fitz.Page) -> list[tuple[fitz.Rect, str]]:
    lines: list[tuple[fitz.Rect, str]] = []
    for block in page.get_text("dict").get("blocks", []):
        for line in block.get("lines", []):
            text = "".join(span.get("text", "") for span in line.get("spans", []))
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                lines.append((fitz.Rect(line["bbox"]), text))
    return lines


def _render(doc: fitz.Document, xref: int) -> bytes | None:
    """The embedded thumbnail as PNG bytes, flattening CMYK and alpha."""
    try:
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:  # CMYK
            pix = fitz.Pixmap(fitz.csRGB, pix)
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)
        return pix.tobytes("png")
    except Exception:
        return None


def _clean(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip(" ,.-–—")
    # The roster prints "Mohammed, Ryan"; show it the way you would say it.
    if "," in name:
        last, _, first = name.partition(",")
        if last.strip() and first.strip():
            name = f"{first.strip()} {last.strip()}"
    return name
