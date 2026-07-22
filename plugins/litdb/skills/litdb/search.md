# Running a search

Read and follow this when the user wants to find papers or notes, see what they
have on a topic, find new/outside work, or explore citations. `LITDB_PY` is
resolved in SKILL.md.

Core rule: search the user's own library FIRST. Only go to external sources when
the user explicitly asks for new/outside work or the library clearly lacks it.

## 1. Search the library (do this first)

```
"$LITDB_PY" -m litdb search "QUERY" -k 10 [--type paper|note] [--year-min Y] [--status to_read]
```
- Hybrid (keyword + semantic) automatically once the corpus is embedded; keyword
  otherwise. Force with `--mode keyword|hybrid`. If results seem thin and nothing
  is embedded, suggest running `embed`.
- Results are one per paper, each with `matched.kind` (`abstract` or `fulltext`)
  and, for full-text hits, `matched.page`. Report title, authors, year; include
  `citation_key` when present (for `\cite{}`), especially if `uses_tex` is set.

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
