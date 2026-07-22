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

4. Create it:
   ```
   "$LITDB_PY" -m litdb add-note --title "T" --body "…" \
       [--link PAPER_ID ...] [--relation about] [--confidential]
   ```
   For a long body, pass `--body -` and pipe the text on stdin.

5. Embed so the note is searchable: `"$LITDB_PY" -m litdb embed`.

To link an existing note to another paper later:
`"$LITDB_PY" -m litdb link --note NOTE_ID --paper PAPER_ID [--relation R]`.
