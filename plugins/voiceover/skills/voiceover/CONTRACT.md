# Voiceover Builder — API & Data Contract

Single source of truth for the backend and frontend. Both build to this.

This app turns a PDF slide deck into a narrated MP4 video plus a narration
transcript. It is an instructor-only authoring tool that runs locally as a skill:
the instructor invokes it on a PDF, the app opens on http://127.0.0.1:8010, and the
finished `.mp4` and `.txt` are written to the instructor's working directory.
Students run nothing — they only receive those two files. There is no
student-facing app, no chatbot, no hosting, and no in-app download.

## Auth model

- None. The app runs locally, launched per-file by the instructor. If it later
  becomes a deployable multi-user app, reintroduce a login gate.

## Directory layout

```
backend/            FastAPI app (this contract's server)
frontend/           React + Vite + Tailwind SPA -> builds to frontend/dist

{project}/                    the instructor's project folder (VOICEOVER_OUTPUT_DIR)
  <deck>.mp4                  finished narrated video (build output — the deliverable)
  <deck>.txt                  finished narration transcript (build output)
  .voiceover/                 per-project app data (DATA_DIR); no database
    decks/<deck>/             one folder per deck, named after it (the deck id)
      <deck>.pdf              the deck copy
      slides/slide-NNN.png    per-slide images
      deck/                   <name>.qmd + rendered <name>.html + _files + images
      narration.json          {"slides":[{index,title,slide_text,narration}]}
      config.json             {voice_id, model, stability, similarity_boost}
      audio/slide-NNN.mp3 + manifest.json
      meta.json               {id,name,state,source_type,stale,timestamps} — the
                              source of truth for this deck's existence + state
```
The deck folders under `.voiceover/decks` ARE the project registry — the app lists
decks by scanning them and reads each `meta.json`. There is no database.

## Project states

`uploaded → converting → converted → building → built`
Plus `converting_failed | building_failed`, each carrying a `log`.
`converted` means slides exist with empty narration, ready for the agent to draft;
Narration and Generate are both reachable from there (no drafting state).
`built` means video.mp4 is ready. Editing narration/config after `built` sets a `stale` flag (rebuild needed) but keeps state `built`.

## REST API (all JSON unless noted; all under /api; no auth — local app)

- `GET  /api/projects` → `[{id,name,state,source_type,stale,updated_at}]`
- `POST /api/projects` (multipart: `file`, `name`) → project; starts conversion; `source_type == "pdf"` (PDF decks only; other types → 400 with a message telling the teacher to export to PDF)
- `POST /api/projects/from-path` `{path, name?}` → project; reads a PDF already on disk and starts conversion. Used by the skill launcher so the instructor never uploads in-app.
- `GET  /api/projects/{id}` → full project `{id,name,state,stale,slides:[{index,image_url}],config,log}`
- `GET  /api/projects/{id}/narration` → narration.json
- `PUT  /api/projects/{id}/narration` `{slides:[{index,narration}]}` → `{ok,updated}` (bulk set; the Claude Code agent uses this to write a full draft or multi-slide revision in one call; marks stale; 404 on unknown index)
- `PUT  /api/projects/{id}/narration/{index}` `{narration}` → 200 (autosave one slide; marks stale)
- `PUT  /api/projects/{id}/config` `{voice_id,model,stability,similarity_boost}` → 200 (marks stale)
- `GET  /api/tts/voices` → `{configured, voices:[{voice_id,name,category}]}` (account's ElevenLabs voices; `configured:false` when no key)
- `POST /api/projects/{id}/build` → 202; render deck + TTS (only changed slides) + render video
- `GET  /api/projects/{id}/events` → SSE stream of `{stage,state,done,total,message}` for the active job
- `GET  /api/projects/{id}/slides/{file}` → PNG (slide image)
- `GET  /api/projects/{id}/video` → the rendered `video.mp4` (served inline, Range-aware; 404 until built) — used by the Preview `<video>` only

## Output delivery (no in-app download)

On each finished build the `<deck>.mp4` and `<deck>.txt` (transcript) are rendered
directly into the instructor's project folder (`VOICEOVER_OUTPUT_DIR`, set by the
launcher to the cwd; see `store.video_path` / `store.transcript_path`), so the
deliverables sit next to the project — not buried in `.voiceover`.

The Preview step plays `GET /api/projects/{id}/video` in a `<video>` tag; there is no download button.

## Voices & models (frontend picker; backend passes through to audio_gen)

- Voices: fetched live from the account via `GET /api/tts/voices` (ElevenLabs),
  so account + cloned voices appear. Default `voice_id` is `EXAVITQu4vr4xnSDxMaL`
  ("Sarah"). When no `ELEVENLABS_API_KEY` is set the picker prompts for one.
- Models (`model_id`): `eleven_multilingual_v2` (default, highest quality),
  `eleven_turbo_v2_5` (balanced), `eleven_flash_v2_5` (fastest).
- Voice settings: `stability` and `similarity_boost` sliders (0–1; defaults 0.5 / 0.75).

## Frontend

- React + Vite + Tailwind. Builds to `frontend/dist`; FastAPI serves it at `/` (SPA fallback) and static assets. API calls use RELATIVE paths (`api/...`) so it works behind a proxy/sub-path.
- Four-step wizard with a left-rail step tracker: Upload → Narration → Generate → Preview. No login. The launcher opens `/?project=<id>`, which deep-links straight into that project's wizard (landing on Narration once the deck has converted).
- Narration step: slide rail | slide preview | narration textarea (autosave, word/~seconds counter). Narration is written by the Claude Code agent via `PUT …/narration`; the step polls `GET …/narration` (~3s) so those edits appear live. The instructor can also hand-edit any slide. No in-app chat panel — revisions are requested from Claude Code directly.
- Generate step: voice dropdown (fetched account voices) + model dropdown + stability/similarity sliders; Generate button; SSE progress bar with per-slide ticks.
- Preview step (final): `<video>` of the rendered MP4; Back-to-narration / Regenerate. Notes where the artifacts were saved. No download button.

## Build job (backend)

1. Write edited narration into the deck's `::: {.notes}` (image-deck qmd).
2. `quarto render` the deck.
3. Synthesize audio on the rendered HTML with `config.voice_id` + `config.model` + voice settings (ElevenLabs); re-synthesize only slides whose narration text OR voice signature changed (hash per slide includes voice_id/model/settings).
4. Render `video.mp4` (`video_gen.generate`): each slide's PNG shown for its narration length + a 1.5s pause (silent slides dwell 4s), segments normalized to 1920×1080/25fps and concatenated. Uses ffmpeg from the `imageio-ffmpeg` wheel.
5. Write `transcript.txt` (`jobs._write_transcript`): the per-slide narration, snapshotted so it matches this build.
6. Outputs are already in place: the MP4 and transcript were rendered straight to `VOICEOVER_OUTPUT_DIR` (the project folder); `jobs._announce_outputs` just reports where.

## Env (backend)

`ELEVENLABS_API_KEY` (TTS) is the only key — narration comes from the Claude Code agent, so there is no `ANTHROPIC_API_KEY`. `DATA_DIR` (per-project deck folders + working files; the launcher sets `{project}/.voiceover`). Optional: `TTS_CONCURRENCY` (default 5, capped by your ElevenLabs account's concurrency limit), `VIDEO_CONCURRENCY` (default 4), `VOICEOVER_OUTPUT_DIR` (finished MP4 + transcript destination; the launcher sets it to the cwd).
