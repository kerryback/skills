# voiceover

Turn a slide deck into a narrated MP4 video plus a transcript — and write the
deck's speaker notes while you're at it.

Claude drafts the narration as speaker notes in your own deck: `::: {.notes}`
blocks in a Quarto `.qmd`, the notes pane in a `.pptx`. A local app shows each
slide next to its notes; you pick a voice and press Generate. The finished `.mp4`
and `.txt` land in your working directory.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install voiceover@kerryback-skills
```

Point it at a deck — "narrate these slides" — giving it the `.qmd` or `.pptx`,
not the PDF.

## What you provide

| | |
| --- | --- |
| the deck | a Quarto reveal `.qmd` or a PowerPoint `.pptx` — where the notes live |
| a PDF of it | exported from the same deck — where the slide images come from |
| `ELEVENLABS_API_KEY` | text to speech. A free key works to start |

Quarto is not required: the app renders nothing, which is why it wants the PDF.
Claude checks for the key before launching and offers to help set it, rather than
letting it fail halfway through. Drafting notes needs no key — only generating
the video does.

## How it goes

The app opens at <http://127.0.0.1:8010>. Claude reads your deck and writes
narration into its speaker notes; you read it in the app, change anything that
sounds wrong — in the deck, or by telling Claude — press Reload, choose a voice,
and generate.

Because the notes live in the deck, they are also what you see in presenter view.
The same file can be the talk you give and the video you post.

Edit the slides later and the app notices: it warns when the PDF is older than
the deck, and refuses to build if the two stop agreeing on how many slides there
are. Regenerating re-voices only the notes that actually changed.

## Getting good narration

The narration is drafted to be spoken, not read — a different register from the
text on your slides. It doesn't read the bullets aloud, because a listener can
already see them; it says the thing the bullets are shorthand for.

If a slide's narration is wrong, the fastest fix is usually to tell Claude what
you'd actually say and let it rewrite the passage.

One thing to know: these notes are both the script and your presenter notes, so
a reminder to yourself ("slow down here") will be read aloud.

## Your own voice

If you'd rather the video sounded like you than like a stock voice, the
`cloning` plugin walks through cloning your voice on ElevenLabs. The voice it
produces shows up in this app's voice list.
