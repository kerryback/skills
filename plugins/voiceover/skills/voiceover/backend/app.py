"""Voiceover Builder — FastAPI backend. Implements CONTRACT.md."""
import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from builderlib import config, db, deck, events, jobs, sources, store

db.init()

# No auth: this runs locally as a skill, launched per-deck by the instructor.
app = FastAPI(title="Voiceover Builder")


# --------------------------------------------------------------------------- #
# Decks
# --------------------------------------------------------------------------- #
def _summary(p: dict) -> dict:
    return {
        "id": p["id"], "name": p["name"], "state": p["state"],
        "source_type": p["source_type"], "stale": store.is_stale(p["id"]),
        "files": store.file_status(p["id"]),
        "updated_at": p["updated_at"],
    }


@app.get("/api/projects")
async def list_projects():
    return [_summary(p) for p in db.list_projects()]


class OpenBody(BaseModel):
    source: str
    pdf: str | None = None
    name: str | None = None


@app.post("/api/projects")
async def open_deck(body: OpenBody):
    """Open (or reopen) a deck from two files already on disk: the source the
    instructor writes — .qmd or .pptx, which is where the speaker notes live —
    and the PDF exported from it, which is where the slide images come from.

    Nothing is uploaded and nothing is copied: the deck folder records the two
    paths and re-reads them on every load, so editing the deck in Quarto or
    PowerPoint and reloading is the whole edit cycle.
    """
    src = Path(body.source).expanduser()
    if not src.is_file():
        raise HTTPException(400, f"Deck source not found: {src}")
    try:
        sources.detect(src)
    except ValueError as e:
        raise HTTPException(400, str(e))
    pdf = Path(body.pdf).expanduser() if body.pdf else deck.resolve_pdf(src)
    if not pdf.is_file():
        raise HTTPException(
            400,
            f"No PDF found at {pdf}. Export {src.name} to PDF and save it next "
            "to the deck with the same name.")

    pid = deck.deck_slug(src.stem)
    config.project_dir(pid).mkdir(parents=True, exist_ok=True)
    if db.get_project(pid) is None:
        db.create_project(pid, body.name or src.stem, None, "loading")
    db.update_project(pid, source_path=str(src.resolve()),
                      pdf_path=str(pdf.resolve()))
    jobs.start_load(pid)
    return _summary(db.get_project(pid))


@app.post("/api/projects/{pid}/reload", status_code=202)
async def reload_deck(pid: str):
    """Re-read the deck and its PDF from disk — after editing the notes, or
    after re-exporting the PDF."""
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    jobs.start_load(pid)
    return {"started": True}


@app.get("/api/projects/{pid}")
async def get_project(pid: str):
    proj = db.get_project(pid)
    if not proj:
        raise HTTPException(404, "not found")
    slides = []
    for s in sorted(store.read_slides(pid).get("slides", []),
                    key=lambda s: s["index"]):
        i = s["index"]
        png = store.slides_dir(pid) / f"slide-{i + 1:03d}.png"
        slides.append({
            "index": i,
            "title": s.get("title", ""),
            "notes": s.get("notes", ""),
            "image_url": (f"api/projects/{pid}/slides/slide-{i + 1:03d}.png"
                          if png.exists() else None),
        })
    return {
        "id": proj["id"], "name": proj["name"], "state": proj["state"],
        "source_type": proj["source_type"], "stale": store.is_stale(pid),
        "files": store.file_status(pid),
        "slides": slides, "config": store.read_config(pid),
        "log": proj.get("log", ""),
    }


@app.get("/api/projects/{pid}/notes")
async def get_notes(pid: str):
    """The deck's speaker notes, slide by slide, with each slide's text for
    context. This is what Claude Code reads before drafting; it writes back by
    editing the deck source, not by calling the app."""
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    meta = store.read_meta(pid)
    return {
        "source": meta.get("source_path", ""),
        "source_type": meta.get("source_type"),
        "slides": store.read_slides(pid).get("slides", []),
    }


class ConfigBody(BaseModel):
    voice_id: str | None = None
    model: str | None = None
    stability: float | None = None
    similarity_boost: float | None = None
    style: float | None = None
    use_speaker_boost: bool | None = None
    speed: float | None = None


@app.put("/api/projects/{pid}/config")
async def put_config(pid: str, body: ConfigBody):
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    merged = store.write_config(pid, body.model_dump())
    return {"ok": True, "config": merged}


# --------------------------------------------------------------------------- #
# ElevenLabs
# --------------------------------------------------------------------------- #
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
    ~/.voiceover/.env and load it live — so the instructor never edits a file,
    and the key survives a skill update."""
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


@app.get("/api/tts/voices/{voice_id}")
async def tts_voice(voice_id: str):
    """Resolve one voice id to its name, labels and preview clip.

    Two lookups, because neither alone covers both cases. /v1/voices/{id}
    answers only for voices the account already holds — its premade set and its
    clones — and 400s on anything else. The Voice Library is reached instead
    through /v1/shared-voices, whose `search` matches an id exactly.

    Text-to-speech accepts a library voice directly, with no add-to-my-voices
    step; ElevenLabs files it under the account the first time it is used, so
    after one build it also answers to the first lookup.
    """
    voice_id = voice_id.strip()
    if not config.ELEVENLABS_API_KEY:
        raise HTTPException(400, "Add your ElevenLabs API key first.")
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY}
    import httpx
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            r = await client.get(
                f"https://api.elevenlabs.io/v1/voices/{voice_id}",
                headers=headers)
            if r.status_code == 200:
                v = r.json()
                labels = v.get("labels") or {}
                return {
                    "voice_id": v.get("voice_id", voice_id),
                    "name": v.get("name", ""),
                    "category": v.get("category", ""),
                    "preview_url": v.get("preview_url", ""),
                    # Only the labels worth showing, in the order they read best.
                    "labels": [labels[k] for k in
                               ("gender", "age", "accent", "language", "use_case")
                               if labels.get(k)],
                }
            if r.status_code in (401, 403):
                raise HTTPException(400, "ElevenLabs rejected your API key.")

            # Not one of the account's own — try the Voice Library.
            r = await client.get(
                "https://api.elevenlabs.io/v1/shared-voices",
                params={"search": voice_id, "page_size": 1}, headers=headers)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Could not reach ElevenLabs: {e}")
    if r.status_code != 200:
        raise HTTPException(502, f"ElevenLabs voice error ({r.status_code})")
    # `search` is a match, not a lookup, so confirm the hit is the id we asked
    # for rather than a near miss.
    hits = [v for v in r.json().get("voices", [])
            if v.get("voice_id") == voice_id]
    if not hits:
        raise HTTPException(404, f"No ElevenLabs voice with id {voice_id}.")
    v = hits[0]
    return {
        "voice_id": v["voice_id"],
        "name": v.get("name", ""),
        "category": v.get("category", ""),
        "preview_url": v.get("preview_url", ""),
        "labels": [v[k] for k in
                   ("gender", "age", "accent", "language", "use_case")
                   if v.get(k)],
    }


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #
@app.post("/api/projects/{pid}/build", status_code=202)
async def build(pid: str):
    proj = db.get_project(pid)
    if not proj:
        raise HTTPException(404, "not found")
    if proj["state"] == "loading":
        raise HTTPException(409, "The deck is still loading.")
    if proj["state"] == "load_failed":
        raise HTTPException(409, "The deck could not be loaded — fix that first.")
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
    if not db.get_project(pid):
        raise HTTPException(404, "not found")
    path = store.video_path(pid)
    if not path.exists():
        raise HTTPException(404, "not built yet")
    # Served inline so the viewer's <video> can stream/seek it (Range-aware).
    return FileResponse(path, media_type="video/mp4")


# --------------------------------------------------------------------------- #
# SPA (optional) — mounted last so API routes win.
# --------------------------------------------------------------------------- #
if config.FRONTEND_DIST.exists():
    class SPAStatic(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            if resp.status_code == 404:
                resp = await super().get_response("index.html", scope)
            # index.html must always revalidate. Vite gives every JS/CSS bundle a
            # content-hashed name, so those are safe to cache forever — but the
            # HTML that points at them keeps the same URL, and a viewer that
            # caches it heuristically (VS Code's Simple Browser and other
            # embedded webviews do) keeps loading the previous build's assets
            # after an update, which looks exactly like "the app didn't change".
            ctype = resp.headers.get("content-type", "")
            if ctype.startswith("text/html"):
                resp.headers["Cache-Control"] = "no-cache, must-revalidate"
            elif "/assets/" in scope.get("path", ""):
                resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return resp

    app.mount("/", SPAStatic(directory=str(config.FRONTEND_DIST), html=True), name="spa")
else:
    @app.get("/")
    async def root():
        return {"app": "Voiceover Builder", "frontend": "not built (frontend/dist missing)"}
