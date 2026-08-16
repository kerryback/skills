---
description: Checkpoint memory to disk and hand off to a fresh context window — write your handoff, then you run /clear and resume with nothing lost.
argument-hint: ""
---

Your context window is getting long; refresh it. You CANNOT clear your own
context — this command runs inside the current session — so do the half you can
(write durable state cleanly), then hand off to the human to run `/clear`. On
resume, CLAUDE.md and the state files bring the next session up to speed.

This is a SESSION boundary, not a round boundary. The round keeps going across
the `/clear` — you are still holding the lock when the next session starts, and
that is correct. Finishing a round is `/round`, which is a separate decision
about the work rather than about the context window.

Read `CLAUDE.md` if you have not already. Everything below assumes it.

## 1. Rewrite your handoff, compact

Rewrite `project/<author>/session.md` so a cold-start session could resume from
it alone:

- **Where we are** — one paragraph of status.
- **In flight** — work started but unfinished: which seat or subagent, what state
  it is in, what it was waiting on.
- **Next actions** — immediate steps, most important first.
- **Open threads** — active but unsettled questions.
- **The round** — today's date, the run id, what this round is about, and
  whether a lock is held (often none is, which is fine).

Keep this SHORT. A long handoff defeats the purpose; it is a pointer, not a
transcript.

## 2. Write down anything settled that is not written yet

Do not save this for `/round`. If something was genuinely settled during this
session — a fact confirmed, an idea killed with its reason — put it in
`project/global/state.md` now with a changelog line. A decision that exists only
in a context window you are about to discard is a decision the project loses.

Only promote what is ACTUALLY settled. Do not launder an in-flight guess into
truth: the whole value of `state.md` is that a claim in it has been through the
gate. Anything still in flight belongs in `session.md`, not `state.md`.

## 3. Freshen the subagent memories if they ran

If the Analyst or Replicator did work this session, make sure
`project/<author>/analyst.md` and `replicator.md` reflect it. They normally
self-update on return, but a run that was interrupted leaves them stale — capture
what is known so the next fresh spawn resumes correctly rather than redoing work.

Rewrite these compactly. A file that accumulates superseded blocks under a
"this is all stale now" banner is worse than useless: it reads as current.

## 4. Keep the lock

Do NOT release the round lock here. You are refreshing a context window, not
finishing a round — releasing it would hand the round to someone else in the
middle of your work.

Report where the round stands so the handoff is honest:

```bash
python3 -m tools.lock status
```

If it turns out the round IS finished and you were about to say so, run
`/round` instead of this command — it does the promotion and the release
properly.

## 5. Hand off

Tell the user plainly:

> Memory checkpointed, round still going. Run `/clear` (or start a new session),
> then say `resume`. I will re-read CLAUDE.md, `project/global/state.md` and my
> `session.md` and continue with a fresh context window — nothing is lost.

Do NOT try to clear context yourself, and do not keep working after this. Stop,
so the human can `/clear`.
