---
description: Turn on coauthor in the current directory — create a .coauthor/ folder (memory + state + config) and a workspace/ for empirics. Creates no repo, touches no other files.
argument-hint: "[project name — defaults to the current directory name]"
---

Activate coauthor in the directory you are in right now. coauthor is just a skill;
any directory can use it. "Active here" means a `.coauthor/` folder exists. This
command creates it. It does NOT create a repo, run `git`, or add any `CLAUDE.md`,
`README.md`, or other file at the root — coauthor keeps everything it owns inside
`.coauthor/`, with the sole exception of a `workspace/` folder for the analyst's
code/data/results (which you chose to keep first-class at the root).

## Steps
1. Name = the current directory's basename, unless the user passed "$ARGUMENTS".

2. If `.coauthor/` already exists here, coauthor is already active — say so, do not
   re-scaffold, and stop (offer `/coauthor:roster` or `/coauthor:round` instead).
   One exception: if `.coauthor/.gitignore` still ignores `logs/` wholesale, it
   predates run-stamped naming — the rendered transcripts are meant to be
   committed now. Offer to replace that one file with
   `${CLAUDE_PLUGIN_ROOT}/project-template/.coauthor/.gitignore`, then stop.

3. Copy the scaffold into the cwd, never clobbering existing files:
   `cp -Rn "${CLAUDE_PLUGIN_ROOT}/project-template/." .`
   This creates `.coauthor/` (state.md, session.md, analyst.md, replicator.md, and
   nested .gitignore) and `workspace/` (code/, data/, results/ with its own
   .gitignore). Nothing lands at the repo root except `workspace/`.

4. Replace the `<PROJECT_NAME>` placeholders in `.coauthor/*.md` with the name.

5. Roster: run `/coauthor:roster` so the user picks the debate lineup from the live
   OpenRouter catalog — it writes `.coauthor/config.toml`. (Or seed a starter by
   copying `${CLAUDE_PLUGIN_ROOT}/config.example.toml` to `.coauthor/config.toml`
   and tell them to run `/coauthor:roster` before the first round.)

6. Tell the user:
   - litdb must be installed — the Verifier depends on it (corpus-first). If it's
     not present, flag that verification won't work until it is.
   - Set `OPENROUTER_API_KEY` and `ANTHROPIC_API_KEY` in the environment. For
     empirical rounds, set up whatever data sources the project uses — connection
     details and credentials come from that project's data plugin/skill, not coauthor.
   - Then converse to set the working angle — you seed `.coauthor/state.md` and run
     a litdb discovery pass — and run `/coauthor:round` to start.

## Do not
- Do not `git init`, create a remote, or commit — the directory's version control
  (if any) is the user's, not coauthor's.
- Do not write `CLAUDE.md`, `README.md`, `project.yaml`, or any root file besides
  `workspace/`.
