"""Per-project file I/O: narration.json, config.json, meta.json, paths."""
import json
import shutil
from pathlib import Path

from . import config, db

DEFAULT_CONFIG = {
    # ElevenLabs voice + model. "EXAVITQu4vr4xnSDxMaL" is "Sarah"; the instructor
    # picks a real one (including a cloned voice) from the account's voice list
    # in the UI.
    "voice_id": "EXAVITQu4vr4xnSDxMaL",
    # v3 is the expressive model. The v2 family is deliberately even-toned, which
    # on a long narrated lecture comes out sounding flat — that is the model, not
    # the account tier, and not something a paid upgrade changes.
    "model": "eleven_v3",
    "stability": 0.5,
    "similarity_boost": 0.75,
    # Expression controls, exposed in the Generate step. These match ElevenLabs'
    # own server-side defaults, so they change nothing until the instructor moves
    # them — the point of sending them is that the knobs become reachable.
    "style": 0.0,
    "use_speaker_boost": True,
    "speed": 1.0,
}


def pdir(pid: str) -> Path:
    return config.project_dir(pid)


def narration_path(pid: str) -> Path:
    return pdir(pid) / "narration.json"


def config_path(pid: str) -> Path:
    return pdir(pid) / "config.json"


def meta_path(pid: str) -> Path:
    return pdir(pid) / "meta.json"


def deck_dir(pid: str) -> Path:
    return pdir(pid) / "deck"


def audio_dir(pid: str) -> Path:
    return pdir(pid) / "audio"


def output_base(pid: str) -> str:
    """Filename stem for a deck's visible outputs in the project folder."""
    return pid


def video_path(pid: str) -> Path:
    """The finished MP4. When launched by the skill it lives in the instructor's
    project folder (config.OUTPUT_DIR) so the output is easy to find; otherwise it
    stays inside the deck folder."""
    if config.OUTPUT_DIR:
        return Path(config.OUTPUT_DIR).expanduser() / f"{output_base(pid)}.mp4"
    return pdir(pid) / "video.mp4"


def transcript_path(pid: str) -> Path:
    if config.OUTPUT_DIR:
        return Path(config.OUTPUT_DIR).expanduser() / f"{output_base(pid)}.txt"
    return pdir(pid) / "transcript.txt"


def slides_dir(pid: str) -> Path:
    return pdir(pid) / "slides"


def references_dir(pid: str) -> Path:
    return pdir(pid) / "references"


def list_references(pid: str) -> list:
    """Teacher-uploaded reference files the narration agent may read."""
    return _list_files(references_dir(pid))


def _list_files(d: Path) -> list:
    if not d.exists():
        return []
    return [{"name": p.name, "size": p.stat().st_size}
            for p in sorted(d.iterdir()) if p.is_file()]


def hashes_path(pid: str) -> Path:
    return pdir(pid) / "audio_hashes.json"


def fingerprints_path(pid: str) -> Path:
    """Per-slide content shas from the last ingest. Kept out of narration.json so
    the narration payload the agent reads stays about narration."""
    return pdir(pid) / "fingerprints.json"


def read_fingerprints(pid: str) -> list:
    p = fingerprints_path(pid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("slides", [])
        except Exception:
            return []
    return []


def write_fingerprints(pid: str, slides: list) -> None:
    fingerprints_path(pid).write_text(
        json.dumps({"slides": slides}, indent=2), encoding="utf-8")


def remap_audio(pid: str, pairs: dict) -> None:
    """Move each carried-over slide's MP3 and audio hash to its new index.

    Both are keyed by slide index, so a reattached deck that inserts or drops a
    page would otherwise leave every later slide holding its neighbour's audio —
    consistent with itself, and wrong. Anything no new slide claims is dropped, so
    a deleted slide's audio does not linger.

    Staged through a temp dir because the renames overlap: shifting slides 3..n
    down by one walks each file onto its neighbour.
    """
    adir = audio_dir(pid)
    old_hashes = {}
    if hashes_path(pid).exists():
        try:
            old_hashes = json.loads(hashes_path(pid).read_text(encoding="utf-8"))
        except Exception:
            old_hashes = {}
    if not adir.exists() and not old_hashes:
        return

    staged = adir.parent / "audio.remap"
    shutil.rmtree(staged, ignore_errors=True)
    staged.mkdir(parents=True, exist_ok=True)
    new_hashes = {}
    for new_i, old_i in sorted(pairs.items()):
        src = adir / f"slide-{old_i + 1:03d}.mp3"
        if src.exists():
            shutil.copyfile(src, staged / f"slide-{new_i + 1:03d}.mp3")
        h = old_hashes.get(str(old_i))
        if h:
            new_hashes[str(new_i)] = h

    shutil.rmtree(adir, ignore_errors=True)
    staged.rename(adir)
    hashes_path(pid).write_text(json.dumps(new_hashes, indent=2), encoding="utf-8")


def set_review(pid: str, review: dict | None) -> None:
    """Record (or clear) what the last reattach changed, for the UI banner."""
    meta = read_meta(pid)
    if review:
        meta["review"] = review
    else:
        meta.pop("review", None)
    meta_path(pid).write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                              encoding="utf-8")


def read_review(pid: str) -> dict:
    return read_meta(pid).get("review") or {}


def clear_flags(pid: str, indexes: list | None = None) -> int:
    """Drop the `change` flag from slides the instructor (or the agent) has dealt
    with. `indexes` None clears every flag. Returns how many were cleared."""
    data = read_narration(pid)
    wanted = None if indexes is None else set(indexes)
    cleared = 0
    for s in data.get("slides", []):
        if s.get("change") and (wanted is None or s["index"] in wanted):
            s.pop("change", None)
            cleared += 1
    if cleared:
        write_narration(pid, data)
        if not any(s.get("change") for s in data.get("slides", [])):
            set_review(pid, None)
    return cleared


def read_narration(pid: str) -> dict:
    p = narration_path(pid)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"slides": []}


def write_narration(pid: str, data: dict) -> None:
    narration_path(pid).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_config(pid: str) -> dict:
    p = config_path(pid)
    cfg = dict(DEFAULT_CONFIG)
    if p.exists():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    return cfg


def write_config(pid: str, cfg: dict) -> None:
    merged = read_config(pid)
    merged.update({k: v for k, v in cfg.items() if v is not None})
    config_path(pid).write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return merged


def read_meta(pid: str) -> dict:
    p = meta_path(pid)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def set_deck_name(pid: str, name: str) -> None:
    meta = read_meta(pid)
    meta["deck_name"] = name
    meta_path(pid).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def deck_name(pid: str) -> str:
    return read_meta(pid).get("deck_name", "deck")


def set_state(pid: str, state: str, log: str = None) -> None:
    fields = {"state": state}
    if log is not None:
        fields["log"] = log
    db.update_project(pid, **fields)


def touch_stale(pid: str) -> None:
    proj = db.get_project(pid)
    if proj and proj["state"] == "built":
        db.update_project(pid, stale=True)
