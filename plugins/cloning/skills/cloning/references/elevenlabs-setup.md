# ElevenLabs, for someone who has never used it

Read this when the user is new to the platform. Walk them through it conversationally
rather than pasting the whole thing at them.

Facts here were verified against ElevenLabs' documentation and pricing page in July
2026. Plans and prices change. If a number matters to a decision the user is about to
make with money, check `elevenlabs.io/pricing` rather than quoting this file.

## What it is

A text-to-speech service. You give it text and a voice, and it returns audio. It has
the most convincing English voices generally available, which is why it is worth the
setup effort over the free options built into an operating system.

Three things live under "Voices" in the app:

- The voice library — thousands of ready-made voices, free to use. If the user does
  not specifically need their own voice, this is the answer and cloning is
  unnecessary. Ask before assuming.
- Instant Voice Cloning (IVC) — a clone built from a couple of minutes of audio, in
  under a minute. Good, not exact.
- Professional Voice Cloning (PVC) — a fine-tuned model trained on 30 minutes to 3
  hours, taking hours to train. Close to indistinguishable when the source is good.

## Signing up

Go to `elevenlabs.io`, create an account with email or Google, confirm the address.
The free tier gives 10,000 credits a month and is enough to audition library voices
and hear what the service sounds like. It does not include cloning of either kind.

## Plans, and which one is actually needed

| Tier | Price/month | Credits/month | Instant cloning | Professional cloning |
|---|---|---|---|---|
| Free | $0 | 10,000 | no | no |
| Starter | $6 | 30,000 | yes | no |
| Creator | $22 (first month often half off) | 121,000 | yes | 1 slot |
| Pro | $99 | 600,000 | yes | 1 slot |
| Scale | $299 | 1,800,000 | yes | 1 slot |
| Business | $990 | 6,000,000 | yes | 10 slots |

The practical reading:

- Just testing whether cloning is worth it: Starter, $6. Instant cloning only, which
  is exactly what the step-5 cheap test needs.
- Wanting their real voice for narration: Creator. Note that Creator, Pro, and Scale
  all include exactly one professional slot — paying more buys credits and features,
  not more voices. Only Business raises the slot count.
- A slot is occupied by a voice until deleted, and deleting is how you free it. So
  the one slot should hold the best recording they will make, which is the whole
  reason for the QC step.

Additional professional slots can also be earned through ElevenLabs' "Studio Quality"
manual review if existing voices meet their bar. Not something to plan around.

## Credits

Everything consumes credits, roughly one per character of generated speech. The
numbers above translate to about 30 minutes of audio a month on Starter and two-plus
hours on Creator. Cloning itself does not consume credits; generating speech does.

For a sense of scale: a 40-minute narrated lecture is on the order of 35,000 to
40,000 characters, so Creator covers about three of them per month. If the user
plans heavy narration, price the tier off expected output minutes, not off the
cloning feature.

## The verification read

Professional cloning requires proving the voice is yours. ElevenLabs shows you lines
of text; you record yourself reading them, in the same voice as the training audio.

Two practical points worth telling the user in advance:

- Do it immediately after the main recording session, before the microphone is moved
  or the room changes. A mismatch between the verification read and the training
  audio is a common cause of failure.
- A failed verification means waiting 24 hours before retrying. It is worth two
  minutes of care.

## API key

Needed only for programmatic use — the `voiceover` skill, scripts, any automation.
Not needed to clone a voice or generate speech in the web app.

Profile icon → API Keys → create a key. It is shown once; it cannot be retrieved
later, only regenerated. Store it in an environment variable or a `.env` file, never
in a file that gets committed. The conventional name is `ELEVENLABS_API_KEY`.

If the user has the `voiceover` skill installed, this is the same key it uses — check
whether one already exists before generating another.

## Voice ID

Every voice has an ID, and the API addresses voices by ID rather than name. Find it in
the voice's detail view in the app, or list voices via the API. After a clone
finishes, record the ID somewhere durable. Users routinely lose it and go hunting.

## Things worth knowing before committing

- Terms prohibit cloning someone else's voice without their consent, and the
  verification read exists to enforce it. See the consent section in SKILL.md.
- Cloned voices are private to the account by default. Sharing to the public library
  is opt-in; do not enable it casually on a voice built from someone's real identity.
- Audio generated on paid tiers can generally be used commercially; confirm current
  terms if that matters to the user's situation.
- ElevenLabs applies inaudible watermarking to generated audio and offers detection
  tooling. Worth mentioning to anyone whose concern is misuse of their own voice.
- Deleting a professional voice frees the slot, and the trained model is gone. Keep
  the source recordings — retraining from scratch is possible, remaking the session
  is not.
