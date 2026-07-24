---
description: End a coauthor session safely — write all durable state to .coauthor/ so nothing is lost, then it's safe to /clear or close. Always run this before /clear.
argument-hint: ""
---

You are the Coordinator. The user is stopping. `/clear` and closing the session
save NOTHING on their own — they wipe context. Your job here is to make sure
everything worth keeping is written to `.coauthor/` FIRST, so the user can safely
leave.

## 1. Promote what has settled
Move settled results out of working memory into the durable, committed record:
- Into `.coauthor/state.md`: confirmed thesis changes, newly settled facts (with
  litdb `\cite{}` keys), killed ideas (with reasons), replicated empirical results.
- Into litdb notes: settled facts/decisions, linked to their papers.
Promote only what is actually settled — don't launder in-flight guesses into truth.

## 2. Rewrite the handoff (`.coauthor/session.md`), compact
Write it so a cold-start session resumes from it alone: "Where we are", "In flight"
(unfinished work + which seat/subagent + its state), "Next actions", "Open
threads", and stamp "Last session" with today's date and the last round number.
Drop anything you just promoted. Keep it short.

## 3. Freshen agent state if they ran
If the Analyst or Replicator worked this session and a run was cut short, capture
what's known in `.coauthor/analyst.md` / `.coauthor/replicator.md` so their next
fresh spawn resumes correctly.

## 4. Confirm it's safe to leave
Tell the user, plainly:
"State saved to `.coauthor/` — `state.md`, `session.md`, and any litdb notes. It is
now safe to `/clear` or close the session. To pick up later, open coauthor here and
I'll read `.coauthor/state.md` + `.coauthor/session.md` and continue where we left
off."

Then STOP. Do not keep working, and do not attempt to `/clear` yourself (you
can't — only the human can).

## Relationship to /coauthor:refresh
Same state write; different intent. `/coauthor:stop` = done for now (then `/clear`
or close). `/coauthor:refresh` = keep going with a fresh window (write, then
`/clear`, then resume the same arc).
