# Voiceover Builder — API & Data Contract

Single source of truth for the backend and frontend. Both build to this.

This app turns a slide deck into a narrated MP4 video plus a transcript. It is an
instructor-only authoring tool that runs locally as a skill: the instructor
invokes it on a deck, the app opens on http://127.0.0.1:8010, and the finished
`.mp4` and `.txt` are written to the instructor's working directory. Students run
nothing — they only receive those two files. There is no student-facing app, no
chatbot, no hosting, and no in-app download.

## What a deck is

Two files, both owned by the instructor and never copied into the app:

| file | supplies | who edits it |
| --- | --- | --- |
| `<name>.qmd` (Quarto reveal) or `<name>.pptx` | speaker notes, slide titles, slide text | Claude Code, or the instructor in Quarto / PowerPoint |
| `<name>.pdf` exported from it | one page image per slide | re-exported by the instructor |

The app reads both on load and re-reads them on Reload. It writes to neither.
There is no in-app notes editor and no narration-writing API: the deck file is
the single copy of the notes.

A bare PDF is rejected — it has no speaker notes, so there is nothing to narrate
and nowhere to put a draft.

## Auth model

- None. The app runs locally, launched per-deck by the instructor.

## Directory layout

```
backend/            FastAPI app (this contract's server)
frontend/           React + Vite + Tailwind SPA -> builds to frontend/dist
scripts/            skill_launch.py (start the app), deck_notes.py (read/write notes)

{project}/                    the instructor's project folder (VOICEOVER_OUTPUT_DIR)
  <deck>.qmd | <deck>.pptx    the deck — speaker notes live here
  <deck>.pdf                  the exported PDF — slide images come from here
  <deck>.mp4                  finished narrated video (build output — the deliverable)
  <deck>.txt                  finished narration transcript (build output)
  .voiceover/                 per-project app data (DATA_DIR); no database
    decks/<deck>/             one folder per deck, named after it (the deck id)
      slides/slide-NNN.png    per-slide images rendered from the PDF (1-based)
      slides.json             {"slides":[{index,title,slide_text,notes}]} — the
                              last read of the source deck
      config.json             {voice_id, model, stability, similarity_boost,
                              style, use_speaker_boost, speed}
      audio/<sha>.mp3 + manifest.json
      meta.json               {id,name,state,source_type,source_path,pdf_path,
                              source_mtime,pdf_mtime,build_sig,log,timestamps}
```
The deck folders under `.voiceover/decks` ARE the registry — the app lists decks
by scanning them and reading each `meta.json`. There is no database.

## Deck states

`loading → ready → building → built`, plus `load_failed | building_failed`, each
carrying a `log`. `ready` means the notes and the page images are in hand and
agree on how many slides there are. `built` means the MP4 is ready.

Staleness is computed, not stored: `store.build_signature` shas every slide's
notes plus the voice settings; `_build` stamps it into `build_sig`; `is_stale`
compares. So editing the deck and reloading makes a built video stale without any
edit bookkeeping.

## The slide-count check

`deck.load` refuses when the source's slide count and the PDF's page count
differ — every slide after the first divergence would narrate the wrong picture.
The error names both files, both counts, and the usual cause:
- `.qmd` with more PDF pages than slides: reveal exports one page per fragment
  step unless `pdf-separate-fragments: false` is set under `format: revealjs:`.
- `.pptx` with fewer PDF pages than slides: hidden slides, which PowerPoint
  leaves out of an exported PDF.

`GET /api/projects/{id}` also reports softer drift in `files`: either file
changed since the app read it (`source_changed`, `pdf_changed`) and — the quiet
one — `pdf_older_than_source`, which is how new notes end up over old slides.

## REST API (all JSON; all under /api; no auth — local app)

- `GET  /api/projects` → `[{id,name,state,source_type,stale,files,updated_at}]`
- `POST /api/projects` `{source, pdf?, name?}` → deck summary; starts a load.
  `source` is a path to a `.qmd` or `.pptx` already on disk; `pdf` defaults to
  the same path with a `.pdf` extension. 400 if either file is missing or the
  source is an unsupported type. Re-opening the same source reopens the same
  deck (id = slug of the filename stem).
- `POST /api/projects/{id}/reload` → 202; re-reads the source and the PDF.
- `GET  /api/projects/{id}` → `{id,name,state,source_type,stale,files,
  slides:[{index,title,notes,image_url}],config,log}`
- `GET  /api/projects/{id}/notes` → `{source,source_type,slides:[{index,title,
  slide_text,notes}]}` — what Claude Code reads before drafting. There is no
  corresponding PUT: notes are written by editing the deck.
- `PUT  /api/projects/{id}/config` `{voice_id,model,stability,similarity_boost,style,use_speaker_boost,speed}` → 200 (all fields optional)
- `GET  /api/tts/status` → `{configured}` (is an ElevenLabs key set)
- `POST /api/tts/key` `{api_key}` → validates against ElevenLabs, persists to `~/.voiceover/.env` (outside the skill dir, so a plugin update can't wipe it), updates the live value
- `GET  /api/tts/voices` → `{configured, voices:[{voice_id,name,category}]}`
- `GET  /api/tts/voices/{voice_id}` → `{voice_id,name,category,preview_url,labels[]}` (resolve one id — the account first, then the Voice Library; 404 when no such voice)
- `POST /api/projects/{id}/build` → 202; TTS + video. 409 while loading or after a failed load.
- `GET  /api/projects/{id}/events` → SSE stream of `{stage,state,done,total,message}` for the active job
- `GET  /api/projects/{id}/slides/{file}` → PNG (slide image)
- `GET  /api/projects/{id}/video` → the rendered MP4 (served inline, Range-aware; 404 until built) — for the in-app player only

## Editing notes (there is no notes API)

Claude Code drafts and revises by editing the deck:
- `.qmd` — edit the file; each slide takes a `::: {.notes}` … `:::` block.
- `.pptx` — `scripts/deck_notes.py write <deck>` with `{index: notes}` on stdin
  (zipped XML can't be text-edited). The same script reads notes without the app.

Then `POST …/reload`, or the instructor presses Reload.

## Audio cache

`audio_gen` names each MP3 `sha(notes + voice signature).mp3` and writes
`manifest.json` mapping slide index → filename. Nothing is keyed by slide
position, so inserting or reordering slides re-synthesizes nothing, and two
slides with identical notes share a clip. Unreferenced clips are pruned after
each build.

## Output delivery (no in-app download)

On each finished build the `<deck>.mp4` and `<deck>.txt` (transcript) are
rendered directly into the instructor's project folder (`VOICEOVER_OUTPUT_DIR`,
set by the launcher to the cwd; see `store.video_path` / `store.transcript_path`).
The app plays `GET /api/projects/{id}/video` in a `<video>` tag; there is no
download button.

## Voices & models (frontend picker; backend passes through to audio_gen)

- Voices: fetched live from the account via `GET /api/tts/voices` (ElevenLabs),
  so account + cloned voices appear. Default `voice_id` is `EXAVITQu4vr4xnSDxMaL`
  ("Sarah"). When no `ELEVENLABS_API_KEY` is set the picker prompts for one.
- The rest of ElevenLabs' Voice Library (~15k voices) is not listed — it is only
  browsable and auditionable on their site. The picker takes a pasted id instead
  and resolves it through `GET /api/tts/voices/{voice_id}`, showing the name,
  labels and preview clip before the instructor commits to it. Text-to-speech
  accepts a library voice directly, with no add-to-my-voices step; ElevenLabs
  files it under the account on first use, so afterwards it is in the dropdown.
- Models (`model_id`): `eleven_v3` (default, most expressive),
  `eleven_multilingual_v2` (even, understated), `eleven_turbo_v2_5` (faster),
  `eleven_flash_v2_5` (fastest). v3 is the default because the v2 family's even
  delivery reads as flat over a full narrated lecture — a model property, not an
  account-tier limit.
- Voice settings, all sent on every request (`audio_gen.VOICE_SETTING_KEYS`):
  `stability`, `similarity_boost`, `style`, `use_speaker_boost`, `speed`.
  Defaults 0.5 / 0.75 / 0.0 / true / 1.0. Ranges are 0–1 except `speed` (0.7–1.2).
- Stability is model-shaped: v3 defines three levels (0.0 Creative, 0.5 Natural,
  1.0 Robust) and the picker offers exactly those; the v2 family takes a
  continuous 0–1 slider. The API does not reject in-between values on v3, so the
  backend passes settings through unmodified rather than snapping them.

## Frontend

- React + Vite + Tailwind. Builds to `frontend/dist`; FastAPI serves it at `/`
  (SPA fallback). API calls use RELATIVE paths (`api/...`) so it works behind a
  proxy/sub-path.
- One screen, no wizard and no navigation. The launcher opens `/?project=<id>`.
  Top to bottom: thumbnail strip (amber dot = no notes), then the slide image —
  or the finished video, via a Slide/Video toggle — on the left with that slide's
  speaker notes read-only on the right, then the audio panel (voice, model,
  Generate, a disclosure holding the read settings and the Voice Library field,
  and the SSE progress bar with per-slide ticks).
- The header carries the deck name, both filenames, the state pill, and Reload.
  Drift in either file raises a banner above the strip with its own Reload; a
  failed load replaces the deck view with the reason and a retry.
- Opening `/` with no `?project=` lists the decks this folder knows about. There
  is no upload — a deck is opened by launching the skill on it.

## Build job (backend)

1. Synthesize audio for every slide with notes, using `config.voice_id` +
   `config.model` + voice settings (ElevenLabs). Clips are content-addressed, so
   only text that is new in this voice is sent.
2. Render `video.mp4` (`video_gen.generate`): each slide's PNG shown for its
   narration length + a 1.5s pause (silent slides dwell 4s), segments normalized
   to 1920×1080/25fps and concatenated. Uses ffmpeg from the `imageio-ffmpeg`
   wheel — no system ffmpeg.
3. Write the transcript (`jobs._write_transcript`): the per-slide notes,
   snapshotted so it matches this build.
4. Outputs are already in place: both were rendered straight to
   `VOICEOVER_OUTPUT_DIR`; `jobs._announce_outputs` just reports where.
5. Stamp `build_sig` so later edits show as stale.

Nothing is rendered from source — no Quarto, no LibreOffice, no headless browser.
The slide images come from the instructor's PDF.

## Env (backend)

`ELEVENLABS_API_KEY` (TTS) is the only key — notes come from the deck, so there
is no `ANTHROPIC_API_KEY`. `DATA_DIR` (per-project deck folders + working files;
the launcher sets `{project}/.voiceover`). Optional: `TTS_CONCURRENCY` (default
5, capped by your ElevenLabs account's concurrency limit), `VIDEO_CONCURRENCY`
(default 4), `VOICEOVER_OUTPUT_DIR` (finished MP4 + transcript destination; the
launcher sets it to the cwd).
