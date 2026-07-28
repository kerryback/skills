# Add a note

Read and follow this when the user wants to capture a thought or note, optionally
tied to specific papers. `LITDB_PY` is resolved in SKILL.md.

Two ways in: draft it in chat and run `add-note` (below), or open the browser form
with the `/litdb:note` command (see `commands/note.md`) when the user would rather
compose a longer note, link several papers, or pin a page/quote in a UI. Offer the
form for anything substantial; use `add-note` for a quick one-liner.

## Steps

1. Draft the note from what the user said, in their voice. Give it a short title.
   If it has a clear type, set a `--kind`: `idea`, `summary`, `critique`,
   `question`, `todo`, or `quote`.

2. Links. If the note is about specific papers, find them first (see `search.md`)
   and propose linking with a relation label — `about`, `supports`, `contradicts`,
   `extends`, `uses-method`, `uses-data`. Propose the links and let the user confirm
   before creating several; don't link speculatively. To anchor the note to a spot
   in a paper, add `--page N` and/or `--quote "verbatim passage"` (these attach to
   the linked paper).

3. Confidential. If the note contains unpublished ideas, private critiques, or
   referee-confidential material, add `--confidential`. Confidential notes are
   only ever embedded with a local model, never a hosted API. When unsure, ask.

4. Project tag. By default the note is tagged with the current working directory's
   name. Infer that name and state it in one line — e.g. "Tagging this note to
   project _momentum-crashes_ (from your working folder); tell me if it belongs
   somewhere else." Proceed with the default unless the user redirects; when the
   inferred name is clearly right, don't block on a reply. If they name a different
   project (or several), pass `--project "<name>"` (repeatable, which overrides the
   default); if they want it untagged, pass `--no-project`.

5. Create it:
   ```
   "$LITDB_PY" -m litdb add-note --title "T" --body "…" [--kind summary] \
       [--link PAPER_ID ...] [--relation about] [--page N] [--quote "…"] \
       [--confidential] [--project "<name>" ... | --no-project]
   ```
   For a long body, pass `--body -` and pipe the text on stdin. The result echoes
   the `kind` and the `projects` the note was tagged with.

6. Embed so the note is searchable: `"$LITDB_PY" -m litdb embed`.

To link an existing note to another paper later:
`"$LITDB_PY" -m litdb link --note NOTE_ID --paper PAPER_ID [--relation R] [--page N] [--quote "…"]`.

## Reading notes back
- `"$LITDB_PY" -m litdb notes [--paper ID] [--kind K] [--project NAME] [--since DATE]`
  lists notes (newest first, full bodies). `notes --search "QUERY"` searches notes
  only (hybrid) and returns full notes. `note ID` shows one. Notes are read whole and
  come first when answering topic questions — see `search.md` step 0.
