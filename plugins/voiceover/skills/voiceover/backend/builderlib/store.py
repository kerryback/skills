"""Per-deck file I/O: slides.json, config.json, meta.json, paths.

A deck folder holds only what the app generates — the parsed slides, the page
PNGs, the TTS audio and the settings. The deck itself (the .qmd/.pptx and its
PDF) stays where the instructor keeps it; meta.json records the paths.
"""
import hashlib
import json
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
    # Expression controls. These match ElevenLabs' own server-side defaults, so
    # they change nothing until the instructor moves them — the point of sending
    # them is that the knobs become reachable.
    "style": 0.0,
    "use_speaker_boost": True,
    "speed": 1.0,
}


def pdir(pid: str) -> Path:
    return config.project_dir(pid)


def slides_path(pid: str) -> Path:
    return pdir(pid) / "slides.json"


def config_path(pid: str) -> Path:
    return pdir(pid) / "config.json"


def meta_path(pid: str) -> Path:
    return pdir(pid) / "meta.json"


def audio_dir(pid: str) -> Path:
    return pdir(pid) / "audio"


def slides_dir(pid: str) -> Path:
    return pdir(pid) / "slides"


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


# --------------------------------------------------------------------------- #
# Slides (parsed from the source deck)
# --------------------------------------------------------------------------- #
def read_slides(pid: str) -> dict:
    p = slides_path(pid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return {"slides": []}
    return {"slides": []}


def write_slides(pid: str, slides: list) -> None:
    slides_path(pid).write_text(
        json.dumps({"slides": slides}, indent=2, ensure_ascii=False),
        encoding="utf-8")


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
def read_config(pid: str) -> dict:
    p = config_path(pid)
    cfg = dict(DEFAULT_CONFIG)
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except ValueError:
            pass
    return cfg


def write_config(pid: str, cfg: dict) -> dict:
    merged = read_config(pid)
    merged.update({k: v for k, v in cfg.items() if v is not None})
    config_path(pid).write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    return merged


# --------------------------------------------------------------------------- #
# Meta
# --------------------------------------------------------------------------- #
def read_meta(pid: str) -> dict:
    p = meta_path(pid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def update_meta(pid: str, **fields) -> None:
    db.update_project(pid, **fields)


def source_paths(pid: str) -> tuple:
    """(source, pdf) as Paths, or (None, None) if the deck has no record yet."""
    meta = read_meta(pid)
    src, pdf = meta.get("source_path"), meta.get("pdf_path")
    return (Path(src) if src else None, Path(pdf) if pdf else None)


def _mtime(path: Path | None) -> float:
    try:
        return path.stat().st_mtime if path else 0.0
    except OSError:
        return 0.0


def record_files(pid: str) -> None:
    """Snapshot the two files' mtimes, so a later edit shows up as changed."""
    src, pdf = source_paths(pid)
    db.update_project(pid, source_mtime=_mtime(src), pdf_mtime=_mtime(pdf))


def file_status(pid: str) -> dict:
    """Whether either file has been touched since the last load, and whether the
    PDF predates the deck it is supposed to have come from — the quiet failure
    where new notes get narrated over old slides."""
    meta = read_meta(pid)
    src, pdf = source_paths(pid)
    src_now, pdf_now = _mtime(src), _mtime(pdf)
    return {
        "source": src.name if src else "",
        "pdf": pdf.name if pdf else "",
        "source_dir": str(src.parent) if src else "",
        "source_missing": bool(src and not src.is_file()),
        "pdf_missing": bool(pdf and not pdf.is_file()),
        "source_changed": bool(src_now and src_now > meta.get("source_mtime", 0) + 0.5),
        "pdf_changed": bool(pdf_now and pdf_now > meta.get("pdf_mtime", 0) + 0.5),
        # A minute of slack: exporting the PDF right after saving the deck is the
        # normal order, and clock resolution shouldn't raise a false alarm.
        "pdf_older_than_source": bool(src_now and pdf_now and pdf_now < src_now - 60),
    }


# --------------------------------------------------------------------------- #
# Build signature — is the rendered video still the one these notes describe?
# --------------------------------------------------------------------------- #
def build_signature(pid: str) -> str:
    """A sha over everything that determines the output: every slide's notes, in
    order, plus the voice settings. Comparing it to the signature stored at build
    time answers "is this video current?" without tracking edits one by one."""
    slides = sorted(read_slides(pid).get("slides", []), key=lambda s: s["index"])
    cfg = read_config(pid)
    parts = [f"{s['index']}:{s.get('notes', '')}" for s in slides]
    parts += [f"{k}={cfg.get(k)}" for k in sorted(DEFAULT_CONFIG)]
    return hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()


def is_stale(pid: str) -> bool:
    proj = db.get_project(pid)
    if not proj or proj.get("state") != "built":
        return False
    return proj.get("build_sig", "") != build_signature(pid)


def set_state(pid: str, state: str, log: str = None) -> None:
    fields = {"state": state}
    if log is not None:
        fields["log"] = log
    db.update_project(pid, **fields)
