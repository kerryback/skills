"""Settings for the classroom screen-sharing app.

Nothing here is required. With no config file at all the app runs on public
STUN servers, which is enough on a network that lets two machines talk to each
other directly. What the file is for is the case where it isn't: campus
segmentation that keeps the student laptop and the classroom computer from
reaching each other, where the video has to be relayed by a TURN server.

    ~/.screenshare/config.json

    {
      "code": "4271",
      "cloudflare": {"key_id": "…", "api_token": "…"},
      "turn": {
        "urls": ["turn:turn.example.edu:3478?transport=udp",
                 "turns:turn.example.edu:5349?transport=tcp"],
        "username": "classroom",
        "credential": "…"
      },
      "force_relay": false
    }

`code` fixes the room code so it stays the same all term instead of changing
each launch. `force_relay` refuses direct paths entirely -- it is a test switch,
for confirming TURN actually works before the class where you need it.

There are two ways to give it TURN, and you want one of them, not both:

`cloudflare` is the managed one. Cloudflare does not issue passwords that sit in
a file; it issues short-lived ones from a long-lived key, so this fetches a
fresh set at launch and caches them. A static credential would go stale in the
middle of a term, silently.

`turn` is the static one, for a TURN server that does hand out a fixed username
and password -- your own coturn, or a provider that works that way.
"""

from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HOME_DIR = Path(os.environ.get("SCREENSHARE_HOME", Path.home() / ".screenshare"))
CONFIG_PATH = HOME_DIR / "config.json"

DEFAULT_STUN = [
    "stun:stun.l.google.com:19302",
    "stun:stun.cloudflare.com:3478",
]


def load() -> dict[str, Any]:
    try:
        with CONFIG_PATH.open() as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save(data: dict[str, Any]) -> None:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def room_code(cfg: dict[str, Any] | None = None) -> str:
    """The code students type to prove they are in the room."""
    cfg = load() if cfg is None else cfg
    fixed = str(cfg.get("code") or "").strip()
    if fixed:
        return fixed
    return f"{secrets.randbelow(9000) + 1000}"


def _turn(cfg: dict[str, Any]) -> dict[str, Any] | None:
    """TURN from the environment first, then the config file."""
    env_urls = os.environ.get("SCREENSHARE_TURN_URLS", "").strip()
    if env_urls:
        urls = [u.strip() for u in env_urls.split(",") if u.strip()]
        server: dict[str, Any] = {"urls": urls}
        if os.environ.get("SCREENSHARE_TURN_USERNAME"):
            server["username"] = os.environ["SCREENSHARE_TURN_USERNAME"]
            server["credential"] = os.environ.get("SCREENSHARE_TURN_CREDENTIAL", "")
        return server

    turn = cfg.get("turn")
    if not isinstance(turn, dict):
        return None
    urls = turn.get("urls") or turn.get("url")
    if isinstance(urls, str):
        urls = [urls]
    if not urls:
        return None
    server = {"urls": list(urls)}
    if turn.get("username"):
        server["username"] = turn["username"]
        server["credential"] = turn.get("credential", "")
    return server


# --- Cloudflare -------------------------------------------------------------

CLOUDFLARE_ENDPOINT = (
    "https://rtc.live.cloudflare.com/v1/turn/keys/{key_id}/credentials/generate-ice-servers"
)

# Credentials are short-lived, so they are fetched once and kept until they are
# nearly expired. `error` is held for /api/state: a TURN fetch that quietly
# failed looks exactly like a campus network problem, and the two want very
# different fixes.
_cache: dict[str, Any] = {"servers": None, "expires": 0.0, "error": ""}


def _cloudflare(cfg: dict[str, Any]) -> dict[str, Any] | None:
    block = cfg.get("cloudflare") if isinstance(cfg.get("cloudflare"), dict) else {}
    key_id = os.environ.get("SCREENSHARE_CF_TURN_KEY_ID") or block.get("key_id")
    token = os.environ.get("SCREENSHARE_CF_TURN_TOKEN") or block.get("api_token")
    if not key_id or not token:
        return None
    try:
        ttl = int(block.get("ttl", 86400))
    except (TypeError, ValueError):
        ttl = 86400
    return {"key_id": str(key_id), "token": str(token), "ttl": max(600, ttl)}


def fetch_cloudflare(cloud: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Ask Cloudflare for a fresh ICE server list. Returns None on any failure.

    Cloudflare hands back the whole list -- its own STUN plus TURN over UDP, TCP
    and TLS on 443 -- so it replaces the defaults rather than adding to them.
    """
    request = urllib.request.Request(
        CLOUDFLARE_ENDPOINT.format(key_id=cloud["key_id"]),
        data=json.dumps({"ttl": cloud["ttl"]}).encode(),
        headers={
            "Authorization": f"Bearer {cloud['token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = "check the key ID and API token" if exc.code in (401, 403) else exc.reason
        _cache["error"] = f"Cloudflare returned {exc.code} ({detail})"
        return None
    except Exception as exc:
        _cache["error"] = f"Could not reach Cloudflare: {exc}"
        return None

    servers = payload.get("iceServers")
    if isinstance(servers, dict):  # older shape: a single server object
        servers = [servers]
    if not isinstance(servers, list) or not servers:
        _cache["error"] = "Cloudflare's reply had no iceServers in it"
        return None

    _cache["error"] = ""
    return servers


def _cloudflare_servers(cloud: dict[str, Any]) -> list[dict[str, Any]] | None:
    if _cache["servers"] and time.time() < _cache["expires"]:
        return _cache["servers"]
    servers = fetch_cloudflare(cloud)
    if servers is None:
        return None
    # Refresh early rather than at the last moment, so a long session never
    # hands a student a credential that expires while they are presenting.
    _cache["servers"] = servers
    _cache["expires"] = time.time() + cloud["ttl"] * 0.8
    return servers


def warm_turn() -> None:
    """Fetch credentials at startup so no student waits on the round trip."""
    cloud = _cloudflare(load())
    if cloud:
        _cloudflare_servers(cloud)


def turn_status(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = load() if cfg is None else cfg
    if _cloudflare(cfg):
        working = bool(_cache["servers"])
        return {
            "source": "cloudflare" if working else "cloudflare (failing)",
            "configured": working,
            "error": _cache["error"],
        }
    if _turn(cfg):
        return {"source": "static", "configured": True, "error": ""}
    return {"source": "none", "configured": False, "error": ""}


# --- what the browsers get --------------------------------------------------


def ice_servers(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cfg = load() if cfg is None else cfg

    cloud = _cloudflare(cfg)
    if cloud:
        servers = _cloudflare_servers(cloud)
        if servers:
            return servers
        # Fall through to plain STUN rather than handing back nothing. Direct
        # connections still work; only the relay is missing.

    stun = cfg.get("stun") or DEFAULT_STUN
    servers = [{"urls": list(stun)}]
    turn = _turn(cfg)
    if turn:
        servers.append(turn)
    return servers


def has_turn(cfg: dict[str, Any] | None = None) -> bool:
    return turn_status(load() if cfg is None else cfg)["configured"]


def ice_policy(cfg: dict[str, Any] | None = None) -> str:
    """"relay" makes both ends refuse direct paths -- a way to prove TURN works."""
    cfg = load() if cfg is None else cfg
    forced = cfg.get("force_relay") or os.environ.get("SCREENSHARE_FORCE_RELAY")
    return "relay" if forced and has_turn(cfg) else "all"
