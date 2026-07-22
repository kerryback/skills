# Add papers to the library

Read and follow this when the user wants to add a folder of PDFs or import a
Zotero library. `LITDB_PY` is resolved in SKILL.md. Always `embed` after adding
papers so they become semantically searchable.

## A folder of loose PDFs on disk

1. Get the folder path from the user.
2. Run: `"$LITDB_PY" -m litdb scan-pdfs "<folder>" --embed`
   - It walks the folder, reads each PDF's opening pages, finds the DOI, resolves
     full metadata from OpenAlex, creates the paper (deduped on DOI), and ingests
     the full text as searchable chunks. `--embed` embeds the new papers.
3. Report the outcome from the JSON `summary`: how many `resolved`, how many
   `unresolved`, any `errors`.
4. Unresolved PDFs (no findable DOI — older scans, working papers) are listed but
   NOT added. Recommend routing those through Zotero's "Retrieve Metadata for
   PDF" (best for DOI-less/scanned files). Only if the user wants them searchable
   right now, re-run with `--keep-unresolved` to add them as filename-titled
   records they can fix later.
5. Confirm with `status` and a sample `search`.

Large folders take a while (one OpenAlex lookup per PDF); `--limit N` processes a
first batch if the user wants a quick trial.

## An existing Zotero library

1. Preferences: `import-zotero` already honors `use_better_bibtex`; you don't need
   to pass flags unless the user overrides (`--bbt` / `--no-bbt`).
2. Run: `"$LITDB_PY" -m litdb import-zotero --local`
   - Uses Better BibTeX automatically when available (capturing citation keys),
     else the Zotero local API.
   - The result reports `source` and `with_citation_key`; relay those.
3. If Zotero isn't running or has no papers, guide the user: open Zotero, install
   the Zotero Connector browser extension, and add papers (click the connector on
   a paper's page, or use "Add Item by Identifier" with a DOI).
4. Embed: `"$LITDB_PY" -m litdb embed`.

## After importing

Offer to build the citation graph for the new papers (`cite-fetch --all`) and, if
useful, show `missing-refs` — papers the collection references but doesn't own.
