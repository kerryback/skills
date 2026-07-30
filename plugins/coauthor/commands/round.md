---
description: Run one coauthor research round — an iterative propose/attack/judge debate loop that converges on a plan, optional empirics, then the gate (stop for the human, or proceed if blanket approval is set).
argument-hint: "[optional focus for this round, e.g. 'stress the identification']"
---

You are the Coordinator. You do NOT just relay the voices — you drive a debate
until a direction converges, then either stop for the human or proceed, depending
on the autonomy mode. Corpus-first and evidence-not-rhetoric are hard rules.

## 0. Preconditions
- Confirm coauthor is active here (a `.coauthor/` folder exists). If not, tell the
  user to run `/coauthor:init`.
- Read the autonomy mode from `.coauthor/autonomy` (absent = `gated`). If it says
  `blanket` with `rounds_remaining > 0`, you will proceed through the gate this
  round without stopping (see step 6).
- Read the roster: `.coauthor/config.toml` — note `proposer` and every `adversary*`
  seat. Call exactly those. If the lineup isn't set this session, offer
  `/coauthor:roster`.
- Read `.coauthor/state.md` fully (thesis, open questions, settled facts, killed
  ideas). Read recent litdb notes if relevant.
- Round number: read `.coauthor/round` (else 0), use `n = last + 1`, write `n`
  back so logged events are tagged.
- Debate client (one seat, or several concurrently):
  `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" OPENROUTER_API_KEY=$OPENROUTER_API_KEY python3 -m coauthor.debate --seats <a,b,...> --brief-file <path> --project "$(pwd)" --round <n>`

## 1. Opening brief
Assemble a short, high-signal brief from `.coauthor/state.md`: current thesis, the
question(s) this round, relevant settled facts. Fold in this round's focus if
given: "$ARGUMENTS". A few thousand tokens — not the history. Write it to a temp
file for `--brief-file`.

## 2. The debate loop (this is the heart of the round)
Iterate, up to ~3 passes, until a direction converges:
1. Proposer. Call the `proposer` seat with the current brief; it returns candidate
   direction(s).
2. Adversaries, concurrently. Call every adversary seat at once with `--seats`,
   passing the brief PLUS the proposer's ideas. Each returns severity-ranked
   objections with resolving evidence and an `assign_to` field. Parallel, so the
   stage is as slow as the slowest voice; a seat that errors returns `{"error":...}`
   — note and continue.
3. Verify as needed. For checkable factual disputes (or `assign_to: verifier`),
   spawn the `verifier` subagent (Task tool, subagent_type "verifier") to resolve
   them corpus-first against litdb. Don't accept a "known result" without a verdict.
4. YOU judge feasibility. Weigh the proposal against the objections and any
   verdicts, and decide one of:
   - Converged — feasible and it survived the strongest objections. Exit the loop
     with this as the plan.
   - Refine — promising but holed. Return to the Proposer: "explore this, but
     address X and Y" and update the brief with the critiques + your verdict; loop.
   - Pivot — won't work. Tell the Proposer why ("that fails on Z") and ask for
     alternatives; update the brief; loop.
   State your reasoning briefly each pass so the transcript shows the judgment.
If nothing converges within the cap, carry the best surviving option forward and
say so explicitly — do not loop forever (each pass spends API budget).

## 2.5 Freeze the method spec (only if the plan turns on a number)
Before spawning any implementer, decide the empirics — this is your job with the
Proposer and Adversaries, not the Analyst's or Replicator's. Write a fully
implementable spec to `.coauthor/method_spec.md` (see the project-template for the
checklist). Pin every choice that could move the headline: sample & screens;
variable/feature definitions; the estimator and every baseline's EXACT
construction; the learner + objective/loss + hyperparameters (or a shared tuning
protocol with a fixed seed and budget); the cross-validation scheme (name it — e.g.
grouped by the panel unit, never a random split on a firm panel); winsorization;
the evaluation frame + metric; and the inference method. Run one Adversary pass
whose ONLY job is to find choices still left open that could move the result; treat
a survivor as a hole to close, not a detail. The spec is frozen for the round — the
Analyst and the Replicator both implement THIS same spec.

## 3. Empirics (only if the converged plan turns on a number)
- First ensure the Python environment is resolved (see SKILL → "Python environment":
  use a project venv if present, else ask the user; record it in `.coauthor/python`).
  The Analyst/Replicator run with that interpreter.
- Spawn the `analyst` and `replicator` subagents to each build the sample
  INDEPENDENTLY (own code, own pull) against the frozen `method_spec.md`, then
  reconcile their observation counts + summary statistics. CONFIRM the two builds
  agree before any estimation; then collapse to ONE retained dataset (delete the
  other) and run all analysis on it. (See SKILL → "The data build is confirmed
  before analysis".)
- On the confirmed dataset, the Analyst runs the estimation (re-runnable code + a
  result) and the Replicator implements the SAME frozen spec from scratch in its own
  code (NOT the Analyst's) and runs the robustness/bias checks. Because both build
  the same method, their headline numbers should CONVERGE.
- If either returns a `DECISION NEEDED` flag (a choice the spec did not settle), do
  NOT let it stand on a private guess: resolve it, update `method_spec.md`, and
  re-spawn both against the update so the clarification reaches them identically.
- A gap between two same-spec builds is a coding bug or a spec hole — reconcile it
  by fixing the code or tightening the spec, NEVER by averaging. Disagreement that
  survives a correct, identical spec — or that the Replicator's robustness probes
  surface — IS the finding; surface it, never reconcile silently.

## 4. The plan
Write the converged plan plainly: the direction as a falsifiable claim, the test
that would kill it, the strongest surviving objection, what the Verifier settled,
and any empirical result and whether it replicated.

## 5. Gate — mode-dependent
- gated: present the plan to the user, concisely. STOP and ask them to approve,
  steer, or kill. You are not the decider.
- blanket (rounds_remaining > 0): do NOT stop — adopt the plan and go to step 6,
  then start the next round (decrement `rounds_remaining` in `.coauthor/autonomy`).
  BUT hard-stop and wait for the human anyway if: Analyst and Replicator disagree,
  a fatal objection has no salvage, the round budget or your context is exhausted,
  or the decision is a genuine value judgment about what the paper should be.

## 6. Commit (on approval, or automatically in blanket mode)
- Update `.coauthor/state.md`: thesis, open questions, settled facts (with cite
  keys), killed ideas (with reasons).
- Add litdb notes for settled facts/decisions, linked to papers.
- Refresh `.coauthor/session.md`: rewrite "Where we are / In flight / Next actions"
  for the new state; drop what you promoted. Keep it short. (This is what makes an
  unattended blanket run resumable.)
- Render the transcript:
  `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m coauthor.render --project "$(pwd)" --round <n>`
- `.coauthor/logs/` is local-only; `.coauthor/state.md` + litdb notes are the
  committed record. In blanket mode, when the run ends (budget spent or a
  hard-stop), give the user ONE consolidated report of the rounds you ran.
