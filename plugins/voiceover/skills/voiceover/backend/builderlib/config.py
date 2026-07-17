"""Central configuration loaded from backend/.env."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# DATA_DIR is the app's home (the launcher points it at ~/.voiceover). Each deck
# lives in its own folder under DATA_DIR/decks, named after the deck, so relaunching
# the same deck reopens it with its narration and video intact.
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = (BACKEND_DIR / DATA_DIR).resolve()
PROJECTS_DIR = DATA_DIR / "decks"

# Narration is written and revised by the Claude Code agent that launches this
# skill (it edits via the narration API), so the app itself makes no LLM calls
# and needs no Anthropic key. Only ElevenLabs (TTS) is required.
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

# When set (by the skill launcher = the instructor's working directory), each
# finished build copies <name>.mp4 and <name>.txt there.
OUTPUT_DIR = os.environ.get("VOICEOVER_OUTPUT_DIR", "")

# Parallel ElevenLabs TTS requests during a build. ElevenLabs caps concurrent
# requests per account tier; 5 matches this account's limit.
TTS_CONCURRENCY = int(os.environ.get("TTS_CONCURRENCY", "5"))
# Parallel ffmpeg slide-segment encodes during video render (CPU-bound).
VIDEO_CONCURRENCY = int(os.environ.get("VIDEO_CONCURRENCY", "4"))

# React SPA build output (optional; served at / when present).
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"

DATA_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def project_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id
