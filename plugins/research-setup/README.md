# research-setup

Sets up a research repository that several people — and their Claudes — can work
in without tripping over each other, then writes the `CLAUDE.md` that keeps it
that way.

```
/research-setup
```

Claude interviews you, scaffolds the structure, wires the tooling, verifies it
works, and explains it in two minutes.

## What it prevents

Research repos fail in the same few ways, and each one is cheap to prevent and
expensive to fix later:

- **Paths that name one person's home directory**, so nobody else can run the
  code. Four roots, all derived — from an env var, from the script's own
  location, from walking up to `CLAUDE.md` — and no absolute path anywhere.
- **The shared dataset living in whoever built it's folder.** One canonical
  store, read-only, with promotion recorded: hash, shape, who, and why it is
  trusted.
- **Two people rewriting the same prose file.** The round is claimed through git,
  which makes a push an atomic mutex, so exactly one claim wins and the loser
  finds out immediately rather than at merge time.
- **Nobody knowing which script produced a number.** The dependency graph is read
  out of the code — who wrote each file, what it read, what breaks if it changes
  — and runs are recorded as they happen.
- **A structure only its author understands.** The generated `CLAUDE.md` states
  the rules, and a session-start check tells Claude whether the person in front
  of it is set up, so onboarding is something Claude performs rather than a
  README nobody reads.

## What you choose

- **Empirical or not.** If empirical, it scaffolds an analyst/replicator split
  and the two-build protocol: independent builds, reconcile, confirm before
  analysis, collapse to one, never average a disagreement. A theory project skips
  all of it rather than getting two empty directories.
- **A debate panel or not.** Independent model voices that propose and attack
  ideas through OpenRouter. Each coauthor needs their own key and pays for their
  own calls, so it is off unless you ask.
- **Overleaf or not.** For teams where some coauthors write in Overleaf and some
  do not. It mirrors `draft/` — and only `draft/` — into an Overleaf project
  through the git bridge, so the Overleaf people get a normal Overleaf project,
  everyone else keeps a normal git repo, and one person holds both. Claude does
  the syncing, so nobody has to learn `git subtree` to write a paper.

## What it deliberately does not do

No activity log. Recording every tool call is occasionally useful and usually
noise. What is kept is a record of *runs* — one line per execution, with inputs,
outputs, and the commit — because that is what answers "which run produced this
number" a year later.

## Existing projects

It adapts one too, in an order chosen so a mistake surfaces before more moves are
stacked on it: paths first, verified by re-running something whose answer is
already known; then data out of the repo; then the per-author split; then
archiving what is superseded. Commit between steps.
