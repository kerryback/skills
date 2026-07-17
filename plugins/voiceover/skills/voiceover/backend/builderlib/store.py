"""Per-project file I/O: narration.json, config.json, meta.json, paths."""
import json
from pathlib import Path

from . import config, db

DEFAULT_CONFIG = {
    # ElevenLabs voice + model. "EXAVITQu4vr4xnSDxMaL" is "Sarah"; the instructor
    # picks a real one (including a cloned voice) from the account's voice list
    # in the UI.
    "voice_id": "EXAVITQu4vr4xnSDxMaL",
    "model": "eleven_multilingual_v2",
    "stability": 0.5,
    "similarity_boost": 0.75,
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
