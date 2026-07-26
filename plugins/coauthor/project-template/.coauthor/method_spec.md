# Method spec — round <n> (FROZEN <date>)

The single implementable specification for this round's empirics, written by the
Coordinator with the Proposer and Adversaries BEFORE the Analyst and Replicator are
spawned. Both of them implement THIS. Nothing headline-moving is left open. A
`DECISION NEEDED` raised by either implementer is resolved here and the round
re-synced against the update.

(This file is regenerated each empirical round. Rounds that don't turn on a number
leave it as-is.)

## Estimand / headline
- The exact quantity, and the comparisons that decide the round.

## Sample & screens
- Universe, dates, exclusions, the panel unit, point-in-time rules, held-out set.

## Variables / features
- Each feature: exact definition, source field, transform, winsorization (level,
  side, and within what group), missing-value handling. State hard exclusions
  explicitly (e.g. no size/market/target-derived inputs).

## Estimator + every baseline
- The estimator, fully. Each baseline's EXACT construction: matching variables,
  distance, #peers, tie-breaking, backoff.

## Learner
- Family, objective/loss (named — e.g. L1 to match a median-error metric),
  hyperparameters OR the shared tuning protocol (search space, seed, budget,
  selection rule).

## Cross-validation
- The exact scheme. For a firm panel: grouped by the panel unit (never a random
  split, which leaks within-unit persistence). #folds, seed.

## Evaluation
- Frame (e.g. contemporaneous cross-sectional leave-one-out vs temporal split),
  metric, aggregation, inference (clustering / bootstrap), and the tolerance within
  which the Analyst's and Replicator's numbers count as "converged".

## Non-negotiables
- The discipline rules whose violation invalidates the run.
