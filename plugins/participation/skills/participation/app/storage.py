"""Read and write the participation CSV that lives in the instructor's folder.

One cumulative file per course folder, `participation.csv`, so a term's
evaluations open directly in Excel without any merging. Saving a date replaces
every row previously recorded for that date, which makes re-opening a class and
correcting a score safe.
"""

from __future__ import annotations

import csv
import os
import tempfile
from datetime import datetime
from pathlib import Path

FILENAME = "participation.csv"
FIELDS = ["date", "course", "student", "amount", "quality", "notes", "recorded_at"]


class FolderError(Exception):
    """The course folder is unset or unusable."""


def csv_path(folder: str) -> Path:
    if not folder or not folder.strip():
        raise FolderError("This course has no folder set. Add one in the admin panel.")
    path = Path(folder).expanduser()
    if not path.is_dir():
        raise FolderError(f"Folder not found: {path}")
    return path / FILENAME


def read_all(folder: str) -> list[dict[str, str]]:
    path = csv_path(folder)
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return [{k: (row.get(k) or "") for k in FIELDS} for row in csv.DictReader(fh)]


def read_date(folder: str, date: str, course: str) -> dict[str, dict[str, str]]:
    """Existing scores for one class meeting, keyed by student name."""
    out: dict[str, dict[str, str]] = {}
    for row in read_all(folder):
        if row["date"] == date and row["course"] == course:
            out[row["student"]] = {
                "amount": row["amount"],
                "quality": row["quality"],
                "notes": row["notes"],
            }
    return out


def save_date(folder: str, course: str, date: str, entries: list[dict]) -> tuple[Path, int]:
    """Replace this course's rows for `date` with `entries`. Returns (path, count)."""
    path = csv_path(folder)
    stamp = datetime.now().isoformat(timespec="seconds")

    kept = [
        row
        for row in read_all(folder)
        if not (row["date"] == date and row["course"] == course)
    ]
    fresh = [
        {
            "date": date,
            "course": course,
            "student": str(e.get("student", "")).strip(),
            "amount": _score(e.get("amount")),
            "quality": _score(e.get("quality")),
            "notes": str(e.get("notes") or "").strip(),
            "recorded_at": stamp,
        }
        for e in entries
    ]
    # Every student on the roster gets a row for every class meeting, so the
    # file is a complete grid: an unscored student is a recorded zero, not a
    # gap to be interpreted later.
    fresh = [r for r in fresh if r["student"]]

    rows = sorted(kept + fresh, key=lambda r: (r["date"], r["course"], r["student"].lower()))
    _write_atomic(path, rows)
    return path, len(fresh)


def _score(value) -> str:
    """1-3 as given; anything left unscored records as 0."""
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return "0"
    return str(n) if 1 <= n <= 3 else "0"


def _write_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".participation-", suffix=".csv")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
