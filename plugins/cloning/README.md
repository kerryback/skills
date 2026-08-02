# cloning

Clone your own voice on ElevenLabs, end to end.

Cloning is a one-shot business — a professional clone consumes a slot and takes
hours to train — so most of this plugin is about not wasting it. It gets the
account right, drafts a script worth reading, tells you how to record it, and
checks the audio before you spend anything.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install cloning@kerryback-skills
```

Then ask to clone your voice.

## Requirements

An ElevenLabs account, and a way to record yourself. The QC pass uses `ffmpeg`.

## The steps

1. Account and plan. Which tier you need depends on whether you want an instant
   clone or a professional one, and they behave differently.
2. A reading script, drafted from your own slides and papers — so the clone
   learns your vocabulary and your teaching cadence rather than a stranger's.
   A clone trained on generic text sounds generic.
3. Recording it. Fresh, in one sitting, in one room, with one microphone. The
   guidance here matters more than the equipment does.
4. QC before you spend the slot. An automated `ffmpeg` pass checks level, noise
   floor, clipping, and silence, and tells you to re-record rather than letting
   you find out after training.
5. Create the voice, verify it, and test it on something real.

There is also a section on diagnosing a clone that came out disappointing —
usually the recording, rarely the service.

## Only your own voice

This clones the voice of the person asking, and the workflow includes the
verification step ElevenLabs requires for exactly that reason. It is not for
cloning anyone else, with or without a recording of them.

## What it pairs with

The `voiceover` plugin narrates slide decks. Once your clone exists it appears
in that plugin's voice list, and your lecture videos sound like you.
