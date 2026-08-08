# Voiceover Builder — orientation for Claude

Read this first when working on this repo. It describes what the app is, how it
is structured, and the design decisions behind it (with the reasoning, so you
don't undo them by accident).

## What it is

A local app, launched as a Claude Code skill, that turns a slide deck into a
narrated MP4 video plus a transcript.

A deck is two files, both of which stay in the instructor's own folder:
- the deck they wrote — a Quarto reveal `.qmd` or a PowerPoint `.pptx` — which
  is where the speaker notes live, and
- a PDF exported from it, which is where the slide images come from.

The app copies neither and writes to neither. It reads them on load and re-reads
them on Reload. Notes are authored in the deck, by Claude Code or by the
instructor in Quarto/PowerPoint.

Two roles — keep them straight:
- The instructor runs this app on their own machine to author the video. The
  server, the port (8010), and the ElevenLabs key all live here.
- Students run nothing. They receive `<name>.mp4` and `<name>.txt` and view them
  like any other course material. There is no student-facing app or URL.

## Architecture

1. Backend — `backend/`, FastAPI. Owns decks, runs the two long jobs (load,
   build) in background threads, reports progress over an event stream, and
   serves the SPA + the rendered video. No auth, no LLM calls.
2. Frontend — `frontend/`, React + Vite + Tailwind. One screen: thumbnail strip,
   slide (or finished video) on the left, that slide's speaker notes read-only on
   the right, audio controls and Generate underneath. The launcher opens
   `/?project=<id>`.

Key backend modules (`backend/builderlib/`):
- `sources.py` — reads (and writes) speaker notes for both formats. The qmd
  parser splits slides the way Quarto does; `write_qmd_notes` / `write_pptx_notes`
  back the `deck_notes.py` helper Claude uses for PowerPoint.
- `deck.py` — loads a deck: notes from the source, page PNGs from the PDF, and
  the slide-count check between them.
- `store.py` / `db.py` — folder-backed registry (no database: each deck folder's
  `meta.json` is the source of truth) and per-deck file I/O.
- `jobs.py` — two jobs, `_load` and `_build`, each run in a thread via `_run_bg`.
- `audio_gen.py` — content-addressed per-slide TTS.
- `video_gen.py` — composes the PNGs + MP3s into the MP4 with ffmpeg (from the
  `imageio-ffmpeg` pip wheel — no system ffmpeg).

## Deck lifecycle (states)

`loading → ready → building → built`, with `load_failed` and `building_failed`.
`ready` means notes and images are in hand and agree. Staleness is computed, not
tracked: `store.build_signature` shas every slide's notes plus the voice
settings, `_build` stamps it, and `store.is_stale` compares. There is no edit
bookkeeping to get wrong.

## Design choices (and why)

Notes live in the deck, and the app has no notes editor.
This is the load-bearing decision. Quarto and PowerPoint already have good notes
editors — PowerPoint's notes pane sits under the slide, and a .qmd is text — and
the deck file is the copy the instructor presents from. Putting an editor in the
app would create a second copy and immediately raise "which one is right?".
There is no `PUT /narration` and no autosave. Do not reintroduce one.

Everything that used to reconcile two copies is therefore gone. The old build
matched a re-exported PDF against the previous ingest by content fingerprints
(`slidematch.py`), flagged moved slides, offered "keep as is", and warned about
`suspect_rerender` — roughly 400 lines whose entire job was carrying narration
across a deck edit. When the notes are inside the file being edited, they move
with their slides for free. If you find yourself needing slide alignment again,
first check whether you have accidentally reintroduced a second copy of the
notes.

Audio is a content-addressed cache, not an indexed one.
`audio_gen` names each MP3 `sha(notes + voice signature).mp3` and writes a
manifest of index → filename. Nothing is keyed by slide position, so inserting a
slide at the front re-synthesizes nothing, and two slides with identical notes
share one clip. The old scheme (`slide-NNN.mp3` plus an index-keyed hash map)
needed `store.remap_audio` to shuffle files whenever the deck changed shape; that
whole class of bug is gone. Clips no slide points at are pruned after each build,
because a clip's name encodes text that nothing says any more — it can never be
hit again.

The slide-count check is a refusal, not a warning.
If the source has 24 slides and the PDF has 31 pages, every slide after the
first divergence narrates the wrong picture, and it looks fine until someone
watches it. `deck.load` raises with a message that names both files, both
numbers, and the usual cause: for a .qmd, reveal exporting one page per fragment
step (fix: `pdf-separate-fragments: false`); for a .pptx, hidden slides, which
PowerPoint leaves out of an exported PDF. Do not downgrade this to a warning.

The two files can also drift more quietly, so `store.file_status` reports
mtimes: either file changed since the app read it, and — the dangerous one — the
PDF being older than the deck, which is how new notes end up over old slides.

There is no Quarto dependency any more.
The old build injected narration into a generated qmd, rendered it with Quarto,
and parsed the notes back out of the rendered HTML. Nothing renders now: images
come from the instructor's PDF and notes come from the source. Do not add a
render step back — if a deck needs rendering, that happens in the instructor's
own workflow, before the PDF exists.

Input is .qmd or .pptx, plus a PDF.
A bare PDF is rejected with an explanation rather than accepted: it has no
speaker notes, so there would be nothing to narrate and nowhere to put a draft.

The deliverables are files on disk, not a hosted app or an in-app download.
`_build` renders the MP4 and transcript directly to the instructor's project
folder (`VOICEOVER_OUTPUT_DIR`). `GET /api/projects/{id}/video` serves that MP4
inline for the in-app player only. There is no download endpoint, no deploy path,
no login.

The video is composed from images + audio, not screen-recorded.
`video_gen` shows each slide's PNG for the length of its narration MP3 (plus a
1.5s inter-slide pause), silent slides dwell 4s, and the per-slide segments are
concatenated. Every segment is normalized to a 1920×1080 / 25fps / yuv420p / aac
canvas so the concat is a clean stream-copy.

ffmpeg comes from pip, not the system.
`imageio-ffmpeg` ships a bundled static binary; `video_gen.FFMPEG` is its path.
Do not add a system ffmpeg requirement.

Expression is a model + settings choice, not an account tier.
The most common complaint about the output is that the voice sounds flat, and
the instinct is to blame the ElevenLabs plan. It is not the plan. It is the
model: `eleven_multilingual_v2` is deliberately even-toned — fine for a short
clip, monotonous over a ten-minute lecture. The default is `eleven_v3` with
honest labels. Before suggesting a plan upgrade anywhere, check the model.

Be careful not to overstate the settings half of this. All five settings
(`audio_gen.VOICE_SETTING_KEYS`) go on every request and appear in the read
settings panel, but `style` and `use_speaker_boost` already defaulted
server-side to what we now send — exposing them made the knobs reachable; it did
not by itself make the audio less flat. `style`'s effect on v3 is unverified: an
A/B at 0.0 vs 0.7 was inconclusive because generation is non-deterministic and
the run-to-run spread exceeded the between-setting difference.

Voice settings travel as one dict, and the whole dict is in the hash.
`_voice_sig` names every field in `VOICE_SETTING_KEYS`, so adding a field
invalidates old clip names and forces a re-render instead of quietly serving
audio built with different settings. Add a sixth setting to `VOICE_SETTING_KEYS`
and `DEFAULT_VOICE_SETTINGS` and it flows through naming, the API payload, and
staleness automatically. `_merged_settings` only substitutes defaults for `None`,
so an explicit `false` (speaker boost off) survives.

The ElevenLabs key lives in ~/.voiceover/.env, never in the skill directory.
The skill directory is package content — installing or updating the plugin
replaces it. Version 1.x wrote a pasted key to `backend/.env`, inside that
directory, so an update silently deleted it and dropped the user back at the key
banner with no explanation. It hit exactly the people who used the paste-in-app
path rather than exporting a shell variable. `config.py` now resolves the key
from, strongest first: a real environment variable, `~/.voiceover/.env`, then a
legacy `backend/.env` whose key is copied out on first run. The old file is read
but never written and never deleted — the skill directory may be read-only, and
a stale copy is harmless once the home file wins. Do not move it back, and do not
put anything else durable under the skill directory.

## Gotchas / operational notes

- The local dev backend runs without `--reload`, so code changes need a manual
  restart to take effect.
- Frontend changes need `npm run build` in `frontend/`; FastAPI serves the built
  `frontend/dist`, which is committed, so an unbuilt edit will not show up.
- `skill_launch.py` reinstalls requirements when `requirements.txt` changes (it
  stamps a sha in the venv), so a skill update that adds a dependency doesn't
  need the user to blow away `~/.voiceover/venv`.
- The qmd parser follows Quarto's slide rules: headings at or above
  `slide-level`, `---` rules, and a front-matter `title` producing a title slide.
  It tracks fenced code blocks (so a `##` comment inside a Python block is not a
  slide break) and nested `:::` divs. It is not a full Pandoc; the slide-count
  check is the backstop that catches anything it gets wrong.
- A build that dies partway (an ElevenLabs quota error is the usual way) leaves
  the clips it finished on disk under their content-addressed names, so retrying
  after an upgrade re-synthesizes only what's left. The manifest and the prune
  both run after synthesis, so a failed run changes nothing else.
- Notes are both the spoken script and what the instructor sees while presenting.
  That is the point, but it means "remember to slow down" gets read aloud. Worth
  saying once to a new user; don't build a filter for it.
- Global preference for this user: avoid boldface in generated prose.
