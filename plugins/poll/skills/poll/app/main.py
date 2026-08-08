"""Live in-class polling.

The instructor drives a full-screen display on the classroom computer; students
answer from their own devices over a Cloudflare tunnel. Answers are anonymous:
there is no name field, no roster, and nothing stored that could identify who
said what.

The server holds one session in memory. Results are written to a CSV only when
the instructor asks for them.
"""

from __future__ import annotations

import io
import os
import secrets
from pathlib import Path

import segno
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config, deck as deck_mod, results, tally
from .session import Session

BASE_DIR = Path(__file__).resolve().parent

CODE = os.environ.get("POLL_CODE") or config.room_code()
DISPLAY_KEY = os.environ.get("POLL_DISPLAY_KEY") or secrets.token_urlsafe(12)

session = Session(CODE)

app = FastAPI(title="Polls")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _require_key(key: str) -> None:
    """The display and the admin routes sit behind an unguessable key.

    The tunnel makes every route public, and requests arriving through it look
    like they came from localhost, so the key is the only thing that separates
    the instructor's controls from the students' page.
    """
    if not secrets.compare_digest(key or "", DISPLAY_KEY):
        raise HTTPException(status_code=404, detail="Not found")


# --- pages -----------------------------------------------------------------


@app.get("/")
def vote_page(request: Request):
    return templates.TemplateResponse(request, "vote.html", {})


@app.get("/display")
def display_page(request: Request, key: str = ""):
    _require_key(key)
    return templates.TemplateResponse(
        request, "display.html", {"key": DISPLAY_KEY, "code": session.code}
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}


# --- the poll file ---------------------------------------------------------


@app.post("/api/deck")
async def add_deck(payload: dict, key: str = ""):
    """Add a prepared poll file to the session -- `/poll <filename>`.

    The questions append; the pointer does not move. Loading a file at the top
    of class leaves the join screen up, and loading one mid-class doesn't yank
    the projector off the question the room is answering.

    A bad file is rejected with every problem listed at once, and the session is
    left exactly as it was -- so a typo mid-class cannot disturb the questions
    that are working.
    """
    _require_key(key)
    path = str(payload.get("path") or "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="Give me a 'path' to a poll file")
    try:
        loaded = deck_mod.load(path)
    except deck_mod.DeckError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    first = session.extend(loaded["questions"], loaded["title"], loaded["path"])
    await session.broadcast()
    return {
        "title": session.deck["title"],
        "added": len(loaded["questions"]),
        "first": first,
        "total": len(session.deck["questions"]),
        "types": [q["type"] for q in loaded["questions"]],
    }


@app.post("/api/question")
async def add_question(payload: dict, key: str = ""):
    """Put one question on the projector now -- `/poll <question>`.

    Unlike a file, this jumps straight to what it just added and opens voting.
    That is the whole point: the instructor said the question out loud ten
    seconds ago and the room is waiting.
    """
    _require_key(key)
    raw = payload.get("question") if "question" in payload else payload
    try:
        question = deck_mod.normalise_question(raw)
    except deck_mod.DeckError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    index = session.extend([question])
    await session.goto(index)
    return {
        "index": index,
        "total": len(session.deck["questions"]),
        "type": question["type"],
        "text": question["text"],
    }


@app.post("/api/reset")
async def reset(key: str = ""):
    """Empty the session. Explicit only -- nothing else here discards answers."""
    _require_key(key)
    session.reset()
    await session.broadcast()
    return {"ok": True}


@app.get("/api/state")
def state(key: str = ""):
    """Everything about the session, including the tally so far."""
    _require_key(key)
    snapshot = session.display_state()
    snapshot["display_key"] = DISPLAY_KEY
    if session.deck is not None:
        snapshot["all_results"] = [
            dict(tally.tally(question, session.answers(index)), question=question["text"])
            for index, question in enumerate(session.deck["questions"])
        ]
    return JSONResponse(snapshot)


@app.post("/api/save")
def save(key: str = ""):
    _require_key(key)
    try:
        path = results.write_csv(session)
    except (ValueError, OSError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"path": path}


@app.post("/api/tunnel")
async def set_tunnel(payload: dict, key: str = ""):
    _require_key(key)
    url = str(payload.get("url") or "").strip()
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Expected an https:// URL")
    await session.set_tunnel(url)
    return {"ok": True, "url": url}


@app.get("/api/qr.svg")
def qr(key: str = ""):
    _require_key(key)
    if not session.tunnel_url:
        raise HTTPException(status_code=404, detail="No tunnel yet")
    buffer = io.BytesIO()
    segno.make(session.tunnel_url, error="m").save(
        buffer, kind="svg", scale=5, border=2, dark="#0f172a", light="#ffffff"
    )
    return Response(buffer.getvalue(), media_type="image/svg+xml")


# --- live ------------------------------------------------------------------


@app.websocket("/ws/display")
async def ws_display(ws: WebSocket, key: str = ""):
    if not secrets.compare_digest(key or "", DISPLAY_KEY):
        await ws.close(code=4403)
        return
    await ws.accept()
    await session.add_display(ws)
    try:
        while True:
            message = await ws.receive_json()
            kind = message.get("type")
            if kind == "goto":
                await session.goto(int(message.get("index", -1)))
            elif kind == "open":
                await session.set_open(bool(message.get("on")))
            elif kind == "results":
                await session.set_show_results(bool(message.get("on")))
            elif kind == "reveal":
                await session.set_revealed(bool(message.get("on")))
    except (WebSocketDisconnect, RuntimeError, ValueError, TypeError):
        pass
    finally:
        session.displays.discard(ws)


@app.websocket("/ws/vote")
async def ws_vote(ws: WebSocket):
    await ws.accept()
    participant = ""
    try:
        first = await ws.receive_json()
        given = str(first.get("code") or "").strip()
        if first.get("type") != "join" or not secrets.compare_digest(given, session.code):
            await ws.send_json(
                {"type": "error", "message": "That code doesn't match the one on the screen."}
            )
            await ws.close()
            return

        # The browser supplies its own id, kept in local storage, so a student
        # can change their answer instead of being counted twice. It is random
        # and means nothing -- it is not a login.
        participant = str(first.get("id") or "")[:64] or secrets.token_urlsafe(9)
        await ws.send_json({"type": "joined", "id": participant})
        await session.add_voter(participant, ws)

        while True:
            message = await ws.receive_json()
            if message.get("type") == "answer":
                ok, why = await session.record(
                    participant, int(message.get("index", -1)), message.get("value")
                )
                if not ok:
                    await ws.send_json({"type": "rejected", "message": why})
    except (WebSocketDisconnect, RuntimeError, ValueError, TypeError):
        pass
    finally:
        if participant:
            await session.remove_voter(participant, ws)
