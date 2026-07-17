# Voiceover Builder

Turn a PDF slide deck into a narrated MP4 video plus a narration transcript.

## Requirements

Two things you provide; everything else is handled for you.

- Quarto on your PATH — renders the deck for the video. Install from
  https://quarto.org/docs/get-started/. (Needed for the Generate step; you can
  draft narration without it.)
- An ElevenLabs API key in `ELEVENLABS_API_KEY` — the text-to-speech voice. Get a
  free key at https://elevenlabs.io and export it in your shell. (Needed for the
  Generate step.)

Handled for you: Python (the first launch builds a small virtual environment),
ffmpeg (ships with the Python dependencies), and the web UI (ships prebuilt, so
Node is not required). No Anthropic API key is needed — the narration is written
by Claude Code, not by the app.

## Two roles

- Instructor — runs this app locally (a Claude Code skill) to author the video.
  Claude Code writes the per-slide narration; the instructor reviews it, picks a
  voice, and generates. The app opens at http://127.0.0.1:8010.
- Students — run nothing. They receive `<name>.mp4` (the narrated video) and
  `<name>.txt` (the transcript) and view them like any other course material.

The instructor invokes the skill on a PDF; the app opens on the Narration step,
where Claude Code's draft appears live. The instructor reviews it (asking Claude
Code for revisions or editing any slide directly), picks a voice, and generates.
The finished files are written to the working folder. The app makes no LLM calls
of its own.

## Install

From the kerryback/skills plugin marketplace:

```
/plugin marketplace add kerryback/skills
/plugin install voiceover@kerryback-skills
```

or with the `skills` CLI:

```
npx skills@latest add kerryback/skills
```

or manually — clone and symlink the skill into your Claude Code skills directory:

```
git clone https://github.com/kerryback/skills.git
ln -s "$(pwd)/skills/plugins/voiceover/skills/voiceover" ~/.claude/skills/voiceover
```

Installing copies files only; provide Quarto and `ELEVENLABS_API_KEY` yourself
(the skill checks for both on first use and offers to help set them up).

## Run

Invoke `/voiceover` on a PDF, or run the launcher directly:

```
python3 scripts/skill_launch.py /path/to/deck.pdf
```

It builds the app environment (first run only), starts the app on port 8010,
ingests the PDF, and opens the browser on the Narration step. Launch with no file
to open the home screen (pick an existing deck or upload one). If port 8010 is in
use, pass `--port 8011`. Stop with Ctrl-C.

## Storage and outputs

No database. Each deck is a folder under `{project}/.voiceover/decks/<deck-name>`,
named after the deck, holding its PDF copy, narration, slides, and working files.
The app lists decks by reading those folder names, so relaunching the same deck
(from the same folder) reopens it; delete a deck by deleting its folder. The
finished `<deck-name>.mp4` and `<deck-name>.txt` are written to the project folder
itself, so they are easy to find. The shared Python environment lives once in
`~/.voiceover/venv`.

## Structure

```
SKILL.md            the Claude Code skill definition (installs as /voiceover)
backend/            FastAPI backend + builderlib (jobs, audio, video, converters)
frontend/           React + Vite + Tailwind SPA (four-step wizard); dist/ ships prebuilt
scripts/            skill_launch.py — the launcher
Dockerfile          container image (bundles Quarto; ffmpeg via pip)
CONTRACT.md         API and data contract
CLAUDE.md           orientation and design decisions
```

## Environment

| Variable | Purpose |
| --- | --- |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS — voiceover audio (account + cloned voices) |
| `DATA_DIR` | Per-project deck folders + working files (launcher sets `{project}/.voiceover`) |
| `TTS_CONCURRENCY` | Parallel TTS requests per build (default 5; at or below your ElevenLabs account's limit) |
| `VIDEO_CONCURRENCY` | Parallel ffmpeg segment encodes per build (default 4) |
| `VOICEOVER_OUTPUT_DIR` | Where the finished MP4 + transcript are written (launcher sets it to the project folder) |
