# Voiceover Builder

Turn a PDF slide deck into a narrated MP4 video plus a narration transcript.

Two roles, kept separate:

- Instructor — runs this app locally (a Claude Code skill) to author the video.
  Claude Code writes the narration; the instructor reviews it, picks a voice, and
  generates. The app, the port, the ElevenLabs key, and quarto all live here, on
  the instructor's machine.
- Students — run nothing. They receive two files, `<name>.mp4` (the narrated
  video) and `<name>.txt` (the transcript), and view them like any other course
  material. No app, no server, no localhost, no login.

The instructor invokes the skill on a PDF; the app opens at http://127.0.0.1:8010
on the Narration step. Claude Code — the agent that launched the skill — reads the
deck and writes the per-slide narration through the app's API; it appears in the
browser live. The instructor reviews it (and asks Claude Code for revisions, or
edits any slide directly), picks a voice, and generates. There is no login, no
in-app upload, and no in-app download — on each build the finished `<name>.mp4` and
`<name>.txt` are written to the instructor's working directory, and the instructor
shares them with students however they normally distribute course materials.

The app itself makes no LLM calls: all narration comes from Claude Code, so no
Anthropic API key is involved. The only key it needs is ElevenLabs, for
text-to-speech in the Generate step.

## Install (Academic Studio)

This ships as an Academic Studio package. Open Help → Run Setup… and install
"Voiceover Builder"; that installs the skill into `~/.claude/skills/voiceover`
and the prerequisites (Quarto, Python). Set `ELEVENLABS_API_KEY` in your
environment (a free key from elevenlabs.io); Claude walks you through this on
first use. The first launch sets up a small Python environment automatically.

## Run as a skill

Invoke `/voiceover` on a PDF, or run the launcher directly:

```
python3 scripts/skill_launch.py /path/to/deck.pdf
```

It sets up the app environment (first run only), starts the app on port 8010,
creates the project from the PDF, waits for the deck to convert, and opens the
browser on the Narration step. Stop it with Ctrl-C.

If port 8010 is already in use, run with a different one: `--port 8011`. Students
never see this — it only affects the local app.

Storage is folder-based — there is no database. Each deck is a folder under
`{project}/.voiceover/decks/<deck-name>`, named after the deck, holding its PDF
copy, narration, slides, and working files. The app lists decks by reading those
folder names, so relaunching the same deck (from the same project folder) reopens
it, and deleting a deck is just deleting its folder. The finished MP4 and
transcript are written to the project folder itself (`<deck-name>.mp4` /
`<deck-name>.txt`) so they are easy to find. The shared Python environment lives
once in `~/.voiceover/venv`.

## Structure

```
SKILL.md            the Claude Code skill definition (this dir installs as /voiceover)
backend/            FastAPI backend + builderlib (jobs, audio, video, converters)
frontend/           React + Vite + Tailwind SPA (four-step wizard); dist/ ships prebuilt
scripts/            skill_launch.py — the per-file launcher
Dockerfile          container image (bundles Quarto; ffmpeg via pip) — for a future deployable build
CONTRACT.md         API & data contract (source of truth for backend + frontend)
CLAUDE.md           orientation + design decisions
```

## Wizard

Upload → Narration → Generate → Preview. Launched with a PDF, the app opens that
deck on Narration, where Claude Code's draft appears; launched with no file, it
opens the home screen to pick an existing deck or upload one. Preview plays the
finished video; the MP4 + transcript are written to the project folder on each
build.

## Prerequisites

- `quarto` on PATH (deck render). ffmpeg is provided by the `imageio-ffmpeg` pip
  package — no system install.
- `ELEVENLABS_API_KEY` in the environment (TTS).
- The frontend ships prebuilt (`frontend/dist`), so Node is not needed to run —
  only to rebuild the UI from source.

## Environment

| Variable | Purpose |
| --- | --- |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS — voiceover audio (account + cloned voices) |
| `DATA_DIR` | Per-project deck folders + working files (launcher sets `{project}/.voiceover`) |
| `TTS_CONCURRENCY` | Parallel TTS requests per build (default 5; keep at or below your ElevenLabs account's concurrency limit) |
| `VIDEO_CONCURRENCY` | Parallel ffmpeg segment encodes per build (default 4) |
| `VOICEOVER_OUTPUT_DIR` | Where the finished MP4 + transcript are written (launcher sets it to the project folder / cwd) |
