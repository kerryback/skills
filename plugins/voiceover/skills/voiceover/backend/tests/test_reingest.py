"""End-to-end reattach: build a real PDF, ingest it, script it, fake its audio,
then edit the PDF and reattach — and check what survives.

Needs the app's own environment (PyMuPDF), and makes no network calls:

    ~/.voiceover/venv/bin/python backend/tests/test_reingest.py

Everything happens in a temp DATA_DIR, so it never touches real decks.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
WORK = Path(tempfile.mkdtemp(prefix="vo-test-"))
os.environ["DATA_DIR"] = str(WORK / "data")
sys.path.insert(0, str(BACKEND))

import fitz  # noqa: E402
from builderlib import audio_gen, db, jobs, store  # noqa: E402

PID = "deck"

PAGES_V1 = [
    "Introduction to bond duration",
    "Macaulay duration is the weighted average time to cash flow",
    "A worked example on a five year Treasury bond",
    "Convexity corrects the duration approximation",
    "Summary and further reading on fixed income",
]
# Insert a new slide at position 1, delete the worked example, reword convexity.
PAGES_V2 = [
    "Introduction to bond duration",
    "The shape of the yield curve and what it implies",
    "Macaulay duration is the weighted average time to cash flow",
    "Convexity corrects the duration approximation for large yield moves",
    "Summary and further reading on fixed income",
]


def make_pdf(path, pages):
    doc = fitz.open()
    for text in pages:
        page = doc.new_page(width=720, height=405)
        page.insert_text((40, 80), text, fontsize=22)
    doc.save(str(path))
    doc.close()


def narration_for(text):
    return f"Spoken narration about {text.lower()}. " * 3


def ingest(pdf):
    dest = store.pdir(PID) / f"{PID}.pdf"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, dest)
    jobs._convert(PID, dest, "pdf")


def fake_audio():
    """Stand in for a finished build: one MP3 per slide plus the hash map
    audio_gen would have written, so the reuse decision can be checked for real."""
    cfg = store.read_config(PID)
    settings = audio_gen._merged_settings(
        {k: cfg[k] for k in audio_gen.VOICE_SETTING_KEYS if k in cfg})
    sig = audio_gen._voice_sig(cfg["voice_id"], cfg["model"], settings)
    adir = store.audio_dir(PID)
    adir.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for s in store.read_narration(PID)["slides"]:
        i = s["index"]
        (adir / f"slide-{i + 1:03d}.mp3").write_text(f"AUDIO FOR: {s['narration']}")
        hashes[str(i)] = audio_gen._sha(s["narration"] + "\x00" + sig)
    store.hashes_path(PID).write_text(json.dumps(hashes, indent=2))
    return sig


def would_resynthesize(sig):
    """Replay audio_gen.generate's per-slide decision without calling ElevenLabs."""
    hashes = json.loads(store.hashes_path(PID).read_text())
    adir = store.audio_dir(PID)
    out = {}
    for s in store.read_narration(PID)["slides"]:
        i = s["index"]
        if not s["narration"]:
            continue
        h = audio_gen._sha(s["narration"] + "\x00" + sig)
        fresh = (adir / f"slide-{i + 1:03d}.mp3").exists() and hashes.get(str(i)) == h
        out[i] = not fresh
    return out


fails = []


def expect(label, got, want):
    ok = got == want
    print(f"{'ok  ' if ok else 'FAIL'} {label}")
    if not ok:
        print(f"       got  {got}\n       want {want}")
        fails.append(label)


# ---------------------------------------------------------------- first ingest
v1, v2 = WORK / "v1.pdf", WORK / "v2.pdf"
make_pdf(v1, PAGES_V1)
make_pdf(v2, PAGES_V2)

db.create_project(PID, "Deck", "pdf", "uploaded")
ingest(v1)

slides = store.read_narration(PID)["slides"]
expect("first ingest: 5 slides", len(slides), 5)
expect("first ingest: no change flags", [s.get("change") for s in slides], [None] * 5)
expect("first ingest: no review banner", store.read_review(PID), {})

# The agent drafts narration, the instructor builds: audio now exists per slide.
store.write_narration(PID, {"slides": [
    dict(s, narration=narration_for(PAGES_V1[s["index"]])) for s in slides]})
sig = fake_audio()
expect("after build: nothing to re-synthesize",
       any(would_resynthesize(sig).values()), False)

before = {i: (store.audio_dir(PID) / f"slide-{i + 1:03d}.mp3").read_text()
          for i in range(5)}

# ------------------------------------------------------------- reattach edited
ingest(v2)

slides = store.read_narration(PID)["slides"]
narr = {s["index"]: s["narration"] for s in slides}
flags = {s["index"]: s.get("change") for s in slides}

expect("reattach: 5 slides", len(slides), 5)
expect("reattach: flags", flags,
       {0: None, 1: "new", 2: None, 3: "edited", 4: None})
expect("reattach: review summary",
       {k: store.read_review(PID)[k] for k in ("edited", "new", "removed", "unchanged")},
       {"edited": 1, "new": 1, "removed": 1, "unchanged": 3})

# Narration must follow the slide it belongs to, not the index it used to sit at.
expect("slide 0 keeps its script", narr[0], narration_for(PAGES_V1[0]))
expect("inserted slide 1 has no script", narr[1], "")
expect("old slide 1 moved to slide 2", narr[2], narration_for(PAGES_V1[1]))
expect("reworded slide keeps old script as a start", narr[3],
       narration_for(PAGES_V1[3]))
expect("slide 4 keeps its script", narr[4], narration_for(PAGES_V1[4]))
expect("deleted slide's script is gone",
       narration_for(PAGES_V1[2]) in narr.values(), False)

# Audio must move with it.
adir = store.audio_dir(PID)
after = {i: (adir / f"slide-{i + 1:03d}.mp3").read_text()
         for i in range(5) if (adir / f"slide-{i + 1:03d}.mp3").exists()}
expect("audio present for carried slides", sorted(after), [0, 2, 3, 4])
expect("slide 0 audio unchanged", after[0], before[0])
expect("old slide 1's audio moved to slot 2", after[2], before[1])
expect("reworded slide got its own old audio, not its neighbour's",
       after[3], before[3])
expect("slide 4 audio unchanged", after[4], before[4])

# The payoff: with narration untouched, only the inserted slide needs TTS.
resynth = would_resynthesize(sig)
expect("re-synthesis needed for", sorted(i for i, v in resynth.items() if v), [])
expect("inserted slide has no narration yet, so nothing to synthesize",
       1 in resynth, False)

# Now the agent redrafts the two flagged slides, as it does on sight.
store.write_narration(PID, {"slides": [
    dict(s, narration=(narration_for(PAGES_V2[s["index"]])
                       if s.get("change") else s["narration"]))
    for s in slides]})
resynth = would_resynthesize(sig)
expect("after redraft, only the flagged slides re-synthesize",
       sorted(i for i, v in resynth.items() if v), [1, 3])

# ------------------------------------------------------- reattach an unchanged PDF
scripts = [s["narration"] for s in store.read_narration(PID)["slides"]]
ingest(v2)
expect("re-attaching the same PDF reports no changes", store.read_review(PID), {})
expect("re-attaching the same PDF keeps every script",
       [s["narration"] for s in store.read_narration(PID)["slides"]], scripts)
expect("re-attaching the same PDF flags nothing",
       [s.get("change") for s in store.read_narration(PID)["slides"]], [None] * 5)

if fails:
    print(f"\nFAILED: {fails}\nworkdir kept for inspection: {WORK}")
    sys.exit(1)
shutil.rmtree(WORK, ignore_errors=True)
print("\nall ok")
