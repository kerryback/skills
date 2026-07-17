# Voiceover Builder — orientation for Claude

Read this first when working on this repo. It describes what the app is, how it
is structured, and the design decisions behind it (with the reasoning, so you
don't undo them by accident).

This repo began as a fork of the "tutorbots" builder. Removed on purpose, in
order: the student chatbot, the hosted-deck deployment, and the login/auth. It now
runs locally as a skill and produces files. If something here looks like a vestige
of a Q&A tutor, a Koyeb deploy, or a login gate, it is a leftover to clean up, not
a feature to restore.

## What it is

A local app, launched as a Claude Code skill, that turns a PDF slide deck into a
narrated MP4 video plus a narration transcript.

Two roles — keep them straight, because it's easy to conflate the app with its
output:
- The instructor runs this app on their own machine to author the video. The
  server, the port (8010), the API keys, quarto, and node all live here.
- Students run nothing. They receive two files — `<name>.mp4` and `<name>.txt` —
  and view them like any other course material. There is no student-facing app,
  server, or URL; this repo is purely an instructor authoring tool.

The instructor invokes the skill on a PDF (`scripts/skill_launch.py`); the app
opens at http://127.0.0.1:8010 with the deck already loaded (created via
`POST /api/projects/from-path` — no in-app upload). The Claude Code agent that
launched the skill drafts the narration through the API; the instructor reviews
it (asking the agent for revisions or editing slides directly), picks a voice, and
generates the video.

There is no login, no student chatbot, no hosting, and no in-app download. On each
build the finished `<name>.mp4` and `<name>.txt` (transcript) are rendered straight
into the instructor's project folder (`VOICEOVER_OUTPUT_DIR`; see
`store.video_path` / `store.transcript_path`), so the outputs are easy to find.

## Architecture

Two parts:

1. Backend — `backend/`, FastAPI. Owns projects, runs the long jobs (convert,
   build) in background threads, reports progress over a polling event stream,
   and serves the SPA + the rendered video. No auth, and no LLM calls — narration
   is written by the Claude Code agent through the narration API.
2. Frontend — `frontend/`, React + Vite + Tailwind. A four-step wizard:
   Upload → Narration → Generate → Preview. The launcher opens `/?project=<id>`,
   which deep-links straight into that project (landing on Narration).

Key backend modules (`backend/builderlib/`):
- `config.py` — env-driven config (ElevenLabs key, concurrency, paths).
- `db.py` / `store.py` — folder-backed project registry (no database: each deck
  folder's `meta.json` is the source of truth; `list_projects` scans the decks
  dir) and per-deck file I/O.
- `jobs.py` — the state machine: `_convert`, `_build`, each run in a thread via
  `_run_bg`, emitting events. `_convert` leaves each slide with empty narration
  (the agent fills it in). `_build` renders the deck, synthesizes audio, renders
  the video and transcript straight into the project folder (`_write_transcript`;
  `_announce_outputs` reports where). There is no draft job — narration is written
  by Claude Code via the narration API (`PUT …/narration`).
- `audio_gen.py` — parses the rendered deck's notes into narration.json and
  synthesizes per-slide TTS.
- `video_gen.py` — composes the per-slide PNGs + per-slide MP3s into `video.mp4`
  with ffmpeg (from the `imageio-ffmpeg` pip wheel — no system ffmpeg).
- `converters/` — PDF → per-slide images + narration scaffold. `convert.py` is
  the wrapper the jobs call. Only PDF is accepted (see the input design choice).

## Project lifecycle (states)

`uploaded → converting → converted → building → built`, each with a `*_failed`
variant. `converted` means the slides exist with empty narration and the deck is
ready for the agent to draft; the Narration and Generate steps are both open from
there (no drafting state to wait on). `built` means the MP4 is ready. There is no
deploy state. The frontend maps state to the wizard step. The build step
re-synthesizes only slides whose narration text changed (a per-slide sha256 map
is kept in the project dir), then always re-renders the video.

## Design choices (and why)

The deliverables are files on disk, not a hosted app or an in-app download.
`_build` renders the MP4 and transcript directly to their final location — the
instructor's project folder (`VOICEOVER_OUTPUT_DIR`) as `<deck>.mp4` / `<deck>.txt`
when launched by the skill, or the deck folder otherwise; see `store.video_path` /
`store.transcript_path`. `GET /api/projects/{id}/video` serves that MP4 inline for
the Preview `<video>`
only — there is no download endpoint/button. There is no runtime, no password
gate, no Koyeb. Do not reintroduce a deploy/hosting path.

The video is composed from images + audio, not screen-recorded.
`video_gen` shows each slide's PNG for the length of its narration MP3 (plus a
1.5s inter-slide pause), silent slides dwell 4s, and the per-slide segments are
concatenated. Slide index i ↔ `slides/slide-{i+1:03d}.png` ↔ the audio file the
manifest maps to index i. Every segment is normalized to a 1920×1080 / 25fps /
yuv420p / aac canvas so the concat is a clean stream-copy. This avoids a headless
browser and is robust.

ffmpeg comes from pip, not the system.
`imageio-ffmpeg` ships a bundled static binary; `video_gen.FFMPEG` is its path.
This keeps local dev and the container identical with no apt dependency. Do not
add a system ffmpeg requirement.

Audio and video are generated at build time.
TTS and the MP4 render happen once per build. Segment encodes are parallelized
(`VIDEO_CONCURRENCY`, default 4); TTS is parallelized (`TTS_CONCURRENCY`,
default 5, which matches this account's ElevenLabs concurrent-request cap).
Lower them via env if you hit CPU or rate limits.

Narration is authored by Claude Code, not the app.
The Narration step is a plain editor: slide rail | slide preview | narration
textarea, autosaving per-slide edits. The Claude Code agent that launched the
skill reads the deck and writes narration through the narration API
(`PUT …/narration` for a full draft, `PUT …/narration/{index}` for one slide);
the editor polls so those writes appear live. The app holds no model client and
needs no Anthropic key. Do not reintroduce an in-app LLM chat or a drafting job.

Input is PDF-only.
`detect_source_type` accepts only `.pdf`; `.pptx/.ppt` is rejected with a message
telling the teacher to export to PDF. Do not reintroduce a PPTX-render path.

PDF conversion is one image per PDF page.
`converters` render each page to its own PNG. If a generated slide shows two
slides, the source PDF is a 2-up handout — that is an input problem, not a bug.

## Deployment facts

- Builder is containerized (`Dockerfile`, build for `linux/amd64`). The image
  bundles Quarto (deck render). ffmpeg is not apt-installed — it rides in via the
  `imageio-ffmpeg` wheel.
- The app needs, at runtime (env, never baked in): `ELEVENLABS_API_KEY` (TTS).
  That is the only key — narration comes from Claude Code, so there is no
  `ANTHROPIC_API_KEY`. No auth secrets, no `KOYEB_TOKEN` — nothing is deployed.

## Gotchas / operational notes

- Local dev backend runs without `--reload`, so code changes need a manual
  restart to take effect.
- The `built` state is terminal; re-running build re-renders the video.
- Global preference for this user: avoid boldface in generated prose.
