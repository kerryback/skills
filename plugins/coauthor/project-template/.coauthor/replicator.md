# Replicator working state — <PROJECT_NAME>

The Replicator's private memory. The `replicator` subagent reads this when it
spawns and rewrites it before it returns. Keep it compact. Independence still
holds: this file records WHAT was checked and the verdicts — it must not become a
back channel for the Analyst's code (the Replicator implements the same frozen
`method_spec.md` in its own code).

## Numbers checked
<each headline number independently re-implemented from the frozen spec: the
claimed value, your value, AGREE (within tolerance) / DISAGREE (with magnitude +
hypothesis: a coding bug or a spec hole), and the date.>

## Bias checks run
<per result: look-ahead, survivorship/delisting, microcaps/value-weighting,
overlapping-return SEs, data-snooping, OpenAP pitfalls — with the outcome of each.>

## Outstanding
- <results claimed by the Analyst but not yet independently replicated>
- <bias checks still to run>

## Spec gaps raised
<any `DECISION NEEDED` you returned (unspecified choice + why it matters) and how
the Coordinator resolved it in the spec — so a fresh spawn doesn't re-raise it.>

## Implementation notes
<your own code structure and data pull for implementing the frozen spec, plus the
extra constructions your robustness/bias probes use — so a fresh spawn re-uses its
own approach rather than re-inventing it. NOT a different method for the headline.>
