# litdb

litdb is a private, searchable library of your research papers that you use by
talking to Claude in plain English. Point it at your PDFs and it reads them —
the whole paper, not just the title and abstract — so you can later ask things
like "what do I have on momentum crashes?" and get the right papers, even the
one that said "large drawdowns" instead of your words. It also helps you find new
work, keeps track of what you cite, and produces the bibliography file you cite
from. Everything stays on your own computer.

It runs as a Claude Code plugin. You don't learn commands or open a terminal —
you just ask.

---

## What you can do

Once your papers are in, you can say things like:

- "Add all the PDFs in my Papers folder." — it reads each one, looks up the
  correct title, authors, journal, and year, and makes it searchable.
- "What do I have on momentum crashes?" — searches your library by meaning and by
  wording, and tells you which paper and page a passage came from.
- "Find recent papers on factor momentum that I don't already have." — searches
  the wider literature (OpenAlex and Semantic Scholar) and marks what's new to you.
- "What am I citing a lot but haven't saved?" — looks at what your papers
  reference and flags important works missing from your library.
- "Make a .bib file of my whole library." — generates the bibliography you cite
  from in LaTeX.
- "I just downloaded a paper — add it." — or drop it in a folder litdb watches and
  it gets added on its own.
- "Add a note on the Daniel–Moskowitz paper: their crash result is about the short
  leg." — keeps your thought attached to the paper and searchable.

You ask; Claude does the work. Under the hood each of these is a real command
(documented far below) that you can also run yourself if you ever want to — but
you don't have to.

---

## Getting started

1. Install the plugin (one time):

   ```
   claude plugin marketplace add kerryback/skills
   claude plugin install litdb@kerryback-skills
   ```

2. Start using it. The first time, Claude asks you a couple of quick setup
   questions — see the next section — and sets everything up for you. Then just
   tell it to add your papers and start asking.

There's nothing else to configure. litdb keeps everything in one file on your
computer (`~/.litdb`), so it doesn't depend on any particular project or folder.

For better search, it will offer to set up a small free tool (Ollama) so it can
search by meaning, not only by exact words — it walks you through that during
setup. If you skip it, search still works by wording.

---

## Do you use Zotero?

That's the one choice that shapes how litdb fits your workflow, and Claude asks it
during setup.

- If you don't use Zotero (or don't want to): litdb handles everything itself.
  You add PDFs, it organizes and searches them, and it produces your `.bib` file.
  Nothing else needed. If you ever start using Zotero later, litdb can move your
  whole library into it in one step.
- If you do use Zotero: litdb works alongside it and treats Zotero as the master
  copy of your references. It imports your Zotero library, keeps itself up to date
  as you save papers there, and (if you use Better BibTeX) uses your existing
  citation keys. When you add a paper through litdb instead, it puts a copy into
  Zotero for you.

Either way, you can drop new PDFs into a designated folder and litdb adds them
automatically the next time you use it.

---

## What makes it useful

- It reads the whole paper. Search covers the full text, not just abstracts, so
  it can find a point buried in a paper's results section — and it tells you the
  page.
- It searches by meaning and by wording. Ask in your own words; it also finds
  papers that make the same point with different terms.
- It searches your library first. When you look for new work, it checks what you
  already own before reaching out to OpenAlex or Semantic Scholar, and labels what
  you already have.
- It understands citations. It can show what a paper cites, who cites it, and
  which works you lean on most but haven't saved.
- It's private. Everything lives on your machine; nothing is sent to an outside
  service unless you ask it to look something up, and notes you mark confidential
  never leave your computer.
- It writes your bibliography. One request produces a `.bib` file for LaTeX, for
  your whole library or just the papers you choose.

---

## Common questions

- Where do my papers live? In one database file on your computer,
  `~/.litdb/litdb.db`. It's yours; nothing is uploaded.
- Do I need Zotero? No. It's optional — see above.
- Do I need to run commands? No. You talk to Claude. The commands exist for people
  who want to script things.
- What if I download a paper behind a paywall? Getting the PDF still happens in
  your browser (through your library's login) — no tool can bypass that. But once
  the file is on your computer, litdb takes it from there automatically.
- Can it find papers I don't have? Yes — it searches OpenAlex (free) and, if you
  add a free key, Semantic Scholar, and can pull chosen papers in.

---

## For power users: running commands directly

You never need this section, but every action Claude takes is a plain command you
can run yourself or put in a script. The interpreter lives at
`~/.litdb/.venv/bin/python`; `python3 skills/litdb/setup.py --runtime-path` prints its
path. Commands print machine-readable JSON by default; add `--human` for readable
output.

```bash
PY=$(python3 skills/litdb/setup.py --runtime-path)

$PY -m litdb scan-pdfs ~/Papers --keep-unresolved --embed   # add a folder of PDFs
$PY -m litdb search "momentum crashes" --human              # search your library
$PY -m litdb discover "factor momentum" --human             # your library + new work
$PY -m litdb missing-refs --human                           # cited but not owned
$PY -m litdb export-bib --out refs.bib                      # write your bibliography
```

Getting papers in

| Command | Purpose |
|---|---|
| `scan-pdfs DIR [--keep-unresolved] [--embed]` | add a folder of PDFs (look up metadata, read full text) |
| `sync-inbox` | add new PDFs from your inbox folder (skips ones already added) |
| `import-doi DOI [--source]` | add one paper by DOI |
| `import-zotero --file F \| --local \| --bbt` | import from Zotero |
| `ingest-pdf --paper ID (--file F \| --auto) \| --all` | read a PDF's full text into an existing paper |

Searching and reading

| Command | Purpose |
|---|---|
| `search "Q" [--mode] [--type] [--status] [--year-min/max]` | search full text + abstracts by wording, meaning, or both |
| `screen --paper P --status … [--note] [--priority]` | mark reading status / triage |
| `list [--status]` | list papers (your reading queue) |
| `paper ID` | show a paper with its notes, keywords, and citekey |

Finding new work (searches your library first)

| Command | Purpose |
|---|---|
| `external-search "Q" [--source] [--import]` | search OpenAlex / Semantic Scholar (marks what you own; optional import) |
| `discover "Q"` | your library's hits plus new outside candidates in one view |

Citations

| Command | Purpose |
|---|---|
| `cite-fetch --paper ID \| --all` | fetch a paper's references and citers |
| `refs --paper ID` / `cited-by --paper ID` | what a paper cites / who cites it |
| `most-cited` | works your library cites most |
| `missing-refs` | works you cite a lot but don't own |

Fixing up records

| Command | Purpose |
|---|---|
| `update ID [--doi] [--citation-key] [--title] [--authors] [--year] [--venue] …` | correct a paper's details in place (keeps its full text) |
| `merge --keep K --dupe D` | combine two records for the same paper into one |
| `delete ID` | remove a paper and everything attached to it |

Citing and Zotero

| Command | Purpose |
|---|---|
| `export-bib [--out FILE] [--status S] [--ids …]` | write a `.bib` bibliography for the library or a subset |
| `sync-zotero` | pull new papers from Zotero (import + read PDFs + index) |
| `push-zotero [--ids …] [--dry-run] [--force]` | add papers to Zotero (skips ones already sent) |
| `migrate-to-zotero [--dry-run]` | move your whole library into Zotero and switch to Zotero mode |

Notes, indexing, and admin

| Command | Purpose |
|---|---|
| `add-note --body … [--title] [--link ID] [--confidential]` | attach a note (basic, by design — see below) |
| `link --note N --paper P [--relation]` | link an existing note to a paper |
| `embed [--provider] [--model] [--force]` | build/refresh the "search by meaning" index |
| `prefs [set KEY VALUE \| get KEY]` | view/change settings (see Settings) |
| `s2-key [status \| set KEY \| clear]` | store your Semantic Scholar key |
| `status` | library statistics |
| `init` / `onboarded [--mark \| --reset]` | create the database / manage first-run setup |

### Settings

Changed with `litdb prefs set KEY VALUE`, stored in `~/.litdb/preferences.json`:

| Setting | Meaning |
|---|---|
| `source_of_truth` | `litdb` (default) or `zotero` — who's in charge of your references |
| `inbox` | a folder whose new PDFs are added automatically each session |
| `uses_tex` | you write in LaTeX (litdb surfaces citation keys) |
| `use_better_bibtex` | use Better BibTeX citation keys when importing from Zotero |

---

## For developers: how it works

- Storage. One SQLite file, `~/.litdb/litdb.db`, in a fixed per-user home (with the
  venv, `preferences.json`, and the `.onboarded` marker). `LITDB_HOME` / `LITDB_DB`
  override the locations.
- Data model. `paper`, `note`, `note_paper`, `chunk` (the retrieval unit — one
  abstract chunk plus any full-text chunks), `keyword` / `paper_keyword` (with
  provenance), `embedding` (vectors, namespaced by model), `citation` (edges), and
  `ingested_file` (a content-hash ledger that makes inbox scans idempotent). Schema
  migrations are additive and automatic.
- Search. FTS5 BM25 (keyword) and brute-force cosine similarity over float32
  vectors (numpy-accelerated when present), fused with Reciprocal Rank Fusion and
  deduplicated to one hit per paper. No native extension required, so it stays
  portable; a vector engine like sqlite-vec can drop in later.
- Embeddings. One provider interface; vectors are namespaced by `model_id` so
  several models coexist and switching is a config edit plus a reindex. Local by
  default (Ollama `nomic-embed-text`); Voyage / OpenAI / fastembed optional; a
  zero-dependency `hash` provider works before setup. Confidential notes are always
  embedded locally.
- Two modes. `source_of_truth` selects whether litdb or Zotero is authoritative. In
  litdb mode nothing touches Zotero. In Zotero mode litdb is a derived index kept
  current with `sync-zotero` / `push-zotero`; the Zotero integration uses the local
  connector only and never leaves the machine.
- Notes are intentionally minimal. `note` / `note_paper` and `add-note` / `link`
  let you attach and search a thought — they are not a note-taking app. A proper
  integration that complements existing tools (Obsidian, Markdown, Zotero
  annotations) rather than reinventing them is deferred by design; the substrate is
  kept, not built out or stripped.
- Surface. The CLI is primary and drives everything; `litdb.server` optionally
  exposes the same operations as MCP tools.

### Install from source

```bash
git clone https://github.com/kerryback/skills && cd skills/plugins/litdb
python3 skills/litdb/setup.py --check     # report what's present/missing
python3 skills/litdb/setup.py             # dry-run plan (changes nothing)
python3 skills/litdb/setup.py --yes       # build the runtime into ~/.litdb
```

`setup.py` only builds the runtime (venv + package; `--editable` for dev) and
never installs system software for you. Requires Python 3.10+.

### Configuration file

Behavioral choices live in Settings (above). `config.toml` is only for lower-level
defaults — copy `config.example.toml` into the data directory, or point
`LITDB_CONFIG` at it:

```toml
[embedding]
provider = "ollama"          # ollama | fastembed | voyage | openai | hash
model    = "nomic-embed-text"

[policy]
confidential_stay_local = true
local_provider = "ollama:nomic-embed-text"

[external]
openalex_mailto = ""         # your email joins OpenAlex's faster "polite pool"
s2_api_key_env  = "S2_API_KEY"

[zotero]
connector = "http://localhost:23119"
```

### Skills

One self-contained skill ships in the plugin: `litdb`. Its SKILL.md is a lean
router — it resolves the runtime, runs first-run onboarding, loads preferences,
does the session-start catch-up sync, and routes each request to a task file that
lives beside it: `setup.md` (one-time runtime bootstrap via the bundled
`setup.py`: check → consent → install), `onboarding.md`, `add-folder.md`,
`add-note.md`, or `search.md`. Keeping everything in one skill directory means a
single-skill install (e.g. `npx skills add`) is fully self-contained.

### Design principles

Local-first and private by construction; self-contained (Zotero, OpenAlex,
Semantic Scholar, and Better BibTeX are reached with small in-house `urllib`
clients, so a colleague installs just one plugin); programmatic (every step is a
scriptable command with JSON output); and human-in-the-loop (external results and
links are proposed, not written silently).

Possible future refinements: section-aware PDF chunking, a cross-encoder
reranker, a Zotero Web API transport for headless sync, and a real notes
integration. The schema accommodates them without migration.

## License

MIT.
