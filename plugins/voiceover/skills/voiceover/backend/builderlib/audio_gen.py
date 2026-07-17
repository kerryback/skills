"""Per-slide TTS audio generation.

Parses a rendered reveal HTML deck's notes into narration.json and synthesizes
one ElevenLabs MP3 per narrated slide, parameterized by voice_id + model +
voice settings. Re-synthesizes only slides whose narration text OR voice
settings changed since the last build (a per-slide sha256 map is kept in the
project dir, keyed on narration + voice signature).
"""
import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from . import config

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from converters import generate_audio_ref as gaudio  # noqa: E402

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
OUTPUT_FORMAT = "mp3_44100_128"


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _voice_sig(voice_id: str, model: str, stability, similarity_boost) -> str:
    """A signature of everything besides the text that affects the audio, so a
    voice/model/settings change re-synthesizes even when narration is unchanged."""
    return f"{voice_id}|{model}|{stability}|{similarity_boost}"


def synthesize(text: str, out_path: Path, voice_id: str, model: str,
               stability: float = 0.5, similarity_boost: float = 0.75) -> None:
    """Stream one ElevenLabs MP3 to out_path. Reads ELEVENLABS_API_KEY."""
    if not config.ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY is not set (put it in backend/.env).")
    url = ELEVEN_TTS_URL.format(voice_id=voice_id)
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY, "accept": "audio/mpeg"}
    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
        },
    }
    params = {"output_format": OUTPUT_FORMAT}
    with httpx.stream("POST", url, headers=headers, json=payload, params=params,
                      timeout=120.0) as response:
        if response.status_code != 200:
            body = response.read().decode("utf-8", "replace")
            raise RuntimeError(f"ElevenLabs TTS error ({response.status_code}): {body[:300]}")
        with open(out_path, "wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)


def generate(deck_html: Path, audio_dir: Path, narration_json: Path,
             hashes_path: Path, voice_id: str, model: str,
             stability: float = 0.5, similarity_boost: float = 0.75,
             progress=None) -> dict:
    """Parse deck HTML, (re)synthesize changed slides, write manifest + narration.

    progress: optional callable(done, total, message).
    Returns {"total": int, "narrated": int, "synthesized": int, "skipped": int}.
    """
    slides = gaudio.parse_deck(deck_html.read_text(encoding="utf-8"))

    narration_json.write_text(
        json.dumps({"slides": slides}, indent=2, ensure_ascii=False), encoding="utf-8")

    old_hashes = {}
    if hashes_path.exists():
        try:
            old_hashes = json.loads(hashes_path.read_text(encoding="utf-8"))
        except Exception:
            old_hashes = {}

    audio_dir.mkdir(parents=True, exist_ok=True)
    narrated = [s for s in slides if s["narration"]]
    total = len(narrated)
    manifest = []
    new_hashes = {}
    skipped = 0
    tasks = []  # (slide, out_path) needing (re)synthesis

    sig = _voice_sig(voice_id, model, stability, similarity_boost)

    # First pass: build the manifest + hash map and decide which slides to render.
    for s in slides:
        entry = {"index": s["index"], "file": None,
                 "words": len(s["narration"].split())}
        if s["narration"]:
            filename = f"slide-{s['index']:03d}.mp3"
            out_path = audio_dir / filename
            entry["file"] = filename
            h = _sha(s["narration"] + "\x00" + sig)
            new_hashes[str(s["index"])] = h
            changed = old_hashes.get(str(s["index"])) != h
            if out_path.exists() and not changed:
                skipped += 1
            else:
                tasks.append((s, out_path))
        manifest.append(entry)

    # Second pass: synthesize the changed slides concurrently.
    lock = threading.Lock()
    done = skipped
    if progress:
        progress(done, total, "Generating audio")

    def _render(task):
        nonlocal done
        s, out_path = task
        synthesize(s["narration"], out_path, voice_id, model,
                   stability, similarity_boost)
        with lock:
            done += 1
            if progress:
                progress(done, total, f"Slide {s['index'] + 1} audio ready")

    if tasks:
        workers = max(1, min(config.TTS_CONCURRENCY, len(tasks)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = [ex.submit(_render, t) for t in tasks]
            for f in as_completed(futures):
                exc = f.exception()
                if exc:
                    raise exc

    synthesized = len(tasks)

    (audio_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    hashes_path.write_text(json.dumps(new_hashes, indent=2), encoding="utf-8")
    return {"total": len(slides), "narrated": total,
            "synthesized": synthesized, "skipped": skipped}
