#!/usr/bin/env python3
"""Launch the participation app and open it.

Invoked by the `participation` skill. It:
  1. ensures the app environment (a venv in ~/.participation) exists,
  2. starts the FastAPI app on http://127.0.0.1:<port> (default 8020),
  3. opens it in Academic Studio if Studio is listening, otherwise in the
     system browser.

Courses, rosters and extracted photos live in ~/.participation/data so they
survive a plugin update. Evaluations are not kept there -- each course writes
participation.csv into the folder the instructor chose for it.

Usage:
  python3 scripts/skill_launch.py [--port 8020] [--no-open]

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
REQUIREMENTS = SKILL_DIR / "requirements.txt"

HOME_DIR = Path(os.environ.get("PARTICIPATION_HOME", Path.home() / ".participation"))
VENV_DIR = HOME_DIR / "venv"

# Set before importing anything from the skill: an installed plugin directory
# may be read-only, and is replaced wholesale on the next update, so it should
# never collect __pycache__.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL_DIR))
from app import inapp  # noqa: E402  (needs SKILL_DIR on the path first)


def log(message: str) -> None:
    print(f"[participation] {message}", flush=True)


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
    subprocess.run(
        [str(python), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)], check=True
    )
    return python


def wait_up(base: str, timeout: float = 45.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True  # the server answered, whatever the status
        except Exception:
            time.sleep(0.4)
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument(
        "--no-open", action="store_true", help="start the server without opening it"
    )
    args = parser.parse_args()

    python = ensure_venv()

    env = dict(os.environ)
    # Keep __pycache__ out of the installed skill directory, which may be
    # read-only or replaced wholesale on the next plugin update.
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    base = f"http://127.0.0.1:{args.port}"
    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(python), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(args.port)],
        cwd=SKILL_DIR,
        env=env,
    )
    try:
        if not wait_up(base):
            raise SystemExit(
                f"The server did not come up on port {args.port}. If that port is "
                "in use, rerun with a different one, e.g. --port 8021."
            )

        if not args.no_open:
            if inapp.publish_url(base):
                log("Opening in Academic Studio…")
            else:
                webbrowser.open(base)
        log(f"Open: {base}")
        log(f"Courses and rosters are stored in {HOME_DIR / 'data'}")
        log("Leave this running while you evaluate. Press Ctrl-C to stop the app.")
        server.wait()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
