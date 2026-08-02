#!/usr/bin/env python3
"""Launch the classroom polling app.

Invoked by the `polls` skill. It:
  1. ensures the app environment (a venv in ~/.polls) exists,
  2. starts the FastAPI server on http://127.0.0.1:<port> (default 8050),
  3. opens a Cloudflare Quick Tunnel so students get an https:// link,
  4. opens the display page on the classroom computer.

The tunnel is what students actually connect to. A campus LAN address usually
won't reach student wifi, and even where it would, a random https hostname is
easier to put on a projector than an IP address.

Runs on Windows, macOS and Linux.

Usage:
  python3 scripts/skill_launch.py [--poll FILE] [--port 8050] [--no-open]
  python3 scripts/skill_launch.py --check
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

HOME_DIR = Path(os.environ.get("POLLS_HOME", Path.home() / ".polls"))
VENV_DIR = HOME_DIR / "venv"

IS_WINDOWS = os.name == "nt"
MIN_PYTHON = (3, 10)

BIN_DIR = HOME_DIR / "bin"
OWN_CLOUDFLARED = BIN_DIR / ("cloudflared.exe" if IS_WINDOWS else "cloudflared")
RELEASE_BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download"

TUNNEL_URL = re.compile(r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com")

sys.dont_write_bytecode = True


def log(message: str) -> None:
    print(f"[polls] {message}", flush=True)


def ensure_venv() -> Path:
    python = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / (
        "python.exe" if IS_WINDOWS else "python"
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
    try:
        with (HOME_DIR / "config.json").open() as fh:
            fixed = str(json.load(fh).get("code") or "").strip()
        if fixed:
            return fixed
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    return f"{secrets.randbelow(9000) + 1000}"


# --- cloudflared ------------------------------------------------------------


def find_cloudflared() -> str | None:
    found = shutil.which("cloudflared")
    if found:
        return found
    return str(OWN_CLOUDFLARED) if OWN_CLOUDFLARED.exists() else None


def release_asset() -> str | None:
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
    """Download cloudflared into ~/.polls/bin -- no installer, no admin rights."""
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
                    (m for m in archive.getmembers()
                     if m.isfile() and Path(m.name).name == "cloudflared"),
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


# --- readiness --------------------------------------------------------------


def check(poll: str | None = None) -> int:
    """Say whether this machine is set up, and what to do about anything missing."""
    rows: list[tuple[bool, str, str]] = []
    blocking = 0

    version = ".".join(str(n) for n in sys.version_info[:3])
    ok = sys.version_info >= MIN_PYTHON
    rows.append((ok, f"Python {version}", "" if ok else
                 f"Need {'.'.join(str(n) for n in MIN_PYTHON)} or newer. Install from python.org."))
    blocking += not ok

    venv_python = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / (
        "python.exe" if IS_WINDOWS else "python")
    rows.append((True, f"App environment in {VENV_DIR}" if venv_python.exists()
                 else "App environment not built yet",
                 "" if venv_python.exists() else "The first launch builds it. Nothing to do."))

    binary = find_cloudflared()
    if binary:
        rows.append((True, f"cloudflared at {binary}", ""))
    else:
        rows.append((False, "cloudflared is missing", "\n".join(install_hint())))
        blocking += 1

    if poll:
        sys.path.insert(0, str(SKILL_DIR))
        from app import deck as deck_mod  # noqa: E402  (stdlib only)

        try:
            loaded = deck_mod.load(poll)
            kinds = ", ".join(sorted({q["type"] for q in loaded["questions"]}))
            rows.append((True, f"Poll file: {len(loaded['questions'])} questions ({kinds})", ""))
        except deck_mod.DeckError as exc:
            rows.append((False, f"Poll file {poll} has problems", str(exc)))
            blocking += 1

    print("\npolls readiness\n")
    for ok, label, detail in rows:
        print(f"  {'OK  ' if ok else 'FIX '} {label}")
        for line in (detail or "").splitlines():
            print(f"         {line}")
    print()
    print("Ready." if not blocking
          else f"{blocking} thing{'s' if blocking > 1 else ''} to fix.")
    print()
    return 1 if blocking else 0


# --- running ----------------------------------------------------------------


def wait_up(base: str, timeout: float = 45.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/healthz", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            time.sleep(0.4)
    return False


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def start_tunnel(port: int, on_url) -> subprocess.Popen | None:
    binary = find_cloudflared()
    if binary is None:
        log("cloudflared is not here, so students have no link to open.")
        for line in install_hint():
            log(line)
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
    parser.add_argument("--poll", help="path to the poll file to load at startup")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--no-tunnel", action="store_true", help="local only; students can't join")
    parser.add_argument("--no-open", action="store_true", help="don't open the display")
    parser.add_argument("--install-cloudflared", action="store_true",
                        help="download cloudflared into ~/.polls/bin, then launch")
    parser.add_argument("--check", action="store_true",
                        help="report what is set up and what to fix, without launching")
    args = parser.parse_args()

    if args.check:
        raise SystemExit(check(args.poll))

    if args.install_cloudflared:
        install_cloudflared()

    python = ensure_venv()

    code = os.environ.get("POLLS_CODE") or room_code()
    display_key = secrets.token_urlsafe(12)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["POLLS_CODE"] = code
    env["POLLS_DISPLAY_KEY"] = display_key

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
                "in use, rerun with a different one, e.g. --port 8051."
            )

        if args.poll:
            try:
                loaded = post_json(
                    f"{base}/api/deck?key={display_key}",
                    {"path": str(Path(args.poll).expanduser().resolve())},
                )
                log(f"Loaded \"{loaded['title']}\" — {loaded['questions']} questions")
            except urllib.error.HTTPError as exc:
                body = exc.read().decode(errors="replace")
                log(f"Could not load that poll file: {body}")
            except Exception as exc:
                log(f"Could not load that poll file: {exc}")

        if not args.no_tunnel:
            def announce(url: str) -> None:
                log(f"Students answer at: {url}")
                try:
                    post_json(f"{base}/api/tunnel?key={display_key}", {"url": url})
                except Exception as exc:
                    log(f"(could not tell the display about the tunnel: {exc})")

            log("Opening a Cloudflare tunnel…")
            tunnel = start_tunnel(args.port, announce)

        if not args.no_open:
            webbrowser.open(display_url)

        log(f"Display (classroom computer): {display_url}")
        log(f"Room code: {code}")
        log("Leave this running for the whole class. Press Ctrl-C to stop.")
        server.wait()
    finally:
        for process in (tunnel, server):
            if process is not None and process.poll() is None:
                process.terminate()


if __name__ == "__main__":
    main()
