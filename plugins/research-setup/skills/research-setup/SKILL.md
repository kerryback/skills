---
name: research-setup
description: Set up a research repository that several people and their Claudes can work in without tripping over each other — per-author folders, portable paths, a single canonical dataset, provenance, a round lock, and a generated CLAUDE.md. Use when starting a new empirical or theoretical research project, when a solo project is about to gain coauthors, or when an existing project's files have grown organically and need structure. Also use when asked to "set up a research project", "add coauthors to this project", or "make this repo work like the multiples project".
---

You are setting up a research repository. The output is a working structure plus
a `CLAUDE.md` that makes it self-explaining, so the next session — anyone's —
knows the rules without being told.

Do not scaffold first and ask later. Interview, then build, then verify, then
explain what you did.

## What this is for

Research projects rot in predictable ways. Paths hardcode one person's home
directory. The dataset everyone depends on lives in whoever happened to build
it's folder. Two people rewrite the same prose file and git cannot merge it.
Nobody can say which script produced a number, or what breaks if a script
changes. This scaffolds the structure that prevents each of those.

It does NOT set up a general-purpose activity log. Recording every tool call is
occasionally useful and usually noise; what is kept here is a record of *runs* —
one line per script execution, with inputs and outputs — because that is what
answers "which run produced this number" a year later.

## 1. Interview

Ask these before touching the filesystem. Use `AskUserQuestion` where the options
are closed; ask in prose where they are not.

1. **Project name.** Becomes the folder name, the env var prefix, and the title
   of the generated docs. Derive a slug (lowercase, hyphens) and an ENV PREFIX
   (uppercase, underscores) and show both back. `Housing Supply` →
   `housing-supply`, `HOUSING_SUPPLY_DATA`.
2. **One line on what the project is.** Goes at the top of `CLAUDE.md` and
   `protocols.html`. Not a paragraph.
3. **Who is working on it?** Full names. Their slugs come from
   `git config user.name` on their own machines, so tell them what slug each name
   will produce and confirm it now — it is the single most common thing to get
   wrong, and it fails silently.
4. **Is there an empirical component?** If yes, scaffold `analyst/` and
   `replicator/` and include the two-build protocol. If it is theory or a
   literature project, skip both — a theory paper with two empty directories and
   a protocol that does not apply to it is worse than neither.
5. **Where does the data live?** A path outside the repo — a shared Dropbox or
   Box folder, a group drive. Data is not committed. If there is no data at all,
   say so and skip the data sections entirely.
6. **A debate panel?** Independent model voices that propose and attack ideas,
   through OpenRouter. Explain the cost honestly: each coauthor needs their own
   key and pays for their own calls. Default to no unless they want it.
7. **Existing files?** If the repo already has work in it, ask what is live and
   what is superseded. Do not move anything until they have answered.

## 2. Build

Create only what the interview asked for.

```
project/global/{state.md,method_spec.md,data_manifest.md}
project/<author>/{session.md,logs/}
workspaces/global/params.py            (empirical only)
workspaces/<author>/{analyst,replicator}/   (empirical only)
draft/{figures,tables}/
tools/                                 copied from this plugin
.claude/commands/refresh.md
CLAUDE.md  protocols.html  requirements.txt  .gitignore
```

Assemble `CLAUDE.md` from `templates/CLAUDE.md.tmpl`, substituting:

| Placeholder | With |
|---|---|
| `@@PROJECT@@` | the project name |
| `@@ONE_LINE@@` | their one-line description |
| `@@DATA_ENV@@` | `<PREFIX>_DATA` |
| `@@PREFIX@@` | the env prefix |
| `@@EMPIRICAL_SECTIONS@@` | `templates/fragments/empirical.md`, or empty |
| `@@DEBATE_SECTION@@` | `templates/fragments/debate.md`, or empty |
| `@@WRITING_SECTION@@` | `templates/fragments/writing.md`, or empty |
| `@@ROLES@@`, `@@AUTHOR_MEMORY@@`, `@@WORKSPACE_TREE@@`, `@@INDEPENDENCE_NOTE@@`, `@@ONBOARD_EXTRA@@` | see the fragments; write the empirical or the plain variant |

Substitute the same `@@DATA_ENV@@` into the copied `tools/*.py`. Leave no `@@`
marker anywhere — grep for them before you finish.

Then, in the repo:

- `git init` if needed, and `git config core.hooksPath tools/githooks`.
- Create the venv and install `requirements.txt`.
- Add the data root and any keys to the user's shell profile — **ask first**, and
  back the file up before you edit it.
- Make the author's data folder and the `global/` sibling.

## 3. Verify — do not skip this

A scaffold that has not been exercised is a guess. Before you report success:

```bash
python3 tools/onboard.py                      # must print ready
python3 -m tools.provenance --authors         # must list the author trees
python3 -m tools.lock status                  # must say unlocked
grep -rn "@@" CLAUDE.md tools/ protocols.html  # must find nothing
```

If there is data and any script, run one through `tools/runlog.py` and confirm a
line lands in `runs.jsonl`. If a check fails, fix it and say what was wrong —
never report a setup as working on the strength of having written the files.

## 4. Explain, briefly

Two minutes, in your own words: where their folders are, what is shared and what
is theirs, that `protocols.html` covers day-to-day use, and the one rule that
bites — their `git config user.name` names everything they own.

Do not read the generated `CLAUDE.md` at them. It is for you.

## Adapting an existing project

The same structure, applied to a repo that already has work, in this order:

1. **Paths first.** Find hardcoded absolute paths (`grep -rn "/Users/\|/home/"`).
   Rewrite them to the four roots. This is mechanical but it is where the risk
   is: verify by re-running something whose answer is already known, not by
   reading the diff.
2. **Then data out of the repo**, into the data root, with the canonical
   subset promoted to `global/`.
3. **Then the per-author split**, moving existing work into one author's tree.
4. **Then archive**: superseded subprojects into `archive/`, so what is live is
   legible. Ask which are which; do not infer it from timestamps, which a
   mechanical rewrite will have destroyed.

Commit between steps, not at the end. If step 1 breaks something, you want to
find it before three more moves are stacked on top.
