# Add a note

Read and follow this when the user wants to capture a thought or note, optionally
tied to specific papers. `LITDB_PY` is resolved in SKILL.md.

## Steps

1. Draft the note from what the user said, in their voice. Give it a short title.

2. Links. If the note is about specific papers, find them first (see `search.md`)
   and propose linking with a relation label — `about`, `critique`, `compares`,
   `extends`, `cites`. Propose the links and let the user confirm before creating
   several; don't link speculatively.

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
   "$LITDB_PY" -m litdb add-note --title "T" --body "…" \
       [--link PAPER_ID ...] [--relation about] [--confidential] \
       [--project "<name>" ... | --no-project]
   ```
   For a long body, pass `--body -` and pipe the text on stdin. The result echoes
   the `projects` the note was tagged with.

6. Embed so the note is searchable: `"$LITDB_PY" -m litdb embed`.

To link an existing note to another paper later:
`"$LITDB_PY" -m litdb link --note NOTE_ID --paper PAPER_ID [--relation R]`.
