---
description: Checkpoint the Coordinator's memory and hand off to a fresh context window — write state, then you run /clear and resume with no lost progress.
argument-hint: ""
---

You are the Coordinator. Your context window is getting long; refresh it. You
CANNOT clear your own context — a command runs inside the current session. So do
the half you can (write durable state cleanly), then hand off to the human to run
`/clear`. On resume the skill re-reads the files below and continues fresh.

## 1. Promote what has settled
Move anything now settled out of working memory into the durable record:
- Into `.coauthor/state.md`: confirmed thesis changes, newly settled facts (with
  litdb `\cite{}` keys), killed ideas (with reasons), replicated empirical results.
- Into litdb notes: settled facts/decisions, linked to their papers.
Only promote what is actually settled — do not launder in-flight guesses into truth.

## 2. Rewrite the handoff (`.coauthor/session.md`), compact
Rewrite it so a cold-start session could resume from it alone:
- "Where we are" — one-paragraph status.
- "In flight" — work started but unfinished (which seat/subagent, current state).
- "Next actions" — the immediate steps, most important first.
- "Open threads" — active but unsettled questions.
- "Last session" — stamp today's date and the last round number.
Drop anything you just promoted in step 1. Keep it SHORT — this is the whole point.

## 3. Freshen agent state if they ran
If the Analyst or Replicator did work this session, make sure `.coauthor/analyst.md`
/ `.coauthor/replicator.md` reflect it (they normally self-update, but if a run was
cut short, capture what's known so their next fresh spawn resumes correctly).

## 4. Hand off
Tell the user, plainly:
"Memory checkpointed to `.coauthor/`. Run `/clear` (or start a new session), then
send `resume` or `/coauthor:round`. I'll re-read `.coauthor/state.md` and
`.coauthor/session.md` and continue with a fresh context window — nothing is lost."

Do NOT attempt to clear context yourself, and do not keep working after this —
stop so the human can `/clear`.
