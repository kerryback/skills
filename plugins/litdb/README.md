# litdb

A personal literature and notes knowledge base, distributed as a Claude Code
plugin. Per-user and local-first: import your Zotero library, keep notes linked
to papers, triage what to read, search everything by keyword and meaning, pull in
new work from OpenAlex / Semantic Scholar, read PDF full text, and explore the
citation graph — including which papers your library leans on but you don't own
yet.

The everyday interface is a stable CLI (`litdb …`) that a Claude skill drives;
an optional MCP server exposes the same operations as native tools.

---

## Highlights

- Local and private. One SQLite file per user. Confidential notes are never sent
  to a hosted embedding API.
- Hybrid search. BM25 (SQLite FTS5) fused with vector similarity via Reciprocal
  Rank Fusion; results deduplicated to one hit per paper and tagged with whether
  the match was in the abstract or the full text (with a page number).
- Swappable embeddings. Local by default (Ollama `nomic-embed-text`), or hosted
  (Voyage / OpenAI) with a config edit and a reindex. A zero-dependency `hash`
  provider makes search work before anything is set up.
- Zotero + Better BibTeX. Import from a running Zotero; when Better BibTeX is
  present it is used automatically and LaTeX citekeys are captured.
- External discovery. Search OpenAlex (free) and Semantic Scholar corpus-first;
  imports dedupe/merge on DOI, Zotero key, OpenAlex/S2 id, and citekey.
- PDF full text. Extract a paper's PDF (pure-Python) into page-anchored chunks so
  the body is searchable, not just the abstract.
- Citation graph. References, citers, most-cited-in-your-library, and
  `missing-refs` — the papers your collection cites most but you haven't added.
- Portable. Pure-standard-library core; optional extras are pure-Python wheels.
  Works the same on macOS and Windows.

---

## Install

Requires Python 3.10+.

Install as a Claude Code plugin (recommended). litdb is published in the
`kerryback/skills` marketplace. One-time, then the skill self-bootstraps its
runtime on first use:

```
claude plugin marketplace add kerryback/skills
claude plugin install litdb@kerryback-skills
```

That's it — Claude Code discovers the `litdb` skill. The first time you use it,
the skill runs `litdb-setup`, which builds the runtime in a fixed per-user home,
`~/.litdb` (venv at `~/.litdb/.venv`, database at `~/.litdb/litdb.db`). Nothing
depends on any project or repo folder. To update: `claude plugin update
litdb@kerryback-skills`.

Install from source (development). litdb lives in the `kerryback/skills`
marketplace repo, under `plugins/litdb`:

```bash
git clone https://github.com/kerryback/skills && cd skills/plugins/litdb
python3 scripts/setup.py --check     # report what's present/missing
python3 scripts/setup.py             # dry-run plan (changes nothing)
python3 scripts/setup.py --yes       # build the runtime into ~/.litdb
```

`setup.py` only builds the runtime (venv + package, non-editable so the checkout
is disposable; `--editable` for dev). It never installs system software for you.

Optional pieces:

- Semantic search: install [Ollama](https://ollama.com) and `ollama pull nomic-embed-text`.
- Better BibTeX (recommended for LaTeX users): install the `.xpi` from
  https://github.com/retorquere/zotero-better-bibtex/releases/ via Zotero →
  Tools → Add-ons → Install Add-on From File, then restart Zotero.

The managed interpreter is `~/.litdb/.venv/bin/python` (macOS/Linux) or
`~/.litdb/.venv/Scripts/python.exe` (Windows); `python3 scripts/setup.py
--runtime-path` prints it.

---

## Quickstart

```bash
PY=$(python3 scripts/setup.py --runtime-path)

# 1. Get papers in — from Zotero (Better BibTeX used automatically if present)…
$PY -m litdb import-zotero --local
#    …or straight from OpenAlex by DOI / topic, no Zotero needed:
$PY -m litdb import-doi 10.1111/j.1540-6261.1993.tb04702.x
$PY -m litdb external-search "momentum crashes" --import

# 2. Make it semantically searchable
$PY -m litdb embed

# 3. Search (hybrid once embedded)
$PY -m litdb search "distress risk and stock returns" --human

# 4. Capture your thinking, linked to a paper
$PY -m litdb add-note --title "Idea" --body "Momentum vs distress." --link 1

# 5. Triage what to read
$PY -m litdb screen --paper 1 --status to_read --note "read fully" --priority 1
$PY -m litdb list --status to_read --human

# 6. Explore the citation graph
$PY -m litdb cite-fetch --all
$PY -m litdb missing-refs        # papers you cite a lot but don't own
```

---

## Command reference

| Command | Purpose |
|---|---|
| `init` | create the database |
| `import-zotero --file F \| --local \| --bbt` | import papers (Better BibTeX preferred on `--local`) |
| `import-doi DOI [--source]` | add one paper by DOI from OpenAlex/S2 |
| `scan-pdfs DIR [--keep-unresolved] [--embed]` | bulk-import a folder of loose PDFs (resolve DOIs, ingest full text) |
| `external-search "Q" [--source] [--import]` | search OpenAlex/S2 (annotated; optional import) |
| `discover "Q"` | corpus-first: local hits + new external candidates |
| `search "Q" [--mode] [--type] [--status] [--year-min/max]` | keyword or hybrid search |
| `embed [--provider] [--model] [--force]` | build/refresh vectors (swap providers here) |
| `add-note --body … [--title] [--link ID] [--relation] [--confidential]` | add a note |
| `link --note N --paper P [--relation]` | link a note to a paper |
| `screen --paper P --status … [--note] [--priority]` | set reading status / triage |
| `list [--status]` | list papers (reading queue) |
| `paper ID` | show a paper with notes, keywords, citekey |
| `ingest-pdf --paper ID (--file F \| --auto) \| --all` | extract PDF full text into chunks |
| `cite-fetch --paper ID \| --all` | build citation edges from OpenAlex |
| `refs --paper ID` / `cited-by --paper ID` | a paper's references / citers |
| `most-cited` | papers most cited by the rest of your library |
| `missing-refs` | papers your library references most but you don't own |
| `prefs [set KEY VALUE \| get KEY]` | get/set per-user preferences |
| `onboarded [--mark \| --reset]` | first-run onboarding marker |
| `status` | corpus statistics |

Every command prints JSON by default (for the agent to parse); add `--human` for
readable output.

---

## Architecture

- Storage: a single SQLite file in the litdb home, `~/.litdb/litdb.db` (alongside
  the venv, `preferences.json`, and the `.onboarded` marker). Override the home
  with `LITDB_HOME`, or just the DB with `LITDB_DB`.
- Data model: `paper`, `note`, `note_paper` (optional many-to-many links),
  `chunk` (retrieval unit — one abstract chunk plus any full-text chunks),
  `keyword`/`paper_keyword` (with provenance), `embedding` (vectors), `citation`
  (edges). Schema migrations are additive and automatic.
- Retrieval: FTS5 BM25 and brute-force cosine KNN over float32 BLOBs
  (numpy-accelerated when available), fused with RRF. No native extension
  required, so it is portable; a vector engine like sqlite-vec can drop in later.
- Embeddings: hidden behind one provider interface. Vectors are namespaced by
  `model_id`, so multiple models coexist and switching providers is a config edit
  plus a reindex. Confidential notes are always embedded locally.
- Surface: the CLI is primary; `litdb.server` optionally exposes the same
  operations as MCP tools.

---

## Configuration

No configuration is required. To customize, copy `config.example.toml` to your
data directory as `config.toml` (or point `LITDB_CONFIG` at it). Highlights:

```toml
[embedding]
provider = "ollama"          # ollama | fastembed | voyage | openai | hash
model    = "nomic-embed-text"

[policy]
confidential_stay_local = true          # confidential notes never leave the machine
local_provider = "ollama:nomic-embed-text"

[external]
openalex_mailto = ""         # your email joins OpenAlex's faster "polite pool"
s2_api_key_env  = "S2_API_KEY"
```

Switching embedding provider:

```bash
# edit [embedding] in config.toml, then re-embed into the new vector space:
$PY -m litdb embed --provider voyage
```

---

## Skills

The plugin ships two skills:

- `litdb` — the everyday skill. Its SKILL.md is a lean router: it resolves the
  runtime, runs first-run onboarding when needed (`onboarding.md`), loads the
  user's preferences, and routes each request to a task file — `add-folder.md`
  (import PDFs / Zotero), `add-note.md`, or `search.md`. Detailed procedures live
  in those files so the always-loaded instructions stay small.
- `litdb-setup` — one-time dependency bootstrap (check → consent → install).

Per-user state lives in the litdb data directory (not in the repo): a
`.onboarded` marker and `preferences.json`, both managed via `litdb onboarded`
and `litdb prefs` and surfaced through `load_config()`.

---

## Design notes

- Local-first and private by construction; hosted APIs are opt-in and never see
  confidential notes.
- Self-contained: external sources (Zotero, OpenAlex, Semantic Scholar, Better
  BibTeX) are accessed with thin in-house `urllib` clients rather than extra
  services, so a colleague installs one plugin.
- Human-in-the-loop: external results and note↔paper links are proposed, not
  written silently; important imports are the user's call.

## Possible future refinements

Section-aware PDF chunking, a cross-encoder reranker, and Semantic Scholar
citation edges. The schema is built to accommodate them without migration.

## License

MIT.
