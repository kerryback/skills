#!/usr/bin/env python3
"""Launch the classroom screen-sharing app.

Invoked by the `screenshare` skill. It:
  1. ensures the app environment (a venv in ~/.screenshare) exists,
  2. starts the FastAPI server on http://127.0.0.1:<port> (default 8030),
  3. opens a Cloudflare Quick Tunnel so students get an https:// link,
  4. opens the display page on the classroom computer.

The tunnel is not a convenience. Browsers only hand out a screen capture in a
secure context, so a plain http:// address on the campus LAN cannot work at
all; students need https, and the tunnel is what provides it.

Runs on Windows, macOS and Linux. The classroom computer only ever receives
video, so it needs nothing special of its own -- the screen capture happens on
the students' machines.

Usage:
  python3 scripts/skill_launch.py [--port 8030] [--no-tunnel] [--no-open]
  python3 scripts/skill_launch.py --install-cloudflared

On Windows, invoke it with `py -3` or `python` -- `python3` there is usually a
Microsoft Store stub that does nothing.

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = SKILL_DIR / "requirements.txt"

HOME_DIR = Path(os.environ.get("SCREENSHARE_HOME", Path.home() / ".screenshare"))
VENV_DIR = HOME_DIR / "venv"

IS_WINDOWS = os.name == "nt"

# Where we keep our own copy of cloudflared when it isn't installed system-wide.
# A classroom PC is usually locked down, so being able to run without an
# installer and without admin rights matters more than being tidy.
BIN_DIR = HOME_DIR / "bin"
OWN_CLOUDFLARED = BIN_DIR / ("cloudflared.exe" if IS_WINDOWS else "cloudflared")

RELEASE_BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download"

TUNNEL_URL = re.compile(r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com")

# An installed plugin directory may be read-only, and is replaced wholesale on
# the next update, so it should never collect __pycache__.
sys.dont_write_bytecode = True


def log(message: str) -> None:
    print(f"[screenshare] {message}", flush=True)


def ensure_venv() -> Path:
    python = VENV_DIR / ("Scripts" if os.name == "nt" else "bin") / (
        "python.exe" if os.name == "nt" else "python"
    )
    if python.exists():
        return python
    log("Creating the app environment + installing requirements (first run only)…")
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)], check=True)
    return python


def room_code() -> str:
    """A fixed code from the config file if there is one, else a fresh one."""
    try:
        with (HOME_DIR / "config.json").open() as fh:
            fixed = str(json.load(fh).get("code") or "").strip()
        if fixed:
            return fixed
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return f"{secrets.randbelow(9000) + 1000}"


def wait_up(base: str, timeout: float = 45.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/healthz", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True  # the server answered, whatever the status
        except Exception:
            time.sleep(0.4)
    return False


def post_json(url: str, payload: dict) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(request, timeout=5).read()


MIN_PYTHON = (3, 10)


def check() -> int:
    """Report whether this machine is ready, and what to do about it if not.

    Written for someone setting the plugin up for the first time on a machine
    that is not the author's. Every failure says what to run next, because
    "cloudflared: missing" on its own helps nobody.
    """
    rows: list[tuple[bool, str, str]] = []
    blocking = 0

    version = ".".join(str(n) for n in sys.version_info[:3])
    ok = sys.version_info >= MIN_PYTHON
    rows.append((ok, f"Python {version}", "" if ok else
                 f"Need {'.'.join(str(n) for n in MIN_PYTHON)} or newer. Install from python.org."))
    blocking += not ok

    venv_python = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / (
        "python.exe" if IS_WINDOWS else "python")
    if venv_python.exists():
        rows.append((True, f"App environment in {VENV_DIR}", ""))
    else:
        rows.append((True, "App environment not built yet",
                     "The first launch builds it automatically. Nothing to do."))

    binary = find_cloudflared()
    if binary:
        rows.append((True, f"cloudflared at {binary}", ""))
    else:
        rows.append((False, "cloudflared is missing", "\n".join(install_hint())))
        blocking += 1

    # config.json is optional, but a broken one is worth catching now rather
    # than having it silently ignored during a class.
    sys.path.insert(0, str(SKILL_DIR))
    from app import config  # noqa: E402  (stdlib only, so no venv needed)

    if not config.CONFIG_PATH.exists():
        rows.append((True, "No config file (fine)",
                     f"Room code is random each launch. To fix the code or add TURN, "
                     f"write {config.CONFIG_PATH}."))
    else:
        try:
            with config.CONFIG_PATH.open() as fh:
                json.load(fh)
            rows.append((True, f"Config at {config.CONFIG_PATH}", ""))
        except json.JSONDecodeError as exc:
            rows.append((False, f"Config at {config.CONFIG_PATH} is not valid JSON",
                         f"{exc}. The whole file is being ignored until this is fixed."))
            blocking += 1

    status = config.turn_status()
    if status["source"] == "none":
        rows.append((True, "No TURN configured",
                     "Fine until you find a room where video doesn't arrive. See the skill."))
    else:
        # Actually try the credentials rather than just noting they exist.
        config.warm_turn()
        status = config.turn_status()
        rows.append((status["configured"], f"TURN via {status['source']}",
                     status["error"]))
        blocking += not status["configured"]

    print("\nscreenshare readiness\n")
    for ok, label, detail in rows:
        print(f"  {'OK  ' if ok else 'FIX '} {label}")
        for line in (detail or "").splitlines():
            print(f"         {line}")
    print()
    if blocking:
        print(f"{blocking} thing{'s' if blocking > 1 else ''} to fix before running a class.\n")
    else:
        print("Ready. Launch it with no arguments to start.\n")
    return 1 if blocking else 0


def find_cloudflared() -> str | None:
    """A system-wide install first, then the copy we downloaded ourselves."""
    found = shutil.which("cloudflared")
    if found:
        return found
    return str(OWN_CLOUDFLARED) if OWN_CLOUDFLARED.exists() else None


def release_asset() -> str | None:
    """The cloudflared build for this machine, named as GitHub publishes it."""
    machine = platform.machine().lower()
    sixty_four = machine in ("amd64", "x86_64", "arm64", "aarch64")
    arm = machine in ("arm64", "aarch64")

    if IS_WINDOWS:
        return f"cloudflared-windows-{'amd64' if sixty_four else '386'}.exe"
    if sys.platform == "darwin":
        return f"cloudflared-darwin-{'arm64' if arm else 'amd64'}.tgz"
    if sys.platform.startswith("linux"):
        return f"cloudflared-linux-{'arm64' if arm else 'amd64'}"
    return None


def install_hint() -> list[str]:
    if IS_WINDOWS:
        manager = "winget install --id Cloudflare.cloudflared"
    elif sys.platform == "darwin":
        manager = "brew install cloudflared"
    else:
        manager = "your package manager (see the cloudflared docs)"
    return [
        f"  With admin rights:  {manager}",
        "  Without them:       rerun this launcher with --install-cloudflared,",
        f"                      which downloads it into {BIN_DIR} only.",
    ]


def install_cloudflared() -> str:
    """Download cloudflared into ~/.screenshare/bin.

    No installer and no admin rights: the binary lands in the instructor's own
    directory and is run by absolute path. That is what makes this usable on a
    locked-down classroom PC.
    """
    asset = release_asset()
    if asset is None:
        raise SystemExit(
            f"No cloudflared build for {sys.platform}/{platform.machine()}. "
            "Install it yourself and put it on PATH."
        )

    url = f"{RELEASE_BASE}/{asset}"
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Downloading cloudflared from {url} …")

    with tempfile.TemporaryDirectory() as work:
        downloaded = Path(work) / asset
        with urllib.request.urlopen(url, timeout=120) as response, downloaded.open("wb") as out:
            shutil.copyfileobj(response, out)

        if asset.endswith(".tgz"):
            with tarfile.open(downloaded) as archive:
                member = next(
                    (m for m in archive.getmembers() if m.isfile() and Path(m.name).name == "cloudflared"),
                    None,
                )
                if member is None:
                    raise SystemExit("That archive did not contain a cloudflared binary.")
                source = archive.extractfile(member)
                if source is None:
                    raise SystemExit("Could not read cloudflared out of the archive.")
                with source, OWN_CLOUDFLARED.open("wb") as out:
                    shutil.copyfileobj(source, out)
        else:
            shutil.copyfile(downloaded, OWN_CLOUDFLARED)

    if not IS_WINDOWS:
        OWN_CLOUDFLARED.chmod(0o755)

    log(f"cloudflared is in {OWN_CLOUDFLARED}")
    return str(OWN_CLOUDFLARED)


def start_tunnel(port: int, on_url) -> subprocess.Popen | None:
    """Run a Cloudflare Quick Tunnel and report the https URL it prints.

    Quick Tunnels need no Cloudflare account and no DNS: cloudflared dials out
    to Cloudflare and gets back a random trycloudflare.com hostname. The URL is
    new every launch, which is why the display page shows it rather than the
    instructor writing it down.
    """
    binary = find_cloudflared()
    if binary is None:
        log("cloudflared is not here, so there is no https link for students.")
        for line in install_hint():
            log(line)
        log("Students cannot share a screen over plain http, so this is required.")
        return None

    process = subprocess.Popen(
        [binary, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def reader() -> None:
        found = False
        for line in process.stdout or []:
            if not found:
                match = TUNNEL_URL.search(line)
                if match:
                    found = True
                    on_url(match.group(0))

    threading.Thread(target=reader, daemon=True).start()
    return process


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8030)
    parser.add_argument("--no-tunnel", action="store_true", help="local only; students cannot join")
    parser.add_argument("--no-open", action="store_true", help="start without opening the display")
    parser.add_argument(
        "--install-cloudflared",
        action="store_true",
        help="download cloudflared into ~/.screenshare/bin, then launch (no admin rights needed)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether this machine is set up, and what to fix, without launching",
    )
    args = parser.parse_args()

    if args.check:
        raise SystemExit(check())

    if args.install_cloudflared:
        install_cloudflared()

    python = ensure_venv()

    code = os.environ.get("SCREENSHARE_CODE") or room_code()
    display_key = secrets.token_urlsafe(12)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["SCREENSHARE_CODE"] = code
    env["SCREENSHARE_DISPLAY_KEY"] = display_key

    base = f"http://127.0.0.1:{args.port}"
    display_url = f"{base}/display?key={display_key}"

    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(args.port)],
        cwd=SKILL_DIR,
        env=env,
    )

    tunnel = None
    try:
        if not wait_up(base):
            raise SystemExit(
                f"The server did not come up on port {args.port}. If that port is "
                "in use, rerun with a different one, e.g. --port 8031."
            )

        if not args.no_tunnel:
            def announce(url: str) -> None:
                log(f"Students join at: {url}")
                try:
                    post_json(f"{base}/api/tunnel?key={display_key}", {"url": url})
                except Exception as exc:  # the link still works; only the display misses it
                    log(f"(could not tell the display about the tunnel: {exc})")

            log("Opening a Cloudflare tunnel…")
            tunnel = start_tunnel(args.port, announce)

        if not args.no_open:
            webbrowser.open(display_url)

        log(f"Display (classroom computer): {display_url}")
        log(f"Room code: {code}")
        log("The join link and code are on the display page — put it on the projector.")
        log("Leave this running for the whole class. Press Ctrl-C to stop.")
        server.wait()
    finally:
        for process in (tunnel, server):
            if process is not None and process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    main()
