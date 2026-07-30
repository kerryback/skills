# Analyst working state — <PROJECT_NAME>

The Analyst's private memory. The `analyst` subagent reads this when it spawns
(so it resumes instead of rebuilding context) and rewrites it before it returns.
Keep it compact — a curated state, not a log. The exhaustive record is in
`.coauthor/logs/`.

## Sample & screens built
<the sample currently constructed: universe, date range, inclusion/exclusion
filters, missing-data handling. State each decision once, here.>

## Data build reconciliation
<obs count + summary stats reported for the Coordinator's cross-check against the
Replicator's independent build; CONFIRMED? which copy was retained as the single
source of truth. Analysis runs only on the confirmed dataset.>

## Pipeline / scripts
<entry points in `workspace/code/` and what each produces. So a fresh spawn knows
what already runs and what to re-run.>

## Data quirks & gotchas
<things learned the hard way about the data sources for THIS project: join keys,
source vintages, variable conventions, timing/lag conventions.>

## Results produced (this arc)
<headline numbers made, each with the script that makes it and its status
(awaiting replication / replicated / superseded). Once promoted to state.md's
"Empirical results", drop it here.>

## TODO
- <next empirical steps>
