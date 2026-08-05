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
- `slidematch.py` — aligns a reattached deck against the previous ingest, so an
  edited PDF keeps the narration and audio of the slides it did not change.
- `jobs.py` — the state machine: `_convert`, `_build`, each run in a thread via
  `_run_bg`, emitting events. `_convert` leaves each slide with empty narration
  (the agent fills it in), or, on a reattach, carries the previous ingest's
  narration and audio across (`_reingest`). `_build` renders the deck, synthesizes audio, renders
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
re-synthesizes only slides whose narration text or voice signature changed (a
per-slide sha256 map is kept in the project dir), then always re-renders the
video. Reattaching an edited PDF sends the deck back through
`converting → converted`; unchanged slides keep their narration and their audio,
so the next build re-synthesizes only what was actually redrafted.

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

Expression is a model + settings choice, not an account tier.
The most common complaint about the output is that the voice sounds flat or
robotic, and the instinct is to blame the ElevenLabs plan. It is not the plan.
The cause is the model. `eleven_multilingual_v2` is deliberately even-toned —
fine for a short clip, monotonous over a ten-minute lecture — and it was the
default, reinforced by a dropdown that labelled it "highest quality" and so
discouraged switching. The default is now `eleven_v3` with honest labels.

Be careful not to overstate the settings half of this. `audio_gen.synthesize`
used to send only `stability` and `similarity_boost`, but the two it omitted
already defaulted server-side to what it would have sent anyway (`style` 0,
`use_speaker_boost` true). Adding them to the payload made the knobs reachable
from the UI; it did not by itself make the audio less flat. All five settings
(`audio_gen.VOICE_SETTING_KEYS`) now go on every request and appear in the
Generate step. Before adding a plan-upgrade suggestion anywhere, check the model
first — this is not an account-tier problem.

`style` is documented for the v2 family (where it trades stability and latency
for expression). Its effect on v3 is unverified here: an A/B at 0.0 vs 0.7 was
inconclusive because generation is non-deterministic and the run-to-run spread
exceeded the between-setting difference. Don't assert it helps on v3 without
someone actually listening.

Voice settings travel as one dict, and the whole dict is in the hash.
`synthesize`/`generate` take a `settings` dict rather than a widening positional
list, and `_voice_sig` names every field in `VOICE_SETTING_KEYS`. That matters:
the per-slide hash keys on narration + voice signature, so adding a field
invalidates old hashes and forces a re-render instead of quietly serving audio
built with different settings. If you add a sixth setting, add it to
`VOICE_SETTING_KEYS` and `DEFAULT_VOICE_SETTINGS` and it flows through hashing,
the API payload, and staleness automatically. Note that `_merged_settings` only
substitutes defaults for `None`, so an explicit `false` (speaker boost off)
survives.

A reattached deck is matched by content, never by index.
The instructor edits the PDF and hands it back (Upload ▸ Reattach edited PDF, or
relaunching the skill on the edited file). It is tempting to carry narration over
by slide index — that is what this used to do — and it is wrong in a way that
hides itself: insert one page and every later slide silently inherits its
neighbour's script, and because `audio/slide-NNN.mp3` and `audio_hashes.json` are
keyed by index too, its audio moves with it. Everything looks consistent and
every slide is narrating the wrong content.

So `_convert` fingerprints each page (`convert._fingerprints`: a sha of the
rendered PNG and a sha of the page text, kept in `fingerprints.json`) and
`slidematch.align` matches the ingests through a cascade — identical render,
then identical text, then similar text, then position within the run between two
matches. `store.remap_audio` then moves each carried slide's MP3 and hash entry
to its new index, staged through a temp dir because the renames overlap.

Two fingerprints rather than one, because each covers the other's blind spot: the
image misses nothing but drifts when a re-export rasterizes identical content
differently, and the text is stable but blind to a chart edit. The similarity
level exists for one specific failure — a slide reworded next to a slide deleted,
where position alone would pair the reworded slide with the deleted one's
narration. If you add a fingerprint, add it to `slidematch.KEYS` in strength
order; the cascade handles the rest.

Changed slides keep their old narration, flagged rather than blanked. It is the
right starting point for a redraft, and sometimes it still fits — hence Keep as
is / `POST …/review/clear`. Writing a slide's narration clears its flag, so the
banner empties itself as the work gets done.

`suspect_rerender` on the review summary is the guard against the expensive
failure mode. When most matched slides come back "same words, different pixels",
that is a re-export, not a rewrite; without saying so, the agent would redraft a
perfectly good deck and re-synthesize every slide. Do not remove it in favour of
just flagging everything.

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
- The key is optional to start: the app boots without it (convert + narration
  still work) and shows an app-wide banner (`ApiKeyBanner`) explaining that audio
  can't be generated yet. The instructor pastes the key there; `POST /api/tts/key`
  validates it against ElevenLabs, then `config.set_elevenlabs_key` persists it to
  `backend/.env` and updates the live value so no restart is needed (a page reload
  refreshes the voice picker). `GET /api/tts/status` backs the banner. Do not make
  the key a hard startup requirement.

## Gotchas / operational notes

- Local dev backend runs without `--reload`, so code changes need a manual
  restart to take effect.
- The two tests in `backend/tests/` cover the reattach path, which is the part
  of this app most likely to break silently. Run them after touching
  `slidematch`, `convert._fingerprints`, `jobs._convert`, or `store.remap_audio`:
  `python3 backend/tests/test_slidematch.py` (no dependencies) and
  `~/.voiceover/venv/bin/python backend/tests/test_reingest.py` (needs PyMuPDF;
  no network, temp DATA_DIR).
- A deck built before fingerprints existed has no `fingerprints.json`, so its
  first reattach has nothing to match against and falls back to carrying
  narration by index (the old behaviour) with no flags. That ingest writes the
  fingerprints, so every reattach after it is matched properly. Don't "fix" the
  fallback by inventing fingerprints for the old ingest — there is no old PDF to
  compute them from.
- The Generate step used to carry a "Password viewers will use" field that
  blocked the Generate button. Nothing in the backend ever read it (there is no
  `password` in `ConfigBody` or `DEFAULT_CONFIG`) — it was a leftover of the
  removed hosting/auth path, so it has been deleted. Do not reintroduce it.
- Frontend changes need `npm run build` in `frontend/`; FastAPI serves the built
  `frontend/dist`, so an unbuilt edit will not show up in the running app.
- The `built` state is terminal; re-running build re-renders the video.
- Global preference for this user: avoid boldface in generated prose.
