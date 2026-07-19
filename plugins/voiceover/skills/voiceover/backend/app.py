"""Voiceover Builder — FastAPI backend. Implements CONTRACT.md."""
import asyncio
import json
import re
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from builderlib import config, convert, db, events, jobs, store

db.init()

# No auth: this runs locally as a skill, launched per-file by the instructor.
# (If it later becomes a deployable multi-user app, reintroduce a login gate.)
app = FastAPI(title="Voiceover Builder")


# --------------------------------------------------------------------------- #
# Projects
# --------------------------------------------------------------------------- #
def _project_summary(p: dict) -> dict:
    return {
        "id": p["id"], "name": p["name"], "state": p["state"],
        "source_type": p["source_type"], "stale": p["stale"],
        "deploy": {"url": p.get("deploy", {}).get("url", "")},
        "updated_at": p["updated_at"],
    }


@app.get("/api/projects")
async def list_projects():
    return [_project_summary(p) for p in db.list_projects()]


def _start_project(filename: str, name: str, data: bytes) -> dict:
    """Create (or reopen) a deck from raw bytes and kick off conversion. Shared by
    the multipart upload and the skill launcher's from-path call.

    A deck's identity is its name: the project id is a filesystem-safe slug of the
    deck's filename stem, and its folder (config.project_dir) is named the same.
    Launching the same deck again reopens that folder — conversion preserves any
    existing narration slide-by-slide (see jobs._convert), so an edited deck keeps
    its script and the video can be regenerated."""
    try:
        source_type = convert.detect_source_type(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    ext = Path(filename).suffix.lower()
    stem = Path(filename or "deck").stem
    pid = _deck_slug(stem)
    pdir = config.project_dir(pid)
    pdir.mkdir(parents=True, exist_ok=True)
    source_path = pdir / f"{pid}{ext}"
    source_path.write_bytes(data)
    proj = db.get_project(pid)
    if proj is None:
        proj = db.create_project(pid, name or stem, source_type, "uploaded")
    jobs.start_conversion(pid, source_path, source_type)
    return _project_summary(proj)


def _deck_slug(name: str) -> str:
    """Filesystem-safe, human-readable deck id/folder name from a deck filename."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", (name or "deck")).strip("-.") or "deck"


@app.post("/api/projects")
async def create_project(file: UploadFile = File(...), name: str = Form(...)):
    return _start_project(file.filename or "deck.pdf", name, await file.read())


class FromPathBody(BaseModel):
    path: str
    name: str | None = None


@app.post("/api/projects/from-path")
async def create_project_from_path(body: FromPathBody):
    """Create a project from a file already on disk. The skill launcher uses this
    so the instructor never uploads through the browser."""
    src = Path(body.path).expanduser()
    if not src.is_file():
        raise HTTPException(400, f"file not found: {src}")
    return _start_project(src.name, body.name or src.stem, src.read_bytes())


@app.get("/api/projects/{pid}")
async def get_project(pid: str):
    proj = db.get_project(pid)
    if not proj:
        raise HTTPException(404, "not found")
    narration = store.read_narration(pid)
    slides = []
    for s in narration.get("slides", []):
        i = s["index"]
        png = store.slides_dir(pid) / f"slide-{i + 1:03d}.png"
        slides.append({
            "index": i,
            "title": s.get("title", ""),
            "narration": s.get("narration", ""),
            "image_url": f"api/projects/{pid}/slides/slide-{i + 1:03d}.png" if png.exists() else None,
        })
    return {
        "id": proj["id"], "name": proj["name"], "state": proj["state"],
        "source_type": proj["source_type"], "stale": proj["stale"],
        "slides": slides, "config": store.read_config(pid),
        "deploy": proj.get("deploy", {}), "log": proj.get("log", ""),
    }


@app.get("/api/projects/{pid}/narration")
async def get_narration(pid: str):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    return store.read_narration(pid)


class NarrationBody(BaseModel):
    narration: str


@app.put("/api/projects/{pid}/narration/{index}")
async def put_narration(pid: str, index: int, body: NarrationBody):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    data = store.read_narration(pid)
    found = False
    for s in data.get("slides", []):
        if s["index"] == index:
            s["narration"] = body.narration
            found = True
            break
    if not found:
        raise HTTPException(404, "slide not found")
    store.write_narration(pid, data)
    store.touch_stale(pid)
    return {"ok": True}


class NarrationItem(BaseModel):
    index: int
    narration: str


class NarrationBulkBody(BaseModel):
    slides: list[NarrationItem]


@app.put("/api/projects/{pid}/narration")
async def put_narration_bulk(pid: str, body: NarrationBulkBody):
    """Set narration for many slides at once. The Claude Code agent uses this to
    write a full first draft (and multi-slide revisions) in a single call."""
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    data = store.read_narration(pid)
    by_index = {s["index"]: s for s in data.get("slides", [])}
    updated = 0
    unknown = []
    for item in body.slides:
        s = by_index.get(item.index)
        if s is None:
            unknown.append(item.index)
            continue
        s["narration"] = item.narration
        updated += 1
    if unknown:
        raise HTTPException(404, f"unknown slide index(es): {unknown}")
    store.write_narration(pid, data)
    store.touch_stale(pid)
    return {"ok": True, "updated": updated}


class ConfigBody(BaseModel):
    voice_id: str | None = None
    model: str | None = None
    stability: float | None = None
    similarity_boost: float | None = None


@app.put("/api/projects/{pid}/config")
async def put_config(pid: str, body: ConfigBody):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    merged = store.write_config(pid, body.model_dump())
    store.touch_stale(pid)
    return {"ok": True, "config": merged}


@app.get("/api/tts/status")
async def tts_status():
    """Whether an ElevenLabs key is configured. Cheap (no network call) so the
    app-wide key banner can poll it without hitting ElevenLabs."""
    return {"configured": bool(config.ELEVENLABS_API_KEY)}


class KeyBody(BaseModel):
    api_key: str


@app.post("/api/tts/key")
async def set_tts_key(body: KeyBody):
    """Validate an ElevenLabs key against the API and, if good, persist it to
    backend/.env and load it live — so the instructor never edits a file."""
    key = (body.api_key or "").strip()
    if not key:
        raise HTTPException(400, "Enter your ElevenLabs API key.")
    import httpx
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get("https://api.elevenlabs.io/v1/user",
                                  headers={"xi-api-key": key})
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Could not reach ElevenLabs: {e}")
    if r.status_code in (401, 403):
        raise HTTPException(400, "ElevenLabs rejected that key. Check it and try again.")
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs error ({r.status_code}).")
    config.set_elevenlabs_key(key)
    return {"configured": True}


@app.get("/api/tts/voices")
async def tts_voices():
    """List the account's ElevenLabs voices (including cloned voices) for the
    voice picker. Returns configured=False when no key is set so the UI can
    prompt for one instead of erroring."""
    if not config.ELEVENLABS_API_KEY:
        return {"configured": False, "voices": []}
    import httpx
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get("https://api.elevenlabs.io/v1/voices",
                             headers={"xi-api-key": config.ELEVENLABS_API_KEY})
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs voices error ({r.status_code})")
    voices = [{"voice_id": v["voice_id"], "name": v.get("name", ""),
               "category": v.get("category", "")}
              for v in r.json().get("voices", [])]
    return {"configured": True, "voices": voices}


@app.post("/api/projects/{pid}/build", status_code=202)
async def build(pid: str):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    jobs.start_build(pid)
    return {"started": True}


@app.get("/api/projects/{pid}/events")
async def project_events(pid: str, request: Request):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")

    async def gen():
        since = 0
        idle = 0
        while True:
            if await request.is_disconnected():
                break
            new, since, active = events.snapshot(pid, since)
            for evt in new:
                yield f"data: {json.dumps(evt)}\n\n"
            if not new:
                idle += 1
            else:
                idle = 0
            if not active and not new:
                yield "event: done\ndata: {}\n\n"
                break
            if idle > 600:  # ~5 min with no activity
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/projects/{pid}/slides/{fname}")
async def slide_image(pid: str, fname: str):
    if "/" in fname or ".." in fname:
        raise HTTPException(400, "bad name")
    path = store.slides_dir(pid) / fname
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(path)


# --------------------------------------------------------------------------- #
# Rendered video — in-app preview only. The finished MP4 + transcript are written
# to the instructor's working directory at build time (see jobs._build); there is
# no in-app download.
# --------------------------------------------------------------------------- #
@app.get("/api/projects/{pid}/video")
async def project_video(pid: str):
    proj = db.get_project(pid)
    if not proj:
        raise HTTPException(404, "not found")
    path = store.video_path(pid)
    if not path.exists():
        raise HTTPException(404, "not built yet")
    # Served inline so the Preview step's <video> can stream/seek it (Range-aware).
    return FileResponse(path, media_type="video/mp4")


# --------------------------------------------------------------------------- #
# SPA (optional) — mounted last so API routes win.
# --------------------------------------------------------------------------- #
if config.FRONTEND_DIST.exists():
    class SPAStatic(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            if resp.status_code == 404:
                return await super().get_response("index.html", scope)
            return resp

    app.mount("/", SPAStatic(directory=str(config.FRONTEND_DIST), html=True), name="spa")
else:
    @app.get("/")
    async def root():
        return {"app": "Voiceover Builder", "frontend": "not built (frontend/dist missing)"}
