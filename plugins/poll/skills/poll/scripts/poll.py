#!/usr/bin/env python3
"""The front door for `/poll`. One command, whatever state the room is in.

Every subcommand here starts by making sure a session exists, so none of them
require anything to have been set up first:

  poll.py start                 bring the room up; join link on the projector
  poll.py ask                   one question, read as JSON on stdin, live now
  poll.py file <path>           add a prepared poll file to the session
  poll.py status                what is running, and what the tally looks like
  poll.py results               write the CSV
  poll.py stop                  end the session
  poll.py check                 is this machine set up?

The first of those to run in a given class pays for the cold start -- building
the venv the very first time, then a few seconds of uvicorn and however long
Cloudflare takes to hand out a hostname. Everything after it is a local HTTP
request against a session that is already up, which is why a question typed
mid-class appears on the projector immediately.

The session is a detached process, not a child of this one. It has to survive
the shell that started it -- otherwise the second `/poll` of the day would find
nothing running and drag the room through a new link.

Prints JSON on stdout. Claude reads that and tells the instructor what happened.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LAUNCHER = SCRIPT_DIR / "skill_launch.py"

HOME_DIR = Path(os.environ.get("POLL_HOME", Path.home() / ".poll"))
STATE_PATH = HOME_DIR / "session.json"
LOG_PATH = HOME_DIR / "app.log"

IS_WINDOWS = os.name == "nt"

# The first launch on a machine builds a venv and pip-installs into it, which is
# slow on classroom wifi; later launches are a few seconds.
COLD_START_TIMEOUT = 240.0
TUNNEL_TIMEOUT = 45.0

sys.dont_write_bytecode = True


def out(payload: dict) -> None:
    print(json.dumps(payload, indent=2))


def die(message: str, **extra: object) -> None:
    out({"ok": False, "error": message, **extra})
    raise SystemExit(1)


# --- talking to a running session -------------------------------------------


def read_state() -> dict | None:
    try:
        with STATE_PATH.open() as fh:
            state = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return state if isinstance(state, dict) and state.get("base") else None


def alive(state: dict) -> bool:
    try:
        with urllib.request.urlopen(state["base"] + "/healthz", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def api(state: dict, path: str, payload: dict | None = None) -> dict:
    url = f"{state['base']}{path}?key={state['display_key']}"
    request = urllib.request.Request(
        url,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"error": body.strip() or f"HTTP {exc.code}"}
        die(str(parsed.get("error") or parsed.get("detail") or body))
    except Exception as exc:  # pragma: no cover - network-shaped failures
        die(f"The session stopped responding: {exc}")
    return {}


def log_tail(lines: int = 12) -> str:
    try:
        return "\n".join(LOG_PATH.read_text(errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


# --- starting one ------------------------------------------------------------


def spawn(port: int, workdir: str, no_open: bool, no_tunnel: bool) -> subprocess.Popen:
    """Start the session in its own process group, detached from this shell.

    Its own group matters at both ends: it survives the shell that started it,
    and `stop` can take down the launcher, uvicorn and cloudflared together
    instead of orphaning a server still holding the port.
    """
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(LAUNCHER), "--port", str(port), "--workdir", workdir]
    if no_open:
        command.append("--no-open")
    if no_tunnel:
        command.append("--no-tunnel")

    handle = LOG_PATH.open("a")
    handle.write(f"\n--- launching on port {port} ---\n")
    handle.flush()

    extras: dict = {"stdout": handle, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
    if IS_WINDOWS:
        extras["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        extras["start_new_session"] = True

    return subprocess.Popen(command, **extras)


def ensure(port: int, no_open: bool = False, no_tunnel: bool = False) -> tuple[dict, bool]:
    """Return the live session, starting one if there isn't one. (state, started)"""
    state = read_state()
    if state is not None and alive(state):
        return state, False

    if state is not None:
        # Stale file from a session that was killed rather than stopped.
        try:
            STATE_PATH.unlink()
        except OSError:
            pass

    process = spawn(port, os.getcwd(), no_open, no_tunnel)

    deadline = time.monotonic() + COLD_START_TIMEOUT
    while time.monotonic() < deadline:
        state = read_state()
        if state is not None and alive(state):
            return state, True
        if process.poll() is not None:
            # It gave up -- usually the port is taken. Say so now rather than
            # letting the instructor watch a dead prompt for four minutes.
            die(f"The session failed to start on port {port}.", log=log_tail())
        time.sleep(0.5)

    die(
        "The session did not come up. If port "
        f"{port} is in use, try another with --port.",
        log=log_tail(),
    )
    raise SystemExit(1)


def await_tunnel(state: dict, timeout: float = TUNNEL_TIMEOUT) -> dict:
    """Wait for Cloudflare to hand out a hostname, so we can print the link."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = read_state()
        if current and (current.get("tunnel_url") or current.get("tunnel_error")):
            return current
        time.sleep(0.5)
    return read_state() or state


def joining(state: dict) -> dict:
    """The three things that go on the projector, and why they might be missing."""
    facts = {
        "student_link": state.get("tunnel_url") or "",
        "room_code": state.get("code", ""),
        "display_url": state.get("display_url", ""),
    }
    if not facts["student_link"] and state.get("tunnel_error"):
        facts["tunnel_problem"] = state["tunnel_error"]
    return facts


# --- subcommands --------------------------------------------------------------


def cmd_start(args) -> None:
    state, started = ensure(args.port, args.no_open, args.no_tunnel)
    if started and not args.no_tunnel:
        state = await_tunnel(state)
    live = api(state, "/api/state")
    out({
        "ok": True,
        "started": started,
        **joining(state),
        "questions": live.get("count", 0),
        "here": live.get("here", 0),
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

    state, started = ensure(args.port, args.no_open, args.no_tunnel)
    if started and not args.no_tunnel:
        state = await_tunnel(state)

    added = api(state, "/api/question", question)
    out({
        "ok": True,
        "started": started,
        "asked": added.get("text"),
        "type": added.get("type"),
        "index": added.get("index"),
        "questions": added.get("total"),
        **joining(state),
    })


def cmd_file(args) -> None:
    target = Path(args.path).expanduser()
    if not target.is_file():
        die(f"No poll file at {target}",
            candidates=sorted(str(p) for p in Path.cwd().glob("*.json"))[:20])

    state, started = ensure(args.port, args.no_open, args.no_tunnel)
    if started and not args.no_tunnel:
        state = await_tunnel(state)

    loaded = api(state, "/api/deck", {"path": str(target.resolve())})
    out({
        "ok": True,
        "started": started,
        "title": loaded.get("title"),
        "added": loaded.get("added"),
        "types": loaded.get("types"),
        "first_index": loaded.get("first"),
        "questions": loaded.get("total"),
        **joining(state),
    })


def cmd_status(args) -> None:
    state = read_state()
    if state is None or not alive(state):
        out({"ok": True, "running": False})
        return
    live = api(state, "/api/state")
    out({
        "ok": True,
        "running": True,
        **joining(state),
        "title": live.get("title", ""),
        "questions": live.get("count", 0),
        "index": live.get("index", -1),
        "open": live.get("open", False),
        "here": live.get("here", 0),
        "responses": live.get("responses", 0),
        "results": live.get("all_results", []),
    })


def cmd_results(args) -> None:
    state = read_state()
    if state is None or not alive(state):
        die("Nothing is running, so there are no answers to write.")
        return
    out({"ok": True, **api(state, "/api/save", {})})


def cmd_stop(args) -> None:
    state = read_state()
    if state is None:
        out({"ok": True, "running": False})
        return
    pid = state.get("pid")
    if isinstance(pid, int):
        # The whole group, not just the launcher: a bare SIGTERM kills the
        # launcher before its cleanup runs and leaves uvicorn holding the port,
        # so the next `/poll` finds the room apparently occupied by nothing.
        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                               capture_output=True, check=False)
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
    for _ in range(20):
        if not alive(state):
            break
        time.sleep(0.25)
    try:
        STATE_PATH.unlink()
    except OSError:
        pass
    out({"ok": True, "running": False, "stopped": True})


def cmd_check(args) -> None:
    command = [sys.executable, str(LAUNCHER), "--check"]
    if args.path:
        command += ["--poll", args.path]
    raise SystemExit(subprocess.run(command).returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live classroom poll.")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--no-open", action="store_true",
                        help="don't open the display in a browser")
    parser.add_argument("--no-tunnel", action="store_true",
                        help="local only; students can't join")
    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("start", help="bring the room up with nothing loaded")

    ask = subs.add_parser("ask", help="put one question up now (JSON on stdin)")
    ask.add_argument("json", nargs="?", help="the question as JSON, or - for stdin")

    add = subs.add_parser("file", help="add a prepared poll file to the session")
    add.add_argument("path")

    subs.add_parser("status", help="what's running, and the tally so far")
    subs.add_parser("results", help="write the CSV")
    subs.add_parser("stop", help="end the session")

    verify = subs.add_parser("check", help="is this machine set up?")
    verify.add_argument("path", nargs="?", help="also validate this poll file")

    args = parser.parse_args()
    {
        "start": cmd_start,
        "ask": cmd_ask,
        "file": cmd_file,
        "status": cmd_status,
        "results": cmd_results,
        "stop": cmd_stop,
        "check": cmd_check,
    }[args.command](args)


if __name__ == "__main__":
    main()
