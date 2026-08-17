# Skills

A [Claude Code](https://claude.com/claude-code) plugin marketplace of
authoring/teaching skills — reusable building blocks for course materials, data
workflows, deck production, and reviewing work.

This repo is a plugin marketplace: each skill is packaged as a plugin under
`plugins/<name>/`. It installs either with Claude Code's built-in plugin commands
or with the `npx skills` CLI — both read the same manifest.

## Install

### Claude Code plugins (built-in)

```
/plugin marketplace add kerryback/skills
/plugin install voiceover@kerryback
```

Non-interactively:

```
claude plugin marketplace add kerryback/skills
claude plugin install voiceover@kerryback
```

Swap `voiceover` for `slides`, `finance-data`, or `critique`.

### npx skills CLI

```
npx skills@latest add kerryback/skills
```

Pick skills from the interactive menu (or `--list` to preview). They install to
`~/.claude/skills/<name>/` (global) or `<project>/.claude/skills/<name>/` (add
`--project`). No login needed — this is a public repo.

Installing copies the skill files only. External tools and API keys are each
skill's own prerequisites — see the skill's README (the voiceover skill, for
example, checks for `quarto` and `ELEVENLABS_API_KEY` and offers to set them up).

## Available skills

| Skill | What it does |
|-------|--------------|
| [`voiceover`](./plugins/voiceover/skills/voiceover) | PDF slide deck → narrated MP4 + transcript. Claude Code writes the narration; ElevenLabs voices it. Needs `quarto` + `ELEVENLABS_API_KEY`. |
| [`cardstock`](./plugins/cardstock/skills/cardstock) | Build a slide deck in the Quarto reveal.js house style — cards, dividers, comparison tables; export to PDF, PPTX, or PNG. |
| [`finance-data`](./plugins/finance-data/skills/finance-data) | Fetch free market/economic data (prices, fundamentals, FRED, factors) and save as CSV. |
| [`critique`](./plugins/critique/skills/critique) | Spawn parallel reviewer agents to critique work from different angles, then synthesize and apply revisions. Heavyweight — fans out subagents. |
| [`research`](./plugins/research/skills/research) | Structure a research repo several people and their Claudes can share: per-author folders, portable paths, one canonical dataset, provenance, a git-enforced round lock, and a generated CLAUDE.md. Ships a writing guide that learns — hooks capture the prose corrections you give, `/style-learn` turns them into rules you accept, written into the guide itself. Optional two-build protocol, OpenRouter debate panel, Overleaf mirror. |
| [`screenshare`](./plugins/screenshare/skills/screenshare) | Let students put their own screen on the classroom projector. A local WebRTC relay published over a Cloudflare Quick Tunnel; students join from an https link and the instructor picks who is shown. Falls back to a TURN relay when campus segmentation blocks the direct path. Needs `cloudflared`. |
| [`survey`](./plugins/survey/skills/survey) | Live in-class polls on the projector — multiple choice, word clouds, scales, numeric estimates, rankings. Claude writes the questions; students answer anonymously from their own devices at a fixed public address. A menu jumps to any prepared question at any time. Needs only an API token. |
| [`poll`](./plugins/poll/skills/poll) | The tunnelled predecessor of `survey`: same polls, but the app runs on the classroom machine and is published over a Cloudflare Quick Tunnel. Prefer `survey` unless you need it to work with no hosted app. Needs `cloudflared`. |
| [`human-write`](./plugins/human-write/skills/human-write) | Write and edit academic prose that reads as human, not machine-generated: varied rhythm, no formulaic AI tells, structure driven by the argument. Defaults to scholarly register (papers, referee reports, proposals); applies to fresh drafting and revision. |
| [`litdb`](./plugins/litdb/skills/litdb) | Personal literature and notes knowledge base: hybrid keyword + semantic search over your own papers, Zotero/Better BibTeX import, loose-PDF ingestion with full text, OpenAlex/Semantic Scholar discovery, citation graph. |
| [`wrds`](./plugins/wrds/skills/wrds) | Build empirical asset-pricing samples from WRDS (CRSP v2/Compustat) and Open Source Asset Pricing. Connection that skips the 2FA prompt, vetted query building blocks, and the competing Ken French / Drechsler / OpenAP conventions written out rather than picked silently. |
| [`participation`](./plugins/participation/skills/participation) | Score class participation against a roster — 1–3 for amount and quality, optional note, one row per student per meeting to `participation.csv`. |
| [`smithers`](./plugins/smithers/skills/smithers) | A personal email and calendar desk: reads Gmail and Calendar through a local connector, writes a briefing of the week ahead, and parks drafted replies for you to review and send. Never sends mail or deletes events itself. |
| [`elegant-pdf`](./plugins/elegant-pdf/skills/elegant-pdf) | Branded documents from a small HTML design system rendered with headless Chrome — one-page flyers (JPEG or clickable PDF) and multi-page programs and reports with cover, running footer, and page numbers. |

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
