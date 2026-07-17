---
name: voiceover
description: >-
  Turn a PDF slide deck into a narrated MP4 video plus a narration transcript.
  Use when an instructor wants to narrate/voice a slide deck, "make a narrated
  video from this PDF", "add AI voiceover to these slides", or "turn this deck
  into a video with a transcript". Invoke it on a PDF file (or with no file to open
  the app's home screen): it launches a local app (http://127.0.0.1:8010) where you
  (Claude Code) draft the per-slide narration and the instructor picks a voice and
  generates the video; the finished .mp4 and .txt are saved to the instructor's
  working directory. Each deck is saved by name and can be reopened to edit and
  regenerate. Requires an ElevenLabs API key and quarto installed.
---

# voiceover

Two roles, don't conflate them:
- The instructor runs this local app (on their own machine) to author the video.
  You, Claude Code, write the narration; the instructor reviews it, picks a voice,
  and generates. The port, the ElevenLabs key, and quarto all matter here.
- Students run nothing. They receive two files — `<name>.mp4` (the narrated video)
  and `<name>.txt` (the transcript) — and view/read them like any other course
  material. No app, no server, no localhost, no login.

The narration is written by you through the app's API, not by an LLM baked into the
app — the app makes no model calls of its own. The finished files land in the
instructor's working directory; the instructor distributes them to students.

## Prerequisites — check first, offer to install what's missing

Before launching, verify these and proactively offer to install or set anything
that's missing. Don't just launch and let it fail later.

- Quarto (renders the deck for the video). Check with `command -v quarto` (or
  `quarto --version`). If it's missing, tell the instructor and offer to install
  it from https://quarto.org/docs/get-started/; do the install if they agree.
  Narration drafting works without Quarto, but the Generate step needs it.
- `ELEVENLABS_API_KEY` in the environment (text-to-speech, Generate step only).
  Check with `printenv ELEVENLABS_API_KEY`. If it's empty, offer to help set it:
  they create a free key at elevenlabs.io, then you help export
  `ELEVENLABS_API_KEY` in their shell profile (or their `~/.env`) so it persists.
  Narration itself needs no key — you write it.
- Python is already present (it runs the launcher), and the first launch sets up a
  small Python environment automatically. ffmpeg is not needed — it ships with the
  Python dependencies. The frontend ships prebuilt, so Node is not required.

If Quarto or the key is missing and the instructor just wants to start drafting,
you can still launch — narration works — but say clearly that the Generate step
won't run until the missing piece is in place. The launcher also prints these
warnings at startup as a backstop.

## What to do

The launcher lives in this skill's own directory. Below, `<skill-dir>` is the
"Base directory for this skill" reported when the skill is invoked; use that
absolute path. `<port>` defaults to 8010.

1. Run the prerequisite checks above and offer to fix anything missing.

2. Identify the deck. If the instructor named a PDF, use it (only `.pdf` — export
   PowerPoint to PDF first). If they just want to start the app — to reopen an
   existing deck or upload one in the browser — launch with no file.

3. Launch the app in the background from the instructor's current directory (so
   the finished files save there):

   ```
   python3 "<skill-dir>/scripts/skill_launch.py" "<absolute path to the PDF>"   # a specific deck
   python3 "<skill-dir>/scripts/skill_launch.py"                                # home screen
   ```

   Run it in the background — it starts a long-lived local server. The first launch
   sets up the app environment, so it takes a little longer.
   - With a PDF: the launcher prints `Open: http://127.0.0.1:<port>/?project=<deck>`,
     where `<deck>` is the deck's id (a slug of its filename). Note it.
   - With no PDF: it opens the home screen. When the instructor uploads or picks a
     deck there, get its id from `GET http://127.0.0.1:<port>/api/projects` (the
     most recently updated entry).

   Decks are saved by name under `{project}/.voiceover/decks/<deck>` (the project
   folder is where the skill was launched). Launching the same deck again from the
   same folder reopens it — existing narration is preserved.

4. Draft (or revise) the narration yourself. This is the heart of the skill — do
   not wait for the instructor and do not expect the app to draft anything.
   - Work from the extracted slide text, not the PDF images. Once the deck has
     converted, get the slides:
     `GET http://127.0.0.1:<port>/api/projects/<deck>/narration` returns
     `{ "slides": [ { "index": 0, "title": "…", "slide_text": "…", "narration": "…" }, … ] }`
     (indexes 0-based, one per PDF page; poll until slides appear if it is still
     converting). Each slide's `slide_text` is the page's text — draft from that.
     This is far faster than rendering the whole PDF as images; do NOT read the
     whole PDF up front.
   - Only when a slide's `slide_text` is empty or clearly missing the visual
     content (a chart, diagram, or all-image slide) read just that one page's
     image — the app serves it at
     `GET http://127.0.0.1:<port>/api/projects/<deck>/slides/slide-<NNN>.png`
     (NNN is the 1-based, zero-padded page number, e.g. slide-003.png), or read
     that single page of the PDF. Don't render pages whose text is enough.
   - If narration is already present (a reopened deck), leave it unless the
     instructor asks for changes. If it is empty (a new deck), write spoken
     narration for every slide following the style rules below — in one pass.
   - Save the whole draft in one call (don't PUT slide by slide):
     `PUT http://127.0.0.1:<port>/api/projects/<deck>/narration` with body
     `{ "slides": [ { "index": 0, "narration": "…" }, … ] }`.
     It appears in the instructor's browser within a few seconds (the Narration
     step polls). To revise a single slide later, PUT
     `/api/projects/<deck>/narration/<index>` with `{ "narration": "…" }`.

5. Hand off to the instructor:
   - Tell them the narration is visible at the URL on the Narration step; they can
     read it, ask you for revisions, or edit any slide directly.
   - When they're happy, they go to Generate to pick a voice (ElevenLabs; default
     "Sarah") and build, then Preview to watch. Each build writes
     `<deck-name>.mp4` and `<deck-name>.txt` to their project folder.
   - Leave the launcher running while they work; stop it with Ctrl-C when done.

6. Revisions come to you, in chat. When the instructor asks for changes ("tighten
   slide 3", "warmer tone", "add a worked example on the terminal-value slide"),
   edit the affected slides via the narration API. Keep the style rules.

7. If the server does not come up (port already in use), rerun with a different
   port, e.g. `--port 8011`, and use that port in the API calls.

## Narration style rules

Write what a good lecturer would say aloud, not slide captions.
- Spoken prose only: no markdown, bullets, headings, or stage directions.
- Roughly 60–130 words per slide; teach the content, don't just describe it.
- One continuous lecture: each slide picks up mid-thought from the previous one.
  Lead with the substance. Do not open slides with throat-clearing transitions
  like "Let's", "Now", "Next", "So", "Moving on", or "Let's look at".
- Never say "this slide" or "welcome"; narrate the content directly.
- Stay faithful to what each slide actually shows.
