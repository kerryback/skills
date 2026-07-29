"""SQLite storage for courses and rosters.

Evaluation data itself does *not* live here -- it is written to a CSV in the
instructor's course folder (see storage.py). This database only holds the
things the app needs to show the evaluation screen: courses, their folders,
and the students extracted from the roster PDF.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def _data_dir() -> Path:
    """Where courses, rosters and photos live.

    Deliberately outside the installed skill: a plugin update replaces the skill
    directory, and an instructor's rosters must survive that. Override with
    PARTICIPATION_DATA_DIR.
    """
    override = os.environ.get("PARTICIPATION_DATA_DIR")
    if override:
        return Path(override).expanduser()
    home = os.environ.get("PARTICIPATION_HOME")
    root = Path(home).expanduser() if home else Path.home() / ".participation"
    return root / "data"


DATA_DIR = _data_dir()
PHOTO_DIR = DATA_DIR / "photos"
DB_PATH = DATA_DIR / "participation.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    term        TEXT NOT NULL DEFAULT '',
    folder      TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    photo       TEXT NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS students_course ON students(course_id);
"""


def init() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.executescript(SCHEMA)


@contextmanager
def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


# --- courses ---------------------------------------------------------------


def list_courses() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute(
            """SELECT c.*, (SELECT COUNT(*) FROM students s WHERE s.course_id = c.id)
                      AS student_count
               FROM courses c ORDER BY c.name COLLATE NOCASE"""
        ).fetchall()


def get_course(course_id: int) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()


def create_course(name: str, term: str, folder: str) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO courses (name, term, folder) VALUES (?, ?, ?)",
            (name.strip(), term.strip(), folder.strip()),
        )
        return int(cur.lastrowid)


def update_course(course_id: int, name: str, term: str, folder: str) -> None:
    with connect() as con:
        con.execute(
            "UPDATE courses SET name = ?, term = ?, folder = ? WHERE id = ?",
            (name.strip(), term.strip(), folder.strip(), course_id),
        )


def delete_course(course_id: int) -> None:
    for row in list_students(course_id):
        _unlink_photo(row["photo"])
    with connect() as con:
        con.execute("DELETE FROM students WHERE course_id = ?", (course_id,))
        con.execute("DELETE FROM courses WHERE id = ?", (course_id,))


# --- students --------------------------------------------------------------


def list_students(course_id: int) -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute(
            "SELECT * FROM students WHERE course_id = ? ORDER BY sort_order, id",
            (course_id,),
        ).fetchall()


def get_student(student_id: int) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def add_student(course_id: int, name: str, photo_bytes: bytes | None, sort_order: int) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO students (course_id, name, photo, sort_order) VALUES (?, ?, '', ?)",
            (course_id, name.strip(), sort_order),
        )
        student_id = int(cur.lastrowid)
    if photo_bytes:
        rel = _write_photo(course_id, student_id, photo_bytes)
        with connect() as con:
            con.execute("UPDATE students SET photo = ? WHERE id = ?", (rel, student_id))
    return student_id


def rename_student(student_id: int, name: str) -> None:
    with connect() as con:
        con.execute("UPDATE students SET name = ? WHERE id = ?", (name.strip(), student_id))


def set_student_photo(student_id: int, course_id: int, photo_bytes: bytes) -> None:
    row = get_student(student_id)
    if row is not None:
        _unlink_photo(row["photo"])
    rel = _write_photo(course_id, student_id, photo_bytes)
    with connect() as con:
        con.execute("UPDATE students SET photo = ? WHERE id = ?", (rel, student_id))


def delete_student(student_id: int) -> None:
    row = get_student(student_id)
    if row is None:
        return
    _unlink_photo(row["photo"])
    with connect() as con:
        con.execute("DELETE FROM students WHERE id = ?", (student_id,))


def clear_roster(course_id: int) -> None:
    for row in list_students(course_id):
        _unlink_photo(row["photo"])
    with connect() as con:
        con.execute("DELETE FROM students WHERE course_id = ?", (course_id,))


def resequence(course_id: int) -> None:
    """Renumber sort_order by current name order."""
    rows = list_students(course_id)
    ordered = sorted(rows, key=lambda r: _sort_key(r["name"]))
    with connect() as con:
        for i, row in enumerate(ordered):
            con.execute("UPDATE students SET sort_order = ? WHERE id = ?", (i, row["id"]))


def _sort_key(name: str) -> tuple[str, str]:
    parts = name.replace(",", " ").split()
    if not parts:
        return ("", "")
    return (parts[-1].lower(), parts[0].lower())


# --- photo files -----------------------------------------------------------


def photo_path(rel: str) -> Path | None:
    if not rel:
        return None
    path = PHOTO_DIR / rel
    return path if path.is_file() else None


def _write_photo(course_id: int, student_id: int, data: bytes) -> str:
    folder = PHOTO_DIR / str(course_id)
    folder.mkdir(parents=True, exist_ok=True)
    rel = f"{course_id}/{student_id}.png"
    (PHOTO_DIR / rel).write_bytes(data)
    return rel


def _unlink_photo(rel: str) -> None:
    path = photo_path(rel)
    if path is not None:
        path.unlink(missing_ok=True)
