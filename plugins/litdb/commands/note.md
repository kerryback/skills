---
description: Capture a note in a browser form and save it to your litdb library, linked to papers. Opens a local form; on submit the note is stored and embedded.
argument-hint: "[paper id or search terms to pre-link]"
---

Capture a litdb note through the browser form, then confirm what was saved.

## Steps

1. Resolve the runtime. `LITDB_PY` is `~/.litdb/.venv/bin/python` (macOS/Linux) or
   `~/.litdb/.venv/Scripts/python.exe` (Windows). If litdb isn't set up, follow the
   litdb skill's `setup.md` first.

2. Work out a paper to pre-link, if any, from "$ARGUMENTS":
   - A bare integer is a paper id → pass `--paper <id>`.
   - Text → run `"$LITDB_PY" -m litdb search "<text>" -k 5`; on a confident single
     hit, pass its id as `--paper <id>`. Otherwise open the form with no prefill and
     let its picker find the paper.
   - No argument, but you're mid-conversation about a specific paper → pass that
     paper's id as `--paper <id>` so the form opens already linked to it.
   - You may pass `--paper` more than once, and `--project "<name>"` to preselect a
     project tag (default to the current project/topic if the conversation has one).

3. Launch the form (it opens a browser window on the user's machine and BLOCKS until
   they submit or close it):

   ```
   "$LITDB_PY" -m litdb note-form [--paper ID …] [--project "NAME"] --timeout 900
   ```

   Tell the user plainly: "A browser window is opening — write your note, optionally
   pick a kind, link one or more papers (with a page or quote), tag it, then click
   Save."

4. When it returns:
   - `{"submitted": false}` → nothing was saved; say so, don't invent a note.
   - Otherwise it returns the created note. Run `"$LITDB_PY" -m litdb embed` so the
     note is searchable by meaning (it is keyword-indexed at creation, but vector
     embedding happens on `embed`). Then confirm back: the note's kind, its linked
     papers (surface `citation_key`s when `uses_tex`), any page/quote, and its
     project tags.

## Notes
- The form is dependency-free (stdlib http.server); nothing to install. It reads the
  local litdb DB directly — the paper picker searches your library as you type.
- Confidential notes are embedded locally only.
- For a quick one-line note, `add-note --body "…"` in chat is faster; the form is for
  anything you'd actually want to reread or that links several papers.
