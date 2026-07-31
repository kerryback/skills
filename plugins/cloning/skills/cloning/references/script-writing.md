# Drafting the reading script

The user has to read aloud for 30 to 45 minutes. What they read determines what the
clone sounds like, and it is the part of this process people get wrong by default —
they grab a public-domain novel and end up with a clone that sounds like an audiobook
narrator rather than like themselves.

## Source the content from the user's own writing

Ask what body of their material best represents how they talk. Slide decks, lecture
notes, a textbook, papers, a blog, internal memos. Read it — genuinely read it, not
just the headings — and write the script on those topics in their register.

Three things this buys that a generic passage cannot:

- Domain vocabulary enters the training audio. The clone learns how they say
  "heteroskedasticity," "exfiltration," the tickers, the product names, the acronyms.
  Words absent from training are the ones a clone mispronounces later.
- Cadence matches the eventual use. If the clone will narrate lectures, train it on
  someone explaining something, because explaining has a different rhythm than
  reading a story.
- The user reads more naturally. People read their own ideas with conviction and
  someone else's prose with performance. Conviction is what you want captured.

Write it as continuous expository prose. Not slide bullets, not an outline read
aloud — paragraphs that connect.

## Length

Target roughly 7,500 to 8,000 words. That runs about 55 minutes at a normal teaching
pace and gives margin above the 30-minute professional-cloning minimum, so a rough
stretch can be discarded without dropping under.

Rates vary a lot by speaker. Rather than promising a duration, state the word count,
give an estimate, and mark where the 40-minute point falls so the user can stop early
with a usable recording.

Break it into 12 to 18 numbered parts of three to five minutes. Parts give natural
break points, let the user resume cleanly after a flub, and make it possible to drop
one bad section.

## Write for the mouth, not the eye

Every one of these exists because it derails a live reading:

- No bullet fragments. Fragments have no spoken rhythm and the reader's pitch falls
  off a cliff at each one.
- No code, no URLs, no file paths, no email addresses.
- No symbols. Write "percent," "dollars," "and." A dollar sign mid-sentence makes the
  reader stop and decide how to say it.
- Spell numbers and dates the way they would be said. "Eleven, slash, oh three,
  slash, twenty twenty-five" rather than the digits, if the digits are the point.
  "Two hundred eighty-five billion dollars," not the numeral.
- Expand or avoid ambiguous abbreviations. Leave acronyms the user says routinely
  (SQL, API, MCP) and tell them in the preamble to read acronyms however they
  naturally say them.
- Avoid deep parentheticals and long subordinate stacking. A sentence the reader has
  to scan ahead to parse gets read badly.
- Avoid tongue-twisters and heavy sibilance runs. They cause retakes.

## Vary the rhythm deliberately

A clone learns prosody from the training audio. Uniform sentences produce a flat,
metronomic voice, and it is the most common reason a technically clean clone still
sounds wrong.

So vary sentence length hard. Some sentences of three words. Some that run forty and
carry three clauses. Ask rhetorical questions — they train rising intonation, which
otherwise never appears. Include emphasis, contrast, the occasional aside. Let a
paragraph land on a short declarative.

Include some emotional range within the user's normal professional register:
enthusiasm about something genuinely interesting, caution about a real risk, dry
understatement. A clone cannot produce range that was never in the source.

Do not over-engineer this into its own formula. Let the sentences be as long as their
thoughts, and the variation follows.

## The preamble

Open the file with a short block, clearly marked as not-to-be-read, containing:

- Word count and estimated reading time, and where the 40-minute mark falls
- Do not read the part numbers or titles aloud
- Read acronyms however you normally say them
- Flubs need no editing — pause and read the sentence again
- Break every three or four parts
- Start recording, leave two seconds of silence, then begin at Part One

That leading silence matters — it gives the QC script a clean noise-floor sample.

## Check before handing it over

Count the words rather than estimating them, and report the real number:

```
awk 'NR>N' script.md | wc -w        # N = last line of the preamble
```

Then reread for anything unreadable aloud: a stray URL, a bare numeral, a sentence
that needs a second pass to parse. Fix those before the user is standing at a
microphone.
