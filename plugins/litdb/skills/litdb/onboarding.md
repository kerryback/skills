# litdb onboarding (first run)

Read and follow this only when `litdb onboarded` reports `false`. Keep it brief
and interactive — do steps for the user where you can, ask where their judgment
is needed, and never do the whole thing silently. Record answers as preferences
and mark onboarding complete at the end. `LITDB_PY` and `PLUGIN_ROOT` are as
resolved in SKILL.md.

## Steps

1. Runtime and database. Confirm `"$LITDB_PY" -m litdb status` works (invoke the
   `litdb-setup` skill first if the runtime isn't ready).

2. One or two sentences on what litdb is: a private, local, searchable library of
   the user's papers and notes, with semantic search, discovery, and citations.

3. TeX / Better BibTeX.
   - Ask: "Do you write your papers in TeX / LaTeX?"
   - Record it: `"$LITDB_PY" -m litdb prefs set uses_tex true|false`.
   - If yes, explain that the Better BibTeX add-on for Zotero gives every paper a
     stable citation key so litdb can hand you `\cite{key}`. Offer two choices:
     1. use Better BibTeX
     2. do not use Better BibTeX
     Record: `"$LITDB_PY" -m litdb prefs set use_better_bibtex true|false`.
     If they choose (1) and it isn't installed, offer to install it for them:
     with consent, download the latest `.xpi` from
     https://github.com/retorquere/zotero-better-bibtex/releases/ to a known
     location (e.g. `~/Downloads`), then walk them through the final GUI step
     (Zotero → Tools → Add-ons → gear → Install Add-on From File → pick the
     `.xpi` → restart). That last click is the only part you can't do for them.
   - If they don't use TeX, set `use_better_bibtex false` (citekeys aren't needed)
     unless they say otherwise.

4. Get papers in. Ask which fits, then follow the matching task file:
   - Loose PDFs scattered on disk → follow `add-folder.md`.
   - An existing Zotero library → follow `add-folder.md` (Zotero section).
   - Nothing yet / start fresh → seed by topic or DOI:
     `"$LITDB_PY" -m litdb external-search "<topic>" --import` or
     `"$LITDB_PY" -m litdb import-doi <doi>`.
   For a mixed situation (common), do the PDF folder first, then Zotero for the
   DOI-less stragglers.

5. Make it searchable and show it working: `"$LITDB_PY" -m litdb embed`, then a
   sample `"$LITDB_PY" -m litdb search "<their topic>" --human`.
   If `embed` reports an Ollama error (not running, or the model isn't pulled),
   offer to set it up for them: with consent, install Ollama (macOS:
   `brew install ollama`; Windows: `winget install Ollama.Ollama`; or the
   installer from https://ollama.com), start it, and run
   `ollama pull nomic-embed-text`, then retry `embed`. If they decline, note that
   search still works in keyword mode.

6. Optional (offer, don't force): build the citation graph and reveal gaps —
   `"$LITDB_PY" -m litdb cite-fetch --all` then `"$LITDB_PY" -m litdb missing-refs`.

7. Finish: `"$LITDB_PY" -m litdb onboarded --mark`. Preferences were already
   recorded via `prefs` in the steps above.

To re-run onboarding later, the user can run `litdb onboarded --reset`.
