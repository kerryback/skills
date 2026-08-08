---
name: voiceover
description: >-
  Turn a slide deck into a narrated MP4 video plus a transcript, and draft the
  deck's speaker notes. Use when an instructor wants to narrate/voice a deck,
  "make a narrated video from these slides", "add AI voiceover to this deck",
  "write speaker notes for this presentation", or "turn this lecture into a
  video". Works on a Quarto reveal.js .qmd or a PowerPoint .pptx, paired with a
  PDF exported from it: the notes come from the deck, the slide images from the
  PDF. You (Claude Code) draft the speaker notes by editing the deck itself;
  a local app (http://127.0.0.1:8010) shows the slides next to their notes and
  is where the instructor picks a voice and generates. The finished .mp4 and
  .txt are saved to the instructor's working directory. Requires an ElevenLabs
  API key.
---

# voiceover

Two roles, don't conflate them:
- The instructor runs this local app (on their own machine) to author the video.
  You, Claude Code, write the speaker notes; the instructor reviews them, picks a
  voice, and generates. The port and the ElevenLabs key matter here.
- Students run nothing. They receive two files — `<name>.mp4` (the narrated video)
  and `<name>.txt` (the transcript) — and view/read them like any other course
  material. No app, no server, no localhost, no login.

## A deck is two files

The instructor keeps both, in their own folder:

| file | what it gives | edited by |
| --- | --- | --- |
| `lecture-3.qmd` or `lecture-3.pptx` | the speaker notes, slide by slide | you, or the instructor in Quarto / PowerPoint |
| `lecture-3.pdf` | the slide images used in the video | re-exported from the deck |

The app copies neither. It reads them, and re-reads them whenever anyone presses
Reload. The notes live in the deck, which means they are also the notes the
instructor sees in PowerPoint's presenter view or reveal's speaker view — the
same deck can be presented live and shipped as a video.

There is no notes editor in the app, on purpose. Quarto and PowerPoint already
have one, and the deck file is the single copy.

## Prerequisites — check first, offer to fix

- `ELEVENLABS_API_KEY` — the text-to-speech voice, needed only to generate.
  Check with `printenv ELEVENLABS_API_KEY`. Drafting and reviewing notes need no
  key, so a missing one is never a reason to delay launching. If it's empty, say
  so up front and walk them through it — don't just say "you'll need a key":

  1. Sign up (free) at https://elevenlabs.io.
  2. Profile menu, bottom left → API Keys → Create API Key. Copy it; it starts
     with `sk_` and is shown once.
  3. Paste it into the amber banner at the top of the app and press Save key.
     The app validates it against ElevenLabs before accepting, stores it in
     `~/.voiceover/.env` (outside the skill, so a plugin update can't wipe it),
     and enables generation with no restart.

  Offer the alternative if they'd rather have it in the environment for other
  tools too: help them export `ELEVENLABS_API_KEY` in their shell profile. An
  exported variable takes precedence over the stored one.

  Mention the quota once, when they first generate rather than at signup: the
  free tier is measured in minutes of audio per month, which covers trying this
  out but not voicing a full lecture. If a build fails partway with a quota
  error, that is what happened — the already-synthesized slides are cached, so
  resuming after an upgrade re-voices only what's left.
- Python is already present (it runs the launcher), and the first launch sets up
  a small Python environment automatically. Quarto is NOT required — the app
  renders nothing. ffmpeg is not needed either; it ships with the Python
  dependencies. The frontend ships prebuilt, so Node is not required.

## What to do

`<skill-dir>` below is the "Base directory for this skill" reported when the
skill is invoked; use that absolute path. `<port>` defaults to 8010.

1. Identify the two files. The instructor names a deck — take the `.qmd` or
   `.pptx`, not the PDF. Look for the PDF next to it with the same stem. If it
   isn't there, ask them to export it (Quarto: render, then print to PDF with
   `pdf-separate-fragments: false`; PowerPoint: File ▸ Export ▸ PDF) — the app
   cannot make the images without it.

   If they hand you a PDF and nothing else, say what's missing: a PDF has no
   speaker notes, so there is nowhere for the narration to live. Ask for the
   deck it came from.

2. Launch the app in the background from the instructor's current directory (so
   the finished files save there):

   ```
   python3 "<skill-dir>/scripts/skill_launch.py" "<absolute path to the .qmd or .pptx>"
   python3 "<skill-dir>/scripts/skill_launch.py" "<deck>" "<pdf>"   # PDF named differently
   ```

   Run it in the background — it starts a long-lived local server. The first
   launch sets up the app environment, so it takes a little longer. It prints
   `Open: http://127.0.0.1:<port>/?project=<deck>`; note the deck id.

3. Read the deck. `GET http://127.0.0.1:<port>/api/projects/<deck>/notes` returns
   `{ "slides": [ { "index": 0, "title": "…", "slide_text": "…", "notes": "…" }, … ] }`
   — indexes 0-based, one per slide, matched one-to-one with the PDF's pages.
   Draft from `slide_text`; it is far cheaper than rendering images. Only when a
   slide's `slide_text` is empty or clearly misses the visual content (a chart,
   a diagram, an all-image slide) read that one page's image at
   `GET …/api/projects/<deck>/slides/slide-<NNN>.png` (1-based, zero-padded).

   If the state is `load_failed`, the deck and the PDF disagree about how many
   slides there are. The message says which file claims what and what usually
   causes it. Fix that with the instructor before drafting — everything after the
   first divergence would be narration attached to the wrong picture.

4. Write the notes into the deck itself.

   For a `.qmd`, edit the file: each slide takes a
   ```
   ::: {.notes}
   Spoken narration here.
   :::
   ```
   block. Normal file editing — you can see the whole deck, so write the notes
   where they belong.

   For a `.pptx`, use the helper (a .pptx is zipped XML and can't be edited as
   text):
   ```
   echo '{"0": "…", "1": "…"}' | ~/.voiceover/venv/bin/python "<skill-dir>/scripts/deck_notes.py" write "<deck.pptx>"
   ```
   Keys are 0-based slide indexes; slides you leave out are untouched. The same
   script reads notes (`deck_notes.py read <deck>`) if the app isn't running.

   Then `POST http://127.0.0.1:<port>/api/projects/<deck>/reload` so the app
   picks the notes up — or just tell the instructor to press Reload. Notes
   already present are the instructor's; leave them alone unless asked.

5. Hand off with a clear invitation. Tell the instructor, in your own words:
   the notes are on their deck and visible in the app at the URL; they can change
   any of them by editing the deck (Quarto, or PowerPoint's notes pane) and
   pressing Reload, or by telling you — "tighten slide 3", "warmer on the intro",
   "add a worked example on the Gordon-growth slide" — and you'll rewrite them.
   When it reads well they pick a voice and press Generate; the video appears on
   the same screen and `<deck>.mp4` + `<deck>.txt` are written to their folder.

   Say too that if they edit the slides themselves, they should re-export the PDF
   — the app warns when the PDF is older than the deck, and refuses to build if
   the slide counts stop matching.

6. Revisions come to you, in chat. Edit the deck, reload, tell them what changed.
   Keep the style rules below. Editing a slide's notes changes only that slide's
   audio: everything else is reused from the last run, so a one-slide fix costs
   one slide of synthesis.

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

One caveat worth raising with the instructor once: these notes are both the
script the video speaks and the notes they'd see while presenting. Reminders to
themselves ("slow down here", "ask about 2008") get read aloud. If they want
notes for presenting that are not narration, this is the wrong tool for that
deck.
