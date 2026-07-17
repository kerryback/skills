#!/usr/bin/env python3
"""Launch Voiceover Builder and open it in the browser.

Invoked by the `voiceover` skill. It:
  1. ensures the app environment (venv) and the built frontend exist,
  2. starts the FastAPI app on http://127.0.0.1:<port> (default 8010),
  3. if a PDF is given, opens (or reopens) that deck and converts it, then
     deep-links the browser into it; otherwise opens the home screen, where the
     instructor picks an existing deck or uploads a new one.

Each deck lives in its own folder under {project}/.voiceover/decks/<deck-name>
(the project folder = --output-dir), so relaunching the same deck from the same
folder reopens it with its narration intact.

The finished MP4 and transcript are written straight to --output-dir (default: the
current working directory) each time a build completes, so the outputs sit in the
project folder where they are easy to find — there is no in-app download.

Usage:
  python scripts/skill_launch.py [/path/to/deck.pdf] [--output-dir DIR] [--port 8010]

Runs in the foreground and keeps the server alive; stop it with Ctrl-C.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
FRONTEND = REPO / "frontend"

# Runtime state lives OUTSIDE the skill directory so that (a) reinstalling or
# updating the skill never wipes projects, and (b) the package source stays clean
# for repackaging. Override the data location with DATA_DIR in the environment.
# The Python environment is shared and built once, in the user's home.
VENV_DIR = Path(os.environ.get("VOICEOVER_HOME", Path.home() / ".voiceover")) / "venv"


def log(msg):
    print(f"[voiceover] {msg}", flush=True)


def ensure_backend_venv() -> Path:
    py = VENV_DIR / "bin" / "python"
    if py.exists():
        return py
    log("Creating the app environment + installing requirements (first run only)…")
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-q", "-r",
                    str(BACKEND / "requirements.txt")], check=True)
    return py


def ensure_frontend_built():
    # The published package ships a prebuilt frontend/dist, so this is a no-op in
    # normal use. It only rebuilds when running from source with dist removed.
    if (FRONTEND / "dist" / "index.html").exists():
        return
    log("Building the frontend (requires Node/npm)…")
    subprocess.run(["npm", "install"], cwd=FRONTEND, check=True)
    subprocess.run(["npm", "run", "build"], cwd=FRONTEND, check=True)


def preflight():
    """Surface missing prerequisites up front, with a clear message, instead of a
    mid-build crash. Neither is fatal: narration can be drafted without Quarto or a
    key — they're only needed for the Generate/video step."""
    if shutil.which("quarto") is None:
        log("WARNING: 'quarto' not found on PATH. The deck can't be rendered into a "
            "video until Quarto is installed (https://quarto.org/docs/get-started/, "
            "or Help -> Run Setup in Academic Studio). You can still draft and edit "
            "narration now.")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        log("WARNING: ELEVENLABS_API_KEY not found in the environment. The Generate "
            "step (text-to-speech) will fail until it is set (a free key from "
            "elevenlabs.io). Narration itself is written by Claude Code and needs "
            "no key.")


def wait_up(base: str, timeout: float = 45.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(base + "/api/projects", timeout=2)
            return True
        except urllib.error.HTTPError:
            return True  # server answered (any status) = up
        except Exception:
            time.sleep(0.5)
    return False


def create_project(base: str, pdf: Path) -> str:
    body = json.dumps({"path": str(pdf), "name": pdf.stem}).encode()
    req = urllib.request.Request(base + "/api/projects/from-path", data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["id"]


def wait_converted(base: str, pid: str, timeout: float = 180.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with urllib.request.urlopen(f"{base}/api/projects/{pid}", timeout=10) as resp:
            state = json.load(resp)["state"]
        if state == "converting_failed":
            raise SystemExit("Conversion failed — is the file a real PDF slide deck?")
        if state not in ("uploaded", "converting"):
            return
        time.sleep(1.0)
    log("Still converting; opening anyway.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", nargs="?",
                    help="path to a PDF slide deck. Omit to open the home screen, "
                         "where you can pick an existing deck or upload a new one.")
    ap.add_argument("--output-dir", default=os.getcwd(),
                    help="where finished .mp4/.txt are saved (default: cwd)")
    ap.add_argument("--port", type=int, default=8010)
    args = ap.parse_args()

    pdf = None
    if args.pdf:
        pdf = Path(args.pdf).expanduser().resolve()
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            raise SystemExit(f"Not a PDF file: {pdf}")
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    # Per-project data (each deck's narration/audio/working files) lives beside the
    # project, in {project}/.voiceover/decks/<name>, so a project folder is
    # self-contained. Finished MP4s + transcripts go to the project folder itself.
    data_dir = Path(os.environ.get("DATA_DIR") or (output_dir / ".voiceover")).expanduser()

    py = ensure_backend_venv()
    ensure_frontend_built()
    preflight()

    env = dict(os.environ)
    env["VOICEOVER_OUTPUT_DIR"] = str(output_dir)
    # Per-project decks + working files live in {project}/.voiceover.
    env["DATA_DIR"] = str(data_dir)
    # Don't scatter __pycache__ into the (possibly read-only / packaged) skill dir.
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    base = f"http://127.0.0.1:{args.port}"
    log(f"Starting the app on {base} …")
    server = subprocess.Popen(
        [str(py), "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
         "--port", str(args.port)],
        cwd=BACKEND, env=env)
    try:
        if not wait_up(base):
            raise SystemExit(
                f"Server did not come up on port {args.port}. If that port is in "
                "use, rerun with a different one, e.g. --port 8011.")
        if pdf is not None:
            pid = create_project(base, pdf)
            log(f"Opened deck '{pid}' from {pdf.name}. Converting…")
            wait_converted(base, pid)
            url = f"{base}/?project={pid}"
        else:
            url = base
            log("No deck given — opening the home screen (pick a deck or upload one).")
        webbrowser.open(url)
        log(f"Open: {url}")
        log(f"Finished MP4 + transcript will be saved to: {output_dir}")
        log("Leave this running while you work. Press Ctrl-C to stop the app.")
        server.wait()
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
