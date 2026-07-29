"""FastAPI app for quick class-participation evaluations."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date as date_cls
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db, picker, roster, storage

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    yield


app = FastAPI(title="Participation", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _course_or_404(course_id: int):
    course = db.get_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _folder_status(folder: str) -> str:
    if not folder.strip():
        return "unset"
    return "ok" if Path(folder).expanduser().is_dir() else "missing"


# --- course picker ---------------------------------------------------------


@app.get("/")
def index(request: Request):
    courses = db.list_courses()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "courses": courses,
            "today": date_cls.today().isoformat(),
        },
    )


# --- evaluation screen -----------------------------------------------------


@app.get("/evaluate/{course_id}")
def evaluate(request: Request, course_id: int, date: str | None = None):
    course = _course_or_404(course_id)
    students = db.list_students(course_id)
    day = date or date_cls.today().isoformat()

    existing: dict[str, dict[str, str]] = {}
    folder_error = ""
    try:
        existing = storage.read_date(course["folder"], day, course["name"])
    except storage.FolderError as exc:
        folder_error = str(exc)

    rows = [
        {
            "id": s["id"],
            "name": s["name"],
            "has_photo": bool(s["photo"]),
            "initials": _initials(s["name"]),
            "amount": existing.get(s["name"], {}).get("amount", ""),
            "quality": existing.get(s["name"], {}).get("quality", ""),
            "notes": existing.get(s["name"], {}).get("notes", ""),
        }
        for s in students
    ]

    return templates.TemplateResponse(
        request,
        "evaluate.html",
        {
            "course": course,
            "students": rows,
            "date": day,
            "today": date_cls.today().isoformat(),
            "folder_error": folder_error,
        },
    )


@app.get("/api/courses/{course_id}/evaluations")
def load_evaluations(course_id: int, date: str):
    course = _course_or_404(course_id)
    try:
        existing = storage.read_date(course["folder"], date, course["name"])
    except storage.FolderError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"date": date, "entries": existing}


@app.post("/api/courses/{course_id}/evaluations")
async def save_evaluations(course_id: int, request: Request):
    course = _course_or_404(course_id)
    payload = await request.json()
    day = str(payload.get("date") or "").strip()
    if not _valid_date(day):
        return JSONResponse({"error": "Pick a valid date before saving."}, status_code=400)

    entries = payload.get("entries") or []
    names = {s["id"]: s["name"] for s in db.list_students(course_id)}
    resolved = [
        {
            "student": names.get(int(e.get("id", 0)), ""),
            "amount": e.get("amount"),
            "quality": e.get("quality"),
            "notes": e.get("notes"),
        }
        for e in entries
        if str(e.get("id", "")).isdigit()
    ]

    try:
        path, count = storage.save_date(course["folder"], course["name"], day, resolved)
    except storage.FolderError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except OSError as exc:
        return JSONResponse({"error": f"Could not write the file: {exc}"}, status_code=500)

    return {"saved": count, "path": str(path), "date": day}


@app.get("/photo/{student_id}")
def photo(student_id: int):
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=404)
    path = db.photo_path(student["photo"])
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/png")


# --- admin -----------------------------------------------------------------


@app.get("/admin")
def admin(request: Request):
    courses = db.list_courses()
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "courses": [
                {**dict(c), "folder_status": _folder_status(c["folder"])} for c in courses
            ],
        },
    )


@app.post("/admin/courses")
def create_course(name: str = Form(...), term: str = Form(""), folder: str = Form("")):
    if not name.strip():
        return RedirectResponse("/admin", status_code=303)
    course_id = db.create_course(name, term, folder)
    return RedirectResponse(f"/admin/courses/{course_id}", status_code=303)


@app.get("/admin/courses/{course_id}")
def edit_course(request: Request, course_id: int):
    course = _course_or_404(course_id)
    students = db.list_students(course_id)
    return templates.TemplateResponse(
        request,
        "course.html",
        {
            "course": course,
            "folder_status": _folder_status(course["folder"]),
            "students": [
                {
                    "id": s["id"],
                    "name": s["name"],
                    "has_photo": bool(s["photo"]),
                    "initials": _initials(s["name"]),
                }
                for s in students
            ],
        },
    )


@app.post("/admin/courses/{course_id}")
def save_course(
    course_id: int,
    name: str = Form(...),
    term: str = Form(""),
    folder: str = Form(""),
):
    _course_or_404(course_id)
    db.update_course(course_id, name, term, folder)
    return RedirectResponse(f"/admin/courses/{course_id}", status_code=303)


@app.post("/admin/courses/{course_id}/delete")
def remove_course(course_id: int):
    _course_or_404(course_id)
    db.delete_course(course_id)
    return RedirectResponse("/admin", status_code=303)


class RosterImportError(Exception):
    """An import that could not proceed, with a message fit to show the user."""


def _import_roster(course_id: int, data: bytes, mode: str) -> tuple[int, int | None]:
    """Replace or extend a course roster from PDF bytes. Returns (imported, expected)."""
    if data[:5] != b"%PDF-":
        raise RosterImportError("That file is not a PDF.")

    try:
        parsed = roster.parse(data)
    except Exception as exc:  # a malformed PDF should not take the app down
        raise RosterImportError(f"Could not read that PDF: {exc}") from exc

    # Validate before touching the existing roster. A class folder holds plenty
    # of other PDFs, and figures in a paper can look enough like headshots to
    # import a handful of nonsense students over a good roster.
    if not parsed.entries:
        raise RosterImportError(
            "No student photos found in that PDF. This needs the Course Roster "
            "report printed from Esther — a photo per row with the name beside "
            "it. Your existing roster has been left alone."
        )
    if parsed.expected is None:
        raise RosterImportError(
            f"That PDF has images but no student-ID column, so it is not a "
            f"Course Roster — it looks like an ordinary document that happens "
            f"to contain {len(parsed.entries)} picture(s). Your existing roster "
            f"has been left alone."
        )

    if mode == "replace":
        db.clear_roster(course_id)

    start = len(db.list_students(course_id))
    for i, entry in enumerate(parsed.entries):
        label = entry.name or f"Unnamed {i + 1}"
        db.add_student(course_id, label, entry.image, start + i)
    db.resequence(course_id)
    return len(parsed.entries), parsed.expected


@app.post("/api/courses")
async def create_course_api(request: Request):
    """Create a course. Lets the skill set one up from the class folder directly."""
    payload = await request.json()
    name = str(payload.get("name") or "").strip()
    if not name:
        return JSONResponse({"error": "A course needs a name."}, status_code=400)
    course_id = db.create_course(name, str(payload.get("term") or ""),
                                 str(payload.get("folder") or ""))
    return {"id": course_id, "name": name}


@app.get("/api/courses/{course_id}/roster")
def read_roster(course_id: int):
    _course_or_404(course_id)
    return {
        "students": [
            {"id": s["id"], "name": s["name"], "has_photo": bool(s["photo"])}
            for s in db.list_students(course_id)
        ]
    }


@app.post("/api/courses/{course_id}/photos")
async def attach_photos(course_id: int, request: Request):
    """Attach photo files to students by name, for a folder of image files.

    Matching is on the name as stored, case- and spacing-insensitive. Anything
    that doesn't match is reported back rather than guessed at.
    """
    _course_or_404(course_id)
    payload = await request.json()

    def key(value: str) -> str:
        return " ".join(str(value).split()).lower()

    by_name = {key(s["name"]): s["id"] for s in db.list_students(course_id)}
    attached, unmatched, unreadable = [], [], []

    for item in payload.get("photos") or []:
        name = str(item.get("name") or "")
        student_id = by_name.get(key(name))
        if student_id is None:
            unmatched.append(name)
            continue
        path = Path(str(item.get("path") or "")).expanduser()
        try:
            db.set_student_photo(student_id, course_id, path.read_bytes())
        except OSError as exc:
            unreadable.append(f"{name}: {exc}")
            continue
        attached.append(name)

    return {"attached": len(attached), "unmatched": unmatched, "unreadable": unreadable}


@app.post("/api/courses/{course_id}/roster/names")
async def set_roster_names(course_id: int, request: Request):
    """Set the roster from a list of names.

    The general case: a class list can be a spreadsheet, a text file, an email,
    anything. Rather than teach the app every format, Claude reads whatever the
    instructor has and posts the names here. Photos are optional and can be
    attached per student afterwards.
    """
    _course_or_404(course_id)
    payload = await request.json()

    names, seen = [], set()
    for raw in payload.get("names") or []:
        name = " ".join(str(raw).split())
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)

    if not names:
        return JSONResponse({"error": "No names given."}, status_code=400)

    if str(payload.get("mode") or "replace") == "replace":
        db.clear_roster(course_id)

    start = len(db.list_students(course_id))
    for i, name in enumerate(names):
        db.add_student(course_id, name, None, start + i)
    db.resequence(course_id)

    return {"imported": len(names), "total": len(db.list_students(course_id))}


@app.post("/api/courses/{course_id}/roster/from-path")
async def import_roster_from_path(course_id: int, request: Request):
    """Import the roster from a PDF already sitting in the class folder."""
    _course_or_404(course_id)
    payload = await request.json()
    raw = str(payload.get("path") or "").strip()
    if not raw:
        return JSONResponse({"error": "No path given."}, status_code=400)

    path = Path(raw).expanduser()
    if not path.is_file():
        return JSONResponse({"error": f"File not found: {path}"}, status_code=400)

    try:
        imported, expected = _import_roster(
            course_id, path.read_bytes(), str(payload.get("mode") or "replace")
        )
    except RosterImportError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except OSError as exc:
        return JSONResponse({"error": f"Could not read {path}: {exc}"}, status_code=400)

    return {"imported": imported, "expected": expected, "path": str(path)}


@app.post("/admin/courses/{course_id}/students")
async def update_roster(course_id: int, request: Request):
    _course_or_404(course_id)
    payload = await request.json()

    for sid in payload.get("delete", []):
        student = db.get_student(int(sid))
        if student is not None and student["course_id"] == course_id:
            db.delete_student(int(sid))

    for item in payload.get("students", []):
        student = db.get_student(int(item["id"]))
        if student is not None and student["course_id"] == course_id:
            db.rename_student(int(item["id"]), str(item.get("name", "")))

    db.resequence(course_id)
    return {"ok": True, "count": len(db.list_students(course_id))}


@app.post("/admin/courses/{course_id}/students/add")
async def add_student(course_id: int, name: str = Form(...), photo: UploadFile | None = None):
    _course_or_404(course_id)
    image = await photo.read() if photo is not None and photo.filename else None
    order = len(db.list_students(course_id))
    db.add_student(course_id, name, image, order)
    db.resequence(course_id)
    return RedirectResponse(f"/admin/courses/{course_id}", status_code=303)


@app.post("/admin/courses/{course_id}/students/{student_id}/photo")
async def replace_photo(course_id: int, student_id: int, photo: UploadFile):
    student = db.get_student(student_id)
    if student is None or student["course_id"] != course_id:
        raise HTTPException(status_code=404)
    db.set_student_photo(student_id, course_id, await photo.read())
    return {"ok": True}


@app.post("/api/browse-folder")
def browse_folder():
    """Open the OS folder chooser on the machine running the app."""
    try:
        chosen = picker.choose_folder()
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)
    if not chosen:
        return {"cancelled": True}
    return {"folder": chosen}


# --- helpers ---------------------------------------------------------------


def _initials(name: str) -> str:
    parts = [p for p in name.replace(",", " ").split() if p[:1].isalpha()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _valid_date(value: str) -> bool:
    try:
        date_cls.fromisoformat(value)
    except ValueError:
        return False
    return True
