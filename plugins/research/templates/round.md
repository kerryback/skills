---
description: Close out a round — write what it took up and what came of it, and release the lock if one was claimed. `start` optionally claims it first.
argument-hint: "(bare to finish a round) | start <what this round is> | status"
---

A round is one bounded stretch of work that ends with `project/global/state.md`
rewritten. Finishing one is the common case, so **bare `/round` finishes a
round** — that is the command to reach for.

`start` is optional and claims the lock. It is worth doing when a coauthor might
be working right now, and pointless when nobody else is in the repo. What it buys
is early warning: claiming up front means a collision surfaces in the first
minute instead of after you have both spent an afternoon on the same question.
Claiming at the end would protect the file and waste the afternoon.

A round is NOT a session. A long round spans several `/clear`s — that is what
`/refresh` is for, and it deliberately leaves the lock alone. Ending a round is a
decision about the work being settled, never about the context window filling up.

Read `CLAUDE.md` if you have not already. Everything below assumes it.

Parse `$ARGUMENTS`: `start …` → section 1, `status` → section 3, anything else
(including empty) → section 2, which is the normal case.

## 1. `start` — claim it (optional)

The rest of the argument is what this round is for. Make it specific enough that
a coauthor reading `lock status` knows whether to wait or work elsewhere: "peer
rule for microcaps", not "analysis".

```bash
python3 -m tools.lock claim "<what this round is>"
python3 -m tools.runid --project . --new
```

If the claim fails, someone else holds the round. Say who and what they claimed,
and do not work around it by editing `state.md` anyway — the lock is a protocol
between people who agreed to use it, and the whole value is that it is honoured
when it is inconvenient. Offer work that does not touch shared state instead.

Then read `project/global/state.md` and `project/global/method_spec.md` — in that
order, and AFTER the claim, never before. Reading state before claiming is how
you end up building on a version someone else has already replaced.

If this round turns on a number, freeze `method_spec.md` and
`workspaces/global/params.py` now, before spawning any implementer.

## 2. `end` — close it out

### First, work out what this round took up

```bash
python3 -m tools.lock status
```

**If a round is held**, read the `note` — that is what it said it was for when it
was claimed. Do this BEFORE releasing: `release` deletes the lock file, and with
it the only record of what the round set out to do.

**If no round is held**, that is fine and common — nobody claimed one, which is
the normal way to work alone. Do not treat it as an error and do not tell the
user to go back and run `start`. Work out what was taken up from this
conversation and say it back to them in one line for correction, e.g. "Recording
this round as: whether the peer rule changes the microcap result." Everything
below proceeds identically; only the release at the end is skipped.

### Then find what the record is missing

```bash
python3 -m tools.chronology --gap --human
```

That lists commits with no changelog entry dated after them — work whose reason
was never written down, usually from a session that ended without anyone saying
so. Walk it. Write the entry now where you can still reconstruct why; name the
ones you cannot, so the gap is known rather than invisible. Never invent a
reason: a wrong changelog entry is worse than a missing one, because it will be
believed.

### Then write the round's entry — always

Every round gets a changelog entry at the top of `project/global/state.md`, with
your author slug and the date, in the file's own format: what the round took up,
then an arrow, then what came of it and why.

**Write it even when the round settled nothing.** That is not a formality. "We
took up X and dropped it, because Y" is the answer to *did we ever explore X*,
and it is the only place that answer exists — a round that changed nothing
leaves no diff, no promoted file, and no trace anybody can find later. A round
that failed is a result.

Take the left-hand side from the claim note if there was one, not from memory of
how the round drifted. If the round genuinely became about something else, say
both: what it claimed, and what it turned into.

Then promote what actually settled into the body of `state.md` — confirmed
thesis changes, newly settled facts, killed ideas WITH the reason, replicated
empirical results. Only promote what is ACTUALLY settled; an in-flight guess
laundered into `state.md` defeats the whole point of the gate.

### Rewrite the handoff

Bring `project/<author>/session.md` up to date the same way `/refresh` does, and
drop whatever you just promoted — it lives in `state.md` now.

### Then release, if a round was claimed

```bash
python3 -m tools.lock release
```

Skip this when no round was held — there is nothing to release, and running it
is harmless but confusing to report.

When one was held, release even if the round was killed or abandoned. An
unreleased lock blocks every other coauthor, and it fails silently — they will
assume you are still working rather than that you forgot.

Commit before you release, so the round's work and its changelog land together.

## 3. `status` — where does the round stand

```bash
python3 -m tools.lock status
python3 -m tools.chronology --gap --human
```

Report, in three lines: whether a round is claimed and by whom, what it claimed,
and whether the changelog has fallen behind. Then say which of bare `/round`,
`start`, or `/refresh` fits what the human is actually about to do — and if a
round has been claimed a long time with nothing settled, say so plainly rather
than letting it drift.

"No round claimed" is not a problem to fix. It is the normal state when nobody
else is in the repo.
