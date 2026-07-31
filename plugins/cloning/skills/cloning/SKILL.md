---
name: cloning
description: >-
  Clone the user's own voice on ElevenLabs — set up the account, draft a reading
  script from the user's own slides/papers/notes so the clone learns their vocabulary
  and teaching cadence, guide a fresh recording session, check the audio before a
  cloning slot is spent, and create and verify the voice. Use when the user wants to
  "clone my voice", "make an AI version of my voice", "set up a voice on ElevenLabs",
  "use my own voice for narration", or asks what to read aloud for voice training.
  Also use for diagnosing a clone that came out wrong.
---

# Voice cloning on ElevenLabs

Produces a cloned voice the user owns, usable for narration (including the
`voiceover` skill) and anything else driven by ElevenLabs text-to-speech.

The recommended approach, and the one this skill is built around: you draft a reading
script from the user's own writing, and the user records it fresh into a good
microphone in one sitting.

Make the case for it rather than assuming it. A clone learns the room and the codec
along with the voice, so reverb, background noise, and lossy compression in the source
carry into every line the clone will ever speak, and none of it can be taken out
afterward. Purpose-made audio is also usually less total work than cleaning up
recordings — thirty to forty-five minutes in one sitting, against hours of listening
and cutting.

If the user would rather use recordings they already have, that is their decision.
Say what the tradeoff costs, then help them do it well: the audio has to be a single
speaker with no crosstalk, so any stretch where someone else talks needs to come out
first. Run the QC script on the result, and run the cheap instant-clone test in step 4
before committing the professional slot — it will tell them what the source quality
actually buys.

The single most common failure is spending the one professional cloning slot on audio
that was never going to work. Most of this skill is about preventing that.

## Only the user's own voice

Create clones of the person you are talking to, and no one else. ElevenLabs requires
a recorded verification read for professional clones specifically to enforce this,
and their terms prohibit cloning a third party without consent. If the user asks for
a colleague's, a public figure's, or a deceased person's voice, decline the cloning
and offer the alternative: pick a stock voice from the ElevenLabs voice library, or
have the actual person do the verification read themselves on their own account.

## The workflow

Work through these in order. Do not skip step 3.

1. Account and plan → `references/elevenlabs-setup.md`
2. Get the audio — draft the script and record it, or prepare what the user has
3. QC the audio before spending a slot → `scripts/audio_check.sh`
4. Create the voice, verify, test

## Step 1 — Account and plan

If the user has never used ElevenLabs, read `references/elevenlabs-setup.md` and walk
them through it. The short version: cloning requires a paid plan. Instant cloning
needs Starter; professional cloning needs Creator or above, and that tier includes
exactly one professional slot. Do not let them pay for a tier until step 3 has passed
— nothing about writing a script or recording requires a subscription.

## Step 2 — Get the audio

The script-and-fresh-recording path is below. If the user chose to use existing
recordings instead, skip to step 3 with whatever they have — after confirming it is
one speaker throughout, since crosstalk degrades a clone more than almost anything
else.

### Draft the reading script from the user's own writing

This is the highest-leverage step and the one users do not expect. Do not hand them a
generic passage or suggest they read a novel.

Ask what body of their own material best represents how they speak — slide decks,
lecture notes, a textbook they wrote, papers, a blog. Read it. Then write a
continuous reading script on those topics, in their register.

Read `references/script-writing.md` before drafting. It covers length targets,
writing for the mouth rather than the eye, and the specific things that ruin a
recording session.

Save the script into the user's working directory as a markdown file they can read
off a screen.

### Recording

Give them this, adapted to what equipment they actually have:

- Microphone: a dynamic USB mic (Shure MV7 or similar) is the forgiving choice in an
  untreated room because it rejects reflections. A large-diaphragm condenser sounds
  better in a treated space and worse in a bare one. Whatever they own already is
  fine — position and room matter more than the mic.
- Position: six to eight inches away, angled slightly off-axis so plosives do not hit
  the capsule head-on.
- Room: soft surfaces. Curtains, rug, sofa, bookshelves. Kill HVAC, fridge, and
  notifications; phone on airplane mode. Have them record ten seconds of silence and
  listen to it before starting.
- Settings: 48 kHz, 24-bit, mono, WAV. ElevenLabs accepts MP3 at 192 kbps or higher
  and says uncompressed yields little further improvement, but record WAV anyway —
  it costs nothing and leaves room to fix a level problem later. Avoid recording
  through a phone voice-memo app, which writes low-bitrate AAC.
- Levels: target −23 to −18 dBFS RMS with true peak at or below −3 dBFS. That is
  ElevenLabs' stated spec. Clipping is unrecoverable and poisons the clone.
- No processing. No noise reduction, EQ, compression, de-reverb, or "enhance." Raw.
- One session, one setup. Do not record half today and half next week with the mic
  moved.
- Breaks every ten minutes. Vocal fatigue changes timbre, and the last ten minutes
  should not sound like a different person.

Tell them flubs need no editing — pause and re-read the sentence. Long silences do
get trimmed, which the QC script reports on.

## Step 3 — QC before spending a slot

Run the check script on every file before upload:

```
bash "$SKILL_DIR/scripts/audio_check.sh" <file> [more files...]
```

(`$SKILL_DIR` = this skill's folder, i.e. where this SKILL.md lives.)

It reports duration, sample rate, bit depth, channels, codec, mean and peak level,
clipping, and a noise-floor estimate, and flags anything outside ElevenLabs' targets.
It needs `ffmpeg`/`ffprobe` on PATH; if missing, install with `brew install ffmpeg`
(macOS) or the platform equivalent.

Act on what it reports:

- Clipping detected, or true peak above −3 dBFS: have them re-record. Do not
  normalize a clipped file — the waveform is already destroyed.
- RMS below −23 dBFS: usually recoverable with gain, but check the noise floor first;
  quiet audio often means a distant mic, which brings room with it.
- High noise floor: identify the source before re-recording, or the second take will
  match the first.
- Low sample rate, or a lossy codec at low bitrate: bandwidth the source never had.
  Nothing downstream repairs it. On a fresh recording, fix the app or interface
  settings and record again; on existing material, tell the user what it will cost in
  the finished clone and let them decide whether to proceed.
- Total duration under 30 minutes: below the professional-cloning minimum. Either
  record more or use instant cloning.

Only after this passes should the user subscribe to a paid tier.

## Step 4 — Create the voice, verify, test

Prefer proving the concept cheaply first. Cut two to three minutes from the cleanest
stretch, make an instant clone, and have it read a paragraph of real target text. If
that sounds wrong, professional cloning on the same recording will sound wrong too —
better in fidelity, identical in character. Diagnose before committing the slot.

Then, for the professional clone: upload the full set (splitting into five- to
ten-minute files is easier than one large upload), complete the verification read in
the same microphone setup before anything is moved, and wait. Training typically runs
three to six hours, longer when the queue is deep. A failed verification means a
24-hour wait before retrying, so do it carefully once.

When it is ready, test it properly — not on "hello, this is a test," but on a
paragraph of the actual text it will narrate, including the domain vocabulary and any
proper nouns that matter. Listen specifically for the words the user says
distinctively.

Record the resulting voice ID somewhere the user will find it later. The `voiceover`
skill and any ElevenLabs API call both need it.

## Diagnosing a disappointing clone

- Muffled, telephone-like, dull: bandwidth lost at the source — a lossy recording
  app, a headset mic, a low sample rate, or a source recording that never carried the
  full range. Not fixable in settings; it needs a cleaner recording.
- Boxy, distant, echoey: room reverb. Move to a soft-furnished space, get closer to
  the mic, and record again.
- Flat and monotone: the source was read flatly. The clone reproduces the register it
  was given. Re-record with the energy they actually want back.
- Right timbre, wrong rhythm: usually script content — dramatic prose or material
  unlike their real speech. Re-draft per `references/script-writing.md`.
- Mispronounces domain terms: those words were not in the training audio. Add them
  to the script, or handle at generation time with ElevenLabs' pronunciation
  dictionaries.
- Inconsistent across the sample: setup changed mid-recording, or files from
  different sessions were mixed. Use one session only.
