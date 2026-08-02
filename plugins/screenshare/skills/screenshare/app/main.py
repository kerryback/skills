"""A screen-sharing relay for the classroom computer.

Students open an HTTPS link on their own laptops, pick a screen, window or
browser tab, and wait. The instructor -- at the classroom computer, on the
display page -- chooses whose screen goes up on the projector.

The server only carries the WebRTC handshake and a short list of who is in the
room. The video never passes through it: it goes browser to browser, directly
when the network permits and through a TURN relay when it does not.
"""

from __future__ import annotations

import asyncio
import io
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

import segno
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .hub import Hub

BASE_DIR = Path(__file__).resolve().parent

# The launcher generates both of these and passes them in, so it can print the
# code and open the display page without having to ask the server for them.
CODE = os.environ.get("SCREENSHARE_CODE") or config.room_code()
DISPLAY_KEY = os.environ.get("SCREENSHARE_DISPLAY_KEY") or secrets.token_urlsafe(12)

hub = Hub(CODE)

@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fetch TURN credentials now rather than when the first student joins, so
    # nobody waits on the round trip and a bad key shows up in the launcher
    # output instead of halfway through a class.
    await asyncio.to_thread(config.warm_turn)
    status = config.turn_status()
    if status["source"] != "none":
        print(f"[screenshare] TURN: {status['source']}", flush=True)
    if status["error"]:
        print(f"[screenshare] TURN problem: {status['error']}", flush=True)
    yield


app = FastAPI(title="Screen Share", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _require_key(key: str) -> None:
    """The display page and the admin endpoints sit behind an unguessable key.

    The tunnel makes every route publicly reachable, and a request arriving
    through it looks like it came from 127.0.0.1 -- cloudflared is the one
    connecting -- so where the request comes from proves nothing. The key does.
    """
    if not secrets.compare_digest(key or "", DISPLAY_KEY):
        raise HTTPException(status_code=404, detail="Not found")


# --- pages -----------------------------------------------------------------


@app.get("/")
def share_page(request: Request):
    """What the tunnel URL gives a student."""
    return templates.TemplateResponse(request, "share.html", {})


@app.get("/display")
def display_page(request: Request, key: str = ""):
    """The classroom computer's own page, opened locally by the launcher."""
    _require_key(key)
    status = config.turn_status()
    return templates.TemplateResponse(
        request,
        "display.html",
        {
            "key": DISPLAY_KEY,
            "code": hub.code,
            "has_turn": status["configured"],
            "turn_error": status["error"],
            "policy": config.ice_policy(),
        },
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}


# --- for the launcher and for Claude ---------------------------------------


@app.post("/api/tunnel")
async def set_tunnel(payload: dict, key: str = ""):
    """The launcher reports the Cloudflare URL once cloudflared has printed it."""
    _require_key(key)
    url = str(payload.get("url") or "").strip()
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Expected an https:// URL")
    await hub.set_tunnel(url)
    return {"ok": True, "url": url}


@app.get("/api/state")
def state(key: str = ""):
    """Everything worth knowing about the room, for diagnosing a bad session."""
    _require_key(key)
    status = config.turn_status()
    snapshot = hub.snapshot()
    snapshot.update(
        {
            "displays": len(hub.displays),
            "turn_configured": status["configured"],
            "turn_source": status["source"],
            "turn_error": status["error"],
            "ice_policy": config.ice_policy(),
            "config_path": str(config.CONFIG_PATH),
        }
    )
    return JSONResponse(snapshot)


@app.get("/api/qr.svg")
def qr(key: str = ""):
    _require_key(key)
    if not hub.tunnel_url:
        raise HTTPException(status_code=404, detail="No tunnel yet")
    buf = io.BytesIO()
    segno.make(hub.tunnel_url, error="m").save(
        buf, kind="svg", scale=5, border=2, dark="#0f172a", light="#ffffff"
    )
    return Response(buf.getvalue(), media_type="image/svg+xml")


# --- signalling ------------------------------------------------------------


@app.websocket("/ws/student")
async def ws_student(ws: WebSocket):
    await ws.accept()
    peer_id: str | None = None
    try:
        first = await ws.receive_json()
        given = str(first.get("code") or "").strip()
        if first.get("type") != "join" or not secrets.compare_digest(given, hub.code):
            await ws.send_json(
                {
                    "type": "error",
                    "message": "That code doesn't match the one on the classroom screen.",
                }
            )
            await ws.close()
            return

        name = (str(first.get("name") or "").strip() or "Anonymous")[:60]
        peer_id = await hub.add_peer(name, ws)
        await ws.send_json(
            {
                "type": "joined",
                "id": peer_id,
                "ice": config.ice_servers(),
                "policy": config.ice_policy(),
            }
        )

        while True:
            message = await ws.receive_json()
            kind = message.get("type")
            if kind == "ready":
                await hub.set_ready(peer_id)
            elif kind == "unready":
                await hub.set_unready(peer_id)
            elif kind == "signal":
                # Only the student the instructor put up may negotiate. Without
                # this, anyone with the code could send an offer whenever they
                # liked and take the projector from whoever is on it.
                if hub.stage == peer_id:
                    await hub.to_display(
                        {"type": "signal", "from": peer_id, "data": message.get("data")}
                    )
            elif kind == "ping":
                await ws.send_json({"type": "pong"})
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        if peer_id:
            await hub.remove_peer(peer_id)


@app.websocket("/ws/display")
async def ws_display(ws: WebSocket, key: str = ""):
    if not secrets.compare_digest(key or "", DISPLAY_KEY):
        await ws.close(code=4403)
        return
    await ws.accept()
    # The classroom end needs the same ICE servers the students get: when the
    # campus blocks the direct path, both ends have to be able to reach TURN.
    await ws.send_json(
        {"type": "config", "ice": config.ice_servers(), "policy": config.ice_policy()}
    )
    await hub.add_display(ws)
    try:
        while True:
            message = await ws.receive_json()
            kind = message.get("type")
            if kind == "stage":
                await hub.set_stage(message.get("id"))
            elif kind == "auto":
                await hub.set_auto(bool(message.get("on")))
            elif kind == "signal":
                await hub.to_peer(message.get("to"), {"type": "signal", "data": message.get("data")})
            elif kind == "path":
                await hub.record_path(message.get("path") or {})
    except (WebSocketDisconnect, RuntimeError, ValueError):
        pass
    finally:
        await hub.remove_display(ws)
