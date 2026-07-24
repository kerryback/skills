---
description: Set how much the Coordinator does without stopping — gated (ask at every round) or blanket approval for N unattended rounds. Controls the /coauthor:round gate.
argument-hint: "gated | blanket [N rounds, default 5]"
---

Set the autonomy mode, stored in `.coauthor/autonomy` and read at the start of
every `/coauthor:round`. The argument is "$ARGUMENTS".

## Modes
- `gated` (default) — the Coordinator runs the debate loop to a converged plan,
  then STOPS at the gate for the user to approve, steer, or kill before mutating
  state or running the next round.
- `blanket [N]` — the user pre-approves N rounds. The Coordinator proceeds through
  the gate without stopping, updating state and chaining into the next round, up to
  the budget. Default N = 5 if unspecified.

## What to do
1. Confirm coauthor is active here (`.coauthor/` exists); else tell the user to
   run `/coauthor:init`.
2. Parse "$ARGUMENTS":
   - starts with `gated` (or `off`) → write `.coauthor/autonomy` as:
     `mode = gated`
   - starts with `blanket` (or `on`) → read the optional integer (default 5) and
     write:
     ```
     mode = blanket
     rounds_remaining = <N>
     ```
   - empty → report the CURRENT mode from `.coauthor/autonomy` (say `gated` if the
     file is absent) and do not change anything.
3. If you just enabled blanket, warn the user plainly: the Coordinator will now run
   up to N rounds unattended — spending OpenRouter (and possibly WRDS) on each — and
   will still hard-stop for an Analyst/Replicator disagreement, a fatal unsalvageable
   objection, budget/context exhaustion, or a genuine value judgment. State is
   written every round, so the run is resumable and safe to leave.
4. Confirm the new mode (and remaining rounds) back to the user.

## Notes
- Blanket is consumed as it runs: `/coauthor:round` decrements `rounds_remaining`
  each round and reverts to gated behavior when it hits 0.
- The user can also grant blanket inline at a gate ("go ahead, blanket approval for
  5 rounds") — write the same file when they do.
- Turn it off anytime with `/coauthor:autonomy gated`.
