#!/usr/bin/env python3
"""The front door for `/survey`. One command, whatever state the room is in.

  survey.py start                a new room, nothing loaded; join link up
  survey.py ask                  one question, read as JSON on stdin, live now
  survey.py file <path>          add a prepared poll file to the session
  survey.py status               what is running, and what the tally looks like
  survey.py stop                 end the session
  survey.py check [<file>]       is the app reachable, is the token good

The app runs at https://poll.kerryback.com, always on, so none of these pay a
cold start and there is nothing to launch. This script is an HTTP client and
nothing else: no venv, no server process, no tunnel, no state file. It imports
only the standard library, so the plugin has no dependencies to install and the
first `/survey` of a term is as fast as the hundredth.

`ask` and `file` create the session if there isn't one, so the first command of a
class is one command. `start`, and `--new` on either of those two, first throws
away whatever was still running, so a class never opens with last week's
questions in the menu.

Prints JSON on stdout. Claude reads that and tells the instructor what happened.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

DEFAULT_URL = "https://poll.kerryback.com"

HOME_DIR = Path(os.environ.get("SURVEY_HOME", Path.home() / ".survey"))
ENV_PATH = HOME_DIR / ".env"

TIMEOUT = 20

sys.dont_write_bytecode = True


def out(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def die(message: str, **extra: object) -> None:
    out({"ok": False, "error": message, **extra})
    raise SystemExit(1)


class ApiError(Exception):
    """A call that failed where the caller wants to say so in its own words.

    Everywhere but `check`, a failed call should print and stop -- Claude reads
    one JSON object and tells the instructor what went wrong. `check` is the
    exception: a rejected token is the thing it was asked to find out, so it
    reports it as one line of a readiness report instead.
    """

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


# --- where the app is, and how to prove who we are ---------------------------


def _env_file() -> dict[str, str]:
    """Read ~/.survey/.env.

    The token lives outside the skill directory on purpose: the skill directory
    is package content, and a plugin update would wipe a key stored in it.
    """
    values: dict[str, str] = {}
    try:
        text = ENV_PATH.read_text()
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


def config() -> tuple[str, str]:
    """(base_url, token). Real environment wins, then ~/.survey/.env."""
    stored = _env_file()
    base = (
        os.environ.get("SURVEY_URL")
        or stored.get("SURVEY_URL")
        or DEFAULT_URL
    ).rstrip("/")
    token = os.environ.get("SURVEY_TOKEN") or stored.get("SURVEY_TOKEN") or ""
    return base, token


def require_token() -> tuple[str, str]:
    base, token = config()
    if not token:
        die(
            "No SURVEY_TOKEN. Put it in the environment, or in "
            f"{ENV_PATH} as SURVEY_TOKEN=...",
            token_file=str(ENV_PATH),
        )
    return base, token


def api(path: str, payload: dict | None = None, method: str | None = None,
        quiet: bool = False) -> dict:
    base, token = require_token()
    request = urllib.request.Request(
        f"{base}{path}",
        data=None if payload is None else json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method=method or ("GET" if payload is None else "POST"),
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {}
        message = parsed.get("error") or parsed.get("detail") or raw.strip() or f"HTTP {exc.code}"
        if exc.code == 404:
            # 404 on an API route means the token was wrong, not that the route
            # is missing -- the app answers unauthenticated callers with nothing.
            message = (
                "The app didn't accept that token. Check SURVEY_TOKEN matches "
                "the one set on the server."
            )
        if quiet:
            raise ApiError(str(message), exc.code) from None
        die(str(message), status=exc.code)
    except (urllib.error.URLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        if quiet:
            raise ApiError(f"Couldn't reach {base}: {reason}") from None
        die(f"Couldn't reach {base}: {reason}")
    return {}


def facts(body: dict) -> dict:
    """What the instructor needs to say out loud, and to get the screen up.

    Two audiences in one dict. The link and the room code are for the room. The
    display page and its code are for whatever machine is driving the projector
    -- often not this one, which is why the six digits exist alongside the long
    URL this script can open by itself.
    """
    return {
        "student_link": body.get("student_url", ""),
        "room_code": body.get("room_code", ""),
        "display_url": body.get("display_url", ""),
        "display_page": body.get("display_page", ""),
        "display_code": body.get("display_code", ""),
    }


def open_display(body: dict, no_open: bool) -> None:
    url = body.get("display_url")
    if url and not no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def read_deck(path_text: str) -> tuple[dict, str]:
    target = Path(path_text).expanduser()
    if not target.is_file():
        die(
            f"No poll file at {target}",
            candidates=sorted(str(p) for p in Path.cwd().glob("*.json"))[:20],
        )
    try:
        raw = json.loads(target.read_text())
    except json.JSONDecodeError as exc:
        die(f"{target} is not valid JSON: {exc}")
    return raw, target.name


# --- subcommands --------------------------------------------------------------


def clear(state: dict) -> bool:
    """End the session described by `state`, if there is one. True if there was.

    Stop rather than reset, so the room code dies with the session: a link
    forwarded last week shouldn't let anyone answer this week's questions.
    """
    if not state.get("running"):
        return False
    api("/api/stop", {})
    return True


def cmd_start(args) -> None:
    """A new room, every time.

    A session outlives the class that made it -- the app holds it in memory
    until something replaces it -- so this ends whatever is still running
    before opening its own. Otherwise Tuesday starts with last Thursday's
    questions and answers already in the menu.
    """
    replaced = clear(api("/api/state"))
    body = api("/api/session", {})
    open_display(body, args.no_open)
    out({
        "ok": True,
        "started": body.get("started", False),
        "replaced": replaced,
        **facts(body),
        "questions": body.get("questions", 0),
        "here": body.get("here", 0),
    })


def cmd_ask(args) -> None:
    raw = args.json if args.json and args.json != "-" else sys.stdin.read()
    raw = (raw or "").strip()
    if not raw:
        die("No question given. Pipe the question JSON in on stdin.")
    try:
        question = json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"That isn't valid JSON: {exc}")
        return

    before = api("/api/state")
    replaced = args.new and clear(before)
    if replaced:
        before = {}
    body = api("/api/question", question)
    started = not before.get("running")
    if started:
        open_display(body, args.no_open)
    out({
        "ok": True,
        "started": started,
        "replaced": replaced,
        "asked": body.get("text"),
        "type": body.get("type"),
        "index": body.get("index"),
        "questions": body.get("total"),
        **facts(body),
    })


def cmd_file(args) -> None:
    raw, name = read_deck(args.path)
    before = api("/api/state")
    replaced = args.new and clear(before)
    if replaced:
        before = {}
    body = api("/api/deck", {"name": name, "deck": raw})
    started = not before.get("running")
    if started:
        open_display(body, args.no_open)
    out({
        "ok": True,
        "started": started,
        "replaced": replaced,
        "title": body.get("title"),
        "added": body.get("added"),
        "types": body.get("types"),
        "first_index": body.get("first"),
        "questions": body.get("total"),
        **facts(body),
    })


def cmd_status(args) -> None:
    body = api("/api/state")
    if not body.get("running"):
        out({"ok": True, "running": False})
        return
    out({
        "ok": True,
        "running": True,
        **facts(body),
        "title": body.get("title", ""),
        "questions": body.get("count", 0),
        "index": body.get("index", -1),
        "open": body.get("open", False),
        "here": body.get("here", 0),
        "responses": body.get("responses", 0),
        "results": body.get("all_results", []),
    })


def cmd_stop(args) -> None:
    """End the class. The projector says "No session running" by itself."""
    body = api("/api/stop", {})
    out({"ok": True, "running": False, "stopped": bool(body.get("stopped"))})


def cmd_reset(args) -> None:
    body = api("/api/reset", {})
    out({"ok": True, "reset": True, **facts(body)})


def cmd_check(args) -> None:
    """Reachable, authorised, and does this file load.

    There is no machine to set up any more -- this asks about the network and
    the token, which are the only two things that can be wrong before class.
    """
    base, token = config()
    report: dict = {"app": base, "token_set": bool(token)}

    try:
        with urllib.request.urlopen(f"{base}/healthz", timeout=TIMEOUT) as response:
            report["reachable"] = response.status == 200
            report["session_running"] = bool(json.load(response).get("running"))
    except Exception as exc:
        report["reachable"] = False
        report["problem"] = f"Couldn't reach {base}: {exc}"

    if report.get("reachable") and token:
        try:
            state = api("/api/state", quiet=True)
            report["token_ok"] = True
            report["questions"] = state.get("count", 0)
        except ApiError as exc:
            report["token_ok"] = False
            report["problem"] = (
                f"{exc} It is read from {ENV_PATH} unless the environment "
                "sets it."
            )
    elif report.get("reachable") and not token:
        report["problem"] = (
            f"No SURVEY_TOKEN. Put it in the environment or in {ENV_PATH}."
        )

    if args.path:
        raw, name = read_deck(args.path)
        checked = api("/api/validate", {"name": name, "deck": raw})
        report["poll_file"] = {"path": args.path, **checked}

    ok = bool(report.get("reachable")) and bool(report.get("token_ok"))
    out({"ok": ok, **report})
    if not ok:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live classroom poll.")
    parser.add_argument("--no-open", action="store_true",
                        help="don't open the display in a browser")
    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("start", help="a new room, nothing loaded")

    ask = subs.add_parser("ask", help="put one question up now (JSON on stdin)")
    ask.add_argument("json", nargs="?", help="the question as JSON, or - for stdin")
    ask.add_argument("--new", action="store_true",
                     help="end any session still running first")

    add = subs.add_parser("file", help="add a prepared poll file to the session")
    add.add_argument("path")
    add.add_argument("--new", action="store_true",
                     help="end any session still running first")

    subs.add_parser("status", help="what's running, and the tally so far")

    subs.add_parser("stop", help="end the session")
    subs.add_parser("reset", help="empty the session, keeping the room open")

    verify = subs.add_parser("check", help="is the app reachable and the token good")
    verify.add_argument("path", nargs="?", help="also validate this poll file")

    args = parser.parse_args()
    {
        "start": cmd_start,
        "ask": cmd_ask,
        "file": cmd_file,
        "status": cmd_status,
        "stop": cmd_stop,
        "reset": cmd_reset,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    main()
