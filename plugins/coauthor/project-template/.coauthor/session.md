# Session handoff — <PROJECT_NAME>

Working memory for the Coordinator (orchestrator). The Coordinator reads this at
the START of every session, right after `state.md`, and rewrites it at every
human gate and when you stop. It is the anti-amnesia file: keep it current and
compact. This is NOT the paper's truth (`state.md` is) — this is "where we are
right now."

Compaction rule: on startup, promote anything that has become settled into
`state.md` / litdb, then delete it from here. This file should stay short — if it
is growing without bound, it has not been compacted.

## Where we are
<one-paragraph status: the current focus and what just happened. Empty until the
first session.>

## In flight
<work started but not finished — a debate mid-stream, an empirical result awaiting
replication, a verification pending. Each item: what, who (which seat/subagent),
and its current state.>

## Next actions
- <the immediate next steps, most important first, so a fresh session can resume
  without re-deriving the plan>

## Open threads (not yet settled)
<questions and ideas being actively worked but not ready to promote to state.md.
When one settles, move it to state.md and remove it here.>

## Last session
<date + round number last completed, written by the Coordinator when you stop, so
startup knows how fresh this file is.>
