# Voiceover Builder

Turn a slide deck into a narrated MP4 video plus a transcript, with the narration
written as the deck's own speaker notes.

## A deck is two files

| file | supplies |
| --- | --- |
| `lecture-3.qmd` (Quarto reveal) or `lecture-3.pptx` | the speaker notes — the narration script |
| `lecture-3.pdf`, exported from it | the slide images used in the video |

Both stay in your folder. The app reads them and never writes to them. The notes
are the ones you'd see in PowerPoint's presenter view or reveal's speaker view,
so the same deck can be presented live and shipped as a video.

There is no notes editor in the app on purpose: Quarto and PowerPoint already
have one, and the deck is the single copy.

## Requirements

One thing you provide; everything else is handled for you.

- An ElevenLabs API key — the text-to-speech voice. Get a free key at
  https://elevenlabs.io and either export `ELEVENLABS_API_KEY` or paste it into
  the app's banner. Needed only to generate; reading a deck works without it.

Handled for you: Python (the first launch builds a small virtual environment),
ffmpeg (ships with the Python dependencies), and the web UI (ships prebuilt, so
Node is not required). Quarto is not required — the app renders nothing. No
Anthropic API key is needed; the notes are written by Claude Code, not by the app.

## Two roles

- Instructor — runs this app locally (a Claude Code skill) to author the video.
  Claude Code drafts the speaker notes into the deck; the instructor reviews
  them, picks a voice, and generates. The app opens at http://127.0.0.1:8010.
- Students — run nothing. They receive `<name>.mp4` (the narrated video) and
  `<name>.txt` (the transcript) and view them like any other course material.

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

## Run

Invoke `/voiceover` on a deck, or run the launcher directly:

```
python3 scripts/skill_launch.py /path/to/lecture-3.qmd
python3 scripts/skill_launch.py /path/to/lecture-3.pptx /path/to/slides.pdf
```

Point it at the deck you wrote, not at the PDF. The PDF is found next to it by
name unless you pass one. The launcher builds the app environment (first run
only), starts the app on port 8010, reads the deck, and opens the browser on it.
If port 8010 is in use, pass `--port 8011`. Stop with Ctrl-C.

## The edit cycle

Edit the notes in the deck — in Quarto, in PowerPoint's notes pane, or by asking
Claude — then press Reload. The app notices on its own when either file changes
on disk and says so.

Two checks run on every load, because both failures are silent otherwise:
- the deck and the PDF must agree on how many slides there are, or nothing is
  built (a reveal deck exports one page per fragment step unless you set
  `pdf-separate-fragments: false`; PowerPoint leaves hidden slides out);
- the app warns when the PDF is older than the deck, which is how new notes end
  up narrating old slides.

Regenerating re-synthesizes only the notes that actually changed, so fixing one
slide costs one slide of audio.

## Storage and outputs

No database. Each deck is a folder under `{project}/.voiceover/decks/<deck-name>`
holding its page images, audio and settings — not the deck itself, which stays
where you keep it. The finished `<deck-name>.mp4` and `<deck-name>.txt` are
written to the project folder, so they are easy to find. Delete a deck by
deleting its folder. The shared Python environment lives once in
`~/.voiceover/venv`.

## Structure

```
SKILL.md            the Claude Code skill definition (installs as /voiceover)
backend/            FastAPI backend + builderlib (sources, deck, jobs, audio, video)
frontend/           React + Vite + Tailwind SPA (one screen); dist/ ships prebuilt
scripts/            skill_launch.py — the launcher
                    deck_notes.py  — read/write speaker notes (.qmd and .pptx)
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
