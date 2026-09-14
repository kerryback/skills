# Skills

A [Claude Code](https://claude.com/claude-code) plugin marketplace of research
data skills — reusable building blocks for literature management and for pulling
financial, economic, and asset-pricing data.

This repo is a plugin marketplace: each skill is packaged as a plugin under
`plugins/<name>/`. It installs either with Claude Code's built-in plugin commands
or with the `npx skills` CLI — both read the same manifest.

## Install

### Claude Code plugins (built-in)

```
/plugin marketplace add kerryback/skills
/plugin install finance-data@kerryback
```

Non-interactively:

```
claude plugin marketplace add kerryback/skills
claude plugin install finance-data@kerryback
```

Swap `finance-data` for `litdb` or `wrds`.

### npx skills CLI

```
npx skills@latest add kerryback/skills
```

Pick skills from the interactive menu (or `--list` to preview). They install to
`~/.claude/skills/<name>/` (global) or `<project>/.claude/skills/<name>/` (add
`--project`). No login needed — this is a public repo.

Installing copies the skill files only. External tools and API keys are each
skill's own prerequisites — see the skill's README (the wrds skill, for
example, needs WRDS credentials, and finance-data needs a FRED or FinnHub key
for some sources).

## Available skills

| Skill | What it does |
|-------|--------------|
| [`finance-data`](./plugins/finance-data/skills/finance-data) | Fetch free market/economic data (prices, fundamentals, FRED, factors) and save as CSV. |
| [`litdb`](./plugins/litdb/skills/litdb) | Personal literature and notes knowledge base: hybrid keyword + semantic search over your own papers, Zotero/Better BibTeX import, loose-PDF ingestion with full text, OpenAlex/Semantic Scholar discovery, citation graph. |
| [`wrds`](./plugins/wrds/skills/wrds) | Build empirical asset-pricing samples from WRDS (CRSP v2/Compustat) and Open Source Asset Pricing. Connection that skips the 2FA prompt, vetted query building blocks, and the competing Ken French / Drechsler / OpenAP conventions written out rather than picked silently. |

## Layout

```
.claude-plugin/marketplace.json      the marketplace manifest (lists the plugins)
plugins/<name>/
  .claude-plugin/plugin.json         the plugin manifest
  skills/<name>/                     the skill: SKILL.md + its scripts/references/assets
```

## Contributing a skill

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json` (`name`,
   `description`, `version`).
2. Put the skill at `plugins/<name>/skills/<name>/SKILL.md`, with YAML
   frontmatter (`name`, `description`) plus any `scripts/`, `references/`, or
   `assets/` it needs. Use relative paths inside the skill so it works wherever
   it installs.
3. Add the plugin to `.claude-plugin/marketplace.json` and a row to the table
   above.
4. Open a PR.

Keep the `description` sharp — it's the part always in context, and it's what
decides whether the skill triggers.
