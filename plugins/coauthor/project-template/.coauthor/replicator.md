# Replicator working state — <PROJECT_NAME>

The Replicator's private memory. The `replicator` subagent reads this when it
spawns and rewrites it before it returns. Keep it compact. Independence still
holds: this file records WHAT was checked and the verdicts — it must not become a
back channel for the Analyst's code (the Replicator re-derives from the design).

## Numbers checked
<each headline number independently re-derived: the claimed value, your value,
AGREE (within tolerance) / DISAGREE (with magnitude + hypothesis), and the date.>

## Bias checks run
<per result: look-ahead, survivorship/delisting, microcaps/value-weighting,
overlapping-return SEs, data-snooping, OpenAP pitfalls — with the outcome of each.>

## Outstanding
- <results claimed by the Analyst but not yet independently replicated>
- <bias checks still to run>

## Method notes
<your own independent constructions/data slices, so a fresh spawn re-uses its own
approach rather than re-inventing or drifting toward the Analyst's.>
