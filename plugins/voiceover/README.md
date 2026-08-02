# voiceover

Turn a PDF slide deck into a narrated MP4 video plus a transcript.

Claude writes the narration, slide by slide, in a local app you can edit in. You
pick a voice and press Generate. The finished `.mp4` and `.txt` land in your
working directory.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install voiceover@kerryback-skills
```

Point it at a PDF — "narrate these slides" — or invoke `/voiceover` with no file
to open the app's home screen.

## Requirements

| | |
| --- | --- |
| Quarto | renders the deck into the video. Needed only at the Generate step |
| `ELEVENLABS_API_KEY` | text to speech. A free key works to start |

Claude checks both before launching and offers to install or set whatever is
missing, rather than letting it fail halfway through. Writing the narration
needs neither — only generating the video does.

## How it goes

The app opens at <http://127.0.0.1:8010>. Claude reads your deck and drafts
narration for each slide; you read it in the app, change anything that sounds
wrong, choose a voice, and generate.

Decks are saved by name, so you can reopen one later, fix the narration on three
slides, and regenerate without starting over.

## Getting good narration

The narration is drafted to be spoken, not read — which is a different register
from the text on your slides. It doesn't read the bullets aloud, because a
listener can already see them; it says the thing the bullets are shorthand for.

If a slide's narration is wrong, the fastest fix is usually to tell Claude what
you'd actually say and let it rewrite the passage, rather than editing word by
word in the app.

## Your own voice

If you'd rather the video sounded like you than like a stock voice, the
`cloning` plugin walks through cloning your voice on ElevenLabs. The voice it
produces shows up in this app's voice list.
