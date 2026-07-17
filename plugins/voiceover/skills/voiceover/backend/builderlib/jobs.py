"""Background jobs: conversion and build (render + TTS + video).
Each runs in a thread and reports progress via events.

Narration is not drafted here: the Claude Code agent that launches the skill
writes and revises it through the narration API. Conversion leaves each slide
with empty narration for the agent (and the instructor) to fill in."""
import threading
import traceback
from pathlib import Path

from . import audio_gen, config, convert, db, events, store, video_gen


def _run_bg(fn, pid, *args):
    def wrapper():
        events.start(pid)
        try:
            fn(pid, *args)
        except Exception as e:
            log = f"{e}\n{traceback.format_exc()}"
            store.set_state(pid, _fail_state(db.get_project(pid)), log=log)
            events.emit(pid, "error", db.get_project(pid)["state"], message=str(e))
        finally:
            events.finish(pid)
    threading.Thread(target=wrapper, daemon=True).start()


def _fail_state(proj) -> str:
    state = proj["state"] if proj else ""
    mapping = {
        "converting": "converting_failed",
        "building": "building_failed",
    }
    return mapping.get(state, f"{state}_failed")


# --------------------------------------------------------------------------- #
# Conversion
# --------------------------------------------------------------------------- #
def start_conversion(pid: str, source_path: Path, source_type: str):
    _run_bg(_convert, pid, source_path, source_type)


def _convert(pid: str, source_path: Path, source_type: str):
    store.set_state(pid, "converting")
    events.emit(pid, "convert", "converting", 0, 1, "Converting upload")
    # Preserve narration when re-ingesting a deck that already has a script:
    # keep each slide's text by index so an edited deck doesn't lose its narration.
    prior = {}
    try:
        for s in store.read_narration(pid).get("slides", []):
            if s.get("narration"):
                prior[s["index"]] = s["narration"]
    except Exception:
        pass
    had_video = store.video_path(pid).exists()

    result = convert.convert(pid, source_path, source_type)
    store.set_deck_name(pid, result["deck_name"])
    slides = result["slides"]
    for s in slides:
        if prior.get(s["index"]):
            s["narration"] = prior[s["index"]]
    store.write_narration(pid, {"slides": slides})
    # Seed config if absent.
    if not store.config_path(pid).exists():
        store.write_config(pid, {})
    # If this deck already had a rendered video, re-ingesting invalidates it.
    if had_video:
        db.update_project(pid, stale=True)
    store.set_state(pid, "converted")
    events.emit(pid, "convert", "converted", 1, 1,
                f"Converted {len(slides)} slides")


# --------------------------------------------------------------------------- #
# Build (render + TTS + video)
# --------------------------------------------------------------------------- #
def start_build(pid: str):
    _run_bg(_build, pid)


def _build(pid: str):
    store.set_state(pid, "building")
    name = store.deck_name(pid)
    deck_dir = store.deck_dir(pid)
    qmd = deck_dir / f"{name}.qmd"
    slides = store.read_narration(pid)["slides"]
    narrations = [s.get("narration", "") for s in sorted(slides, key=lambda s: s["index"])]

    # 1. Inject narration into the deck qmd notes.
    events.emit(pid, "build", "building", 0, 4, "Writing narration into deck")
    if qmd.exists():
        convert.inject_narration_into_qmd(qmd, narrations)
        # 2. Render.
        events.emit(pid, "build", "building", 1, 4, "Rendering deck (quarto)")
        html_path = convert.render_qmd(qmd)
    else:
        # Reveal .html source with no qmd: use the html as-is.
        html_path = deck_dir / f"{name}.html"
        events.emit(pid, "build", "building", 1, 4, "Using provided reveal HTML")

    # 3. TTS for changed slides.
    events.emit(pid, "build", "building", 2, 4, "Generating audio")
    cfg = store.read_config(pid)

    def prog(done, tot, msg):
        events.emit(pid, "build", "building", 2, 4, f"{msg} ({done}/{tot})")

    stats = audio_gen.generate(
        html_path, store.audio_dir(pid), store.narration_path(pid),
        store.hashes_path(pid), cfg["voice_id"], cfg["model"],
        cfg.get("stability", 0.5), cfg.get("similarity_boost", 0.75),
        progress=prog)

    # 4. Render the video straight into the instructor's project folder (see
    #    store.video_path / store.transcript_path), so the outputs are easy to find.
    def vprog(done, tot, msg):
        events.emit(pid, "build", "building", 3, 4, f"{msg} ({done}/{tot})")

    events.emit(pid, "build", "building", 3, 4, "Rendering video")
    store.video_path(pid).parent.mkdir(parents=True, exist_ok=True)
    video_gen.generate(pid, progress=vprog)

    # Snapshot a narration transcript matched to this build (also in the folder).
    _write_transcript(pid)

    _announce_outputs(pid)

    db.update_project(pid, stale=False)
    store.set_state(pid, "built")
    events.emit(pid, "build", "built", 4, 4,
                f"Built ({stats['synthesized']} synthesized, {stats['skipped']} reused)")


def _announce_outputs(pid: str) -> None:
    """The MP4 + transcript are written directly to their final location (the
    project folder when launched by the skill; the deck folder otherwise) — just
    report where."""
    base = store.output_base(pid)
    where = store.video_path(pid).parent
    events.emit(pid, "build", "building", 4, 4,
                f"Saved {base}.mp4 and {base}.txt to {where}")


def _write_transcript(pid: str) -> None:
    """Write transcript.txt: the spoken narration, slide by slide."""
    proj = db.get_project(pid)
    title = proj["name"] if proj else "Transcript"
    slides = sorted(store.read_narration(pid)["slides"], key=lambda s: s["index"])
    lines = [
        title,
        "Narration transcript",
        "Generated automatically from the narration. To change the script, edit it "
        "in the Voiceover app or ask Claude Code; edits made directly to this file "
        "are replaced on the next build.",
        "",
    ]
    for s in slides:
        head = f"Slide {s['index'] + 1}"
        if s.get("title"):
            head += f" — {s['title']}"
        lines.append(head)
        lines.append((s.get("narration") or "(no narration)").strip())
        lines.append("")
    store.transcript_path(pid).write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8")
