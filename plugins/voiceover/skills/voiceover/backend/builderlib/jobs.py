"""Background jobs: load (read the deck) and build (TTS + video).
Each runs in a thread and reports progress via events.

Speaker notes are not written here, and not by the app at all — they come from
the instructor's .qmd or .pptx, which they (or Claude Code) edit directly.
Loading re-reads that file; building speaks whatever it now says.
"""
import threading
import traceback

from . import audio_gen, db, deck, events, store, video_gen


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
    mapping = {"loading": "load_failed", "building": "building_failed"}
    return mapping.get(state, f"{state}_failed")


# --------------------------------------------------------------------------- #
# Load — read notes from the source, render page images from the PDF
# --------------------------------------------------------------------------- #
def start_load(pid: str):
    _run_bg(_load, pid)


def _load(pid: str):
    store.set_state(pid, "loading", log="")
    events.emit(pid, "load", "loading", 0, 1, "Reading the deck")
    source_path, pdf_path = store.source_paths(pid)

    def prog(done, total, msg):
        events.emit(pid, "load", "loading", done, total, msg)

    result = deck.load(source_path, pdf_path, store.slides_dir(pid), progress=prog)

    store.write_slides(pid, result["slides"])
    db.update_project(pid, source_type=result["source_type"])
    store.record_files(pid)
    if not store.config_path(pid).exists():
        store.write_config(pid, {})

    n = len(result["slides"])
    narrated = sum(1 for s in result["slides"] if (s.get("notes") or "").strip())
    store.set_state(pid, "ready", log="")
    events.emit(pid, "load", "ready", 1, 1,
                f"{n} slides · {narrated} with speaker notes")


# --------------------------------------------------------------------------- #
# Build — synthesize audio, render the video and transcript
# --------------------------------------------------------------------------- #
def start_build(pid: str):
    _run_bg(_build, pid)


def _build(pid: str):
    store.set_state(pid, "building", log="")
    slides = store.read_slides(pid)["slides"]
    if not any((s.get("notes") or "").strip() for s in slides):
        raise RuntimeError(
            "No slide has speaker notes yet — there is nothing to narrate. Add "
            "notes to the deck (or ask Claude to draft them) and reload.")

    cfg = store.read_config(pid)

    events.emit(pid, "build", "building", 0, 2, "Generating audio")

    def aprog(done, total, msg):
        events.emit(pid, "build", "building", 0, 2, f"{msg} ({done}/{total})")

    stats = audio_gen.generate(
        slides, store.audio_dir(pid), cfg["voice_id"], cfg["model"],
        {k: cfg[k] for k in audio_gen.VOICE_SETTING_KEYS if k in cfg},
        progress=aprog)

    def vprog(done, total, msg):
        events.emit(pid, "build", "building", 1, 2, f"{msg} ({done}/{total})")

    events.emit(pid, "build", "building", 1, 2, "Rendering video")
    store.video_path(pid).parent.mkdir(parents=True, exist_ok=True)
    video_gen.generate(pid, progress=vprog)

    _write_transcript(pid)
    _announce_outputs(pid)

    # Stamp what this video was built from, so a later notes or settings change
    # shows up as "needs regenerating" without tracking edits one by one.
    db.update_project(pid, build_sig=store.build_signature(pid))
    store.set_state(pid, "built")
    events.emit(pid, "build", "built", 2, 2,
                f"Built ({stats['synthesized']} synthesized, "
                f"{stats['skipped']} reused)")


def _announce_outputs(pid: str) -> None:
    """The MP4 + transcript are written directly to their final location (the
    project folder when launched by the skill; the deck folder otherwise) — just
    report where."""
    base = store.output_base(pid)
    where = store.video_path(pid).parent
    events.emit(pid, "build", "building", 2, 2,
                f"Saved {base}.mp4 and {base}.txt to {where}")


def _write_transcript(pid: str) -> None:
    """Write the transcript: the spoken narration, slide by slide."""
    proj = db.get_project(pid)
    title = proj["name"] if proj else "Transcript"
    slides = sorted(store.read_slides(pid)["slides"], key=lambda s: s["index"])
    source = store.read_meta(pid).get("source_path", "the deck")
    lines = [
        title,
        "Narration transcript",
        f"Generated from the speaker notes in {source}. To change the script, "
        "edit the notes in the deck — edits made directly to this file are "
        "replaced on the next build.",
        "",
    ]
    for s in slides:
        head = f"Slide {s['index'] + 1}"
        if s.get("title"):
            head += f" — {s['title']}"
        lines.append(head)
        lines.append((s.get("notes") or "(no speaker notes)").strip())
        lines.append("")
    store.transcript_path(pid).write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8")
