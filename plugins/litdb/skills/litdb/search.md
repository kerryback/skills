# Running a search

Read and follow this when the user wants to find papers or notes, see what they
have on a topic, find new/outside work, or explore citations. `LITDB_PY` is
resolved in SKILL.md.

Core rule: search the user's own library FIRST. Only go to external sources when
the user explicitly asks for new/outside work or the library clearly lacks it.

## 0. Notes come first — two tracks

The user's own notes are their prior thinking and outrank papers. For any topic or
"what do I have / think / know on X" question, run TWO separate tracks and present
notes first, as their own section, then papers — never blend them into one ranked
list.

Notes track: a note is short and you want the whole thought, not a snippet, so
surface notes and READ THEM IN FULL.
- If few notes are in scope, just read them all — `"$LITDB_PY" -m litdb notes`
  (optionally `--project NAME`, `--kind K`, `--paper ID`). No search needed.
- If there are many, shortlist by relevance and read those whole:
  `"$LITDB_PY" -m litdb notes --search "QUERY" -k 20` — hybrid keyword+semantic over
  notes only, returned as full note bodies (with each note's linked papers, kind,
  page/quote). Bias to recall (a generous `-k`); you're reading the surfaced notes,
  not trusting a top-1.
- Use your judgment on "few vs many" per request — there's no fixed threshold.

Then the papers track below (steps 1–3). Report what the notes say first, then the
supporting/relevant papers.

## 1. Search the library (do this first)

```
"$LITDB_PY" -m litdb search "QUERY" -k 10 [--type paper|note] [--year-min Y] [--status to_read] [--project NAME]
```
- Hybrid (keyword + semantic) automatically once the corpus is embedded; keyword
  otherwise. Force with `--mode keyword|hybrid`. If results seem thin and nothing
  is embedded, suggest running `embed`.
- Results are one per paper, each with `matched.kind` (`abstract` or `fulltext`)
  and, for full-text hits, `matched.page`, plus the `projects` it's tagged with.
  Report title, authors, year; include `citation_key` when present (for `\cite{}`),
  especially if `uses_tex` is set.
- `--project NAME` scopes results to one project/topic (the tag set by folder
  ingest or note capture). Use it when the user frames a request around a project —
  "in my momentum-crashes project, what do I have on …". An unknown name warns and
  returns nothing rather than silently searching everything. To see the available
  projects and their counts: `"$LITDB_PY" -m litdb projects list`. Manage tags with
  `projects tag NAME --paper ID --note ID`, `projects untag …`, and
  `projects rename OLD NEW` (folds into an existing target).

## 2. External discovery (only when needed)

- Corpus-first combined view: `"$LITDB_PY" -m litdb discover "QUERY"` returns
  `{local, external_new}` — what they have plus new candidates.
- External only: `"$LITDB_PY" -m litdb external-search "QUERY" [--source openalex|s2|both] [--year-min Y]`.
  Each result is annotated `in_corpus`.
- Default source is OpenAlex (free, no key). Semantic Scholar may rate-limit
  anonymous requests (429) — if so, say so and fall back to OpenAlex.
- Importing: propose candidates and import only what the user confirms or what is
  clearly central. Bulk: `external-search "QUERY" --import`; single:
  `import-doi <doi>`. Then run `embed` so new papers are searchable.
- Getting the full text, not just metadata. Importing (above) stores a paper's
  metadata + abstract only — its `location` stays `not downloaded` and full text is
  not searchable. litdb itself never downloads PDFs, but YOU (Claude) can, and
  should, fetch a free copy before falling back on the user:
  1. Only for non-paywalled papers. Use WebSearch to find a freely available PDF —
     an open-access journal copy, a preprint (arXiv/SSRN/NBER/RePEc), or the
     author's page; use WebFetch on a landing page to locate the actual PDF link.
     Never try to bypass a paywall or use pirate sources (e.g. Sci-Hub).
  2. Download it with Bash (`curl -L -o <file>.pdf <url>`), NOT WebFetch (which
     returns processed text, not the binary). Save it in the paper's project folder
     (the per-project convention in SKILL.md — ask which folder if unsure), and
     confirm it really is a PDF before ingesting (the file starts with `%PDF`).
  3. Ingest into the existing record so no duplicate is created:
     `"$LITDB_PY" -m litdb ingest-pdf --paper <id> --file <path>`, then `embed`.
  4. If no free copy exists, say the paper is paywalled and ask the user to download
     it through their library login; once the file is on disk, ingest it the same
     way. Never present a paywalled paper as unavailable without checking for a free
     copy first.

## 3. Citation-graph exploration

Build edges first (once per paper or corpus): `"$LITDB_PY" -m litdb cite-fetch --all`
(or `--paper ID`). Then:
- `"$LITDB_PY" -m litdb refs --paper ID` — the paper's references (annotated with
  what the user holds).
- `"$LITDB_PY" -m litdb cited-by --paper ID` — works citing the paper.
- `"$LITDB_PY" -m litdb most-cited` — papers most cited within the user's library.
- `"$LITDB_PY" -m litdb missing-refs` — papers the library references most but the
  user doesn't own. This is the best answer to "what should I read/add next"; each
  has a DOI to `import-doi`.
