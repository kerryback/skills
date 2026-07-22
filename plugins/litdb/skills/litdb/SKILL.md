---
name: litdb
description: Personal literature and notes knowledge base. Use whenever the user wants to search their own papers/library, add papers (a folder of PDFs or a Zotero library), capture notes tied to papers, triage reading, find new work on a topic, or explore citations — e.g. "what do I have on momentum crashes", "add this folder of PDFs", "import my Zotero library", "add a note about this paper", "what should I read next on X". Always search the user's own corpus before any external source. Backed by a local SQLite store with keyword + semantic (hybrid) search; driven through the litdb CLI.
---

# litdb

A per-user, local, private knowledge base of the user's papers and notes —
keyword, semantic, and hybrid search, plus external discovery and a citation
graph. You operate it through the `litdb` CLI. Search the user's own corpus
before reaching for any external or web source.

This file is a router: it handles session start and points to a task file for
each kind of request. Read the matching task file with your file tool before
acting — don't guess the steps.

## Start of every session

1. Resolve the runtime. litdb runs from a fixed virtualenv in the litdb home,
   `~/.litdb`. The interpreter (call it LITDB_PY) is `~/.litdb/.venv/bin/python`
   (macOS/Linux) or `~/.litdb/.venv/Scripts/python.exe` (Windows). If it does not
   exist or `"$LITDB_PY" -m litdb --help` fails, invoke the `litdb-setup` skill,
   then retry. Use `"$LITDB_PY" -m litdb …` for every command. The home does not
   depend on any project or repo folder.

   The task files referenced below (`onboarding.md`, `add-folder.md`, etc.) live
   in this skill's own directory — the folder containing this SKILL.md (call it
   SKILL_DIR). Read them from there.

2. Check onboarding: `"$LITDB_PY" -m litdb onboarded`.
   - `{"onboarded": false}` → read `SKILL_DIR/onboarding.md` and follow it. It
     records preferences and marks onboarding complete at the end.
   - `{"onboarded": true}` → load preferences with `"$LITDB_PY" -m litdb prefs`
     and honor them for the rest of the session (see below).

## Preferences

Per-user preferences are stored by the app and read with `litdb prefs`
(no args lists all; `prefs KEY` gets one; `prefs KEY VALUE` sets one). Honor
them:

- `uses_tex` — the user writes LaTeX. When true, surface `citation_key` values
  so they can `\cite{…}`.
- `use_better_bibtex` — whether to use Better BibTeX for Zotero imports. The
  `import-zotero` command already honors this automatically.
- Whenever the user states a durable preference about how litdb should behave
  (default search scope, verbosity, a preferred source, etc.), record it:
  `"$LITDB_PY" -m litdb prefs set <key> <value>`.

## Routing — when the user wants to…

Read the named file from SKILL_DIR (this skill's own directory) before acting.

| …do this | read and follow |
|---|---|
| add a folder of PDFs, import Zotero, get papers in | `SKILL_DIR/add-folder.md` |
| capture a note / a thought about a paper | `SKILL_DIR/add-note.md` |
| find papers, search, "what do I have on…", find new work, what to read next | `SKILL_DIR/search.md` |

For anything else (triage/reading status, showing a paper, corpus stats), use the
CLI directly — see the reference below.

## Conventions (always)

- Corpus-first: search the user's library before any external/web source.
- The CLI prints JSON by default; parse it. Add `--human` when showing the user.
- Propose note↔paper links and important imports; let the user confirm.
- Confidential notes stay local and are never sent to a hosted embedder.
- Installing dependencies: when something litdb needs is missing — a Python
  package, `uv`, Ollama and its embedding model, or Better BibTeX — do not just
  print the command for the user to run. Ask whether they'd like you to install
  it; if yes, run the install yourself (via the shell) and report the result; if
  no, give them the command. The one step you cannot fully automate is the final
  Zotero GUI click for the Better BibTeX add-on — offer to download the `.xpi`
  and walk them through that last step. Never install silently; always ask first.

## Command reference

`init, import-zotero, scan-pdfs, import-doi, external-search, discover, search,
embed, add-note, link, screen, list, paper, ingest-pdf, cite-fetch, refs,
cited-by, most-cited, missing-refs, prefs, onboarded, status`. Every command
supports `--human`; see README.md for the full table.
