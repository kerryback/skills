---
description: Checkpoint memory to disk and hand off to a fresh context window — write state, then you run /clear and resume with nothing lost.
argument-hint: ""
---

Your context window is getting long; refresh it. You CANNOT clear your own
context — this command runs inside the current session — so do the half you can
(write durable state cleanly), then hand off to the human to run `/clear`. On
resume, CLAUDE.md and the state files bring the next session up to speed.

Read `CLAUDE.md` if you have not already. Everything below assumes it.

## 1. Promote what has settled

Start by finding what the record is missing:

```bash
python3 -m tools.chronology --gap --human
```

That lists commits with no changelog entry dated after them — work whose reason
was never written down, usually from a session that ended without a `/refresh`.
Walk it. For each one, write the entry now if you can still reconstruct why;
name the ones you cannot, so the gap is known rather than invisible.

Then move anything now settled out of working memory into the durable record:

- Into `project/global/state.md` — confirmed thesis changes, newly settled facts,
  killed ideas WITH the reason they were killed, replicated empirical results.
  Add your entry to the changelog at the top with your author slug and the date
  (see the file's own header for the format).

Only promote what is ACTUALLY settled. Do not launder an in-flight guess into
truth: the whole value of `state.md` is that a claim in it has been through the
gate.

## 2. Rewrite your handoff, compact

Rewrite `project/<author>/session.md` so a cold-start session could resume from
it alone:

- **Where we are** — one paragraph of status.
- **In flight** — work started but unfinished: which seat or subagent, what state
  it is in, what it was waiting on.
- **Next actions** — immediate steps, most important first.
- **Open threads** — active but unsettled questions.
- **Last session** — today's date and the last round number.

Drop anything you promoted in step 1 — it lives in `state.md` now. Keep this
SHORT. A long handoff defeats the purpose; it is a pointer, not a transcript.

## 3. Freshen the subagent memories if they ran

If the Analyst or Replicator did work this session, make sure
`project/<author>/analyst.md` and `replicator.md` reflect it. They normally
self-update on return, but a run that was interrupted leaves them stale — capture
what is known so the next fresh spawn resumes correctly rather than redoing work.

Rewrite these compactly. A file that accumulates superseded blocks under a
"this is all stale now" banner is worse than useless: it reads as current.

## 4. Release anything you are holding

If you hold the round lock and the round is finished, release it — an unreleased
lock blocks the other two:

```bash
python3 -m tools.lock status
python3 -m tools.lock release
```

If the round is genuinely still in progress, keep it and say so in "In flight".

## 5. Hand off

Tell the user plainly:

> Memory checkpointed. Run `/clear` (or start a new session), then say `resume`.
> I will re-read CLAUDE.md, `project/global/state.md` and my `session.md` and
> continue with a fresh context window — nothing is lost.

Do NOT try to clear context yourself, and do not keep working after this. Stop,
so the human can `/clear`.
