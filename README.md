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
/plugin install voiceover@kerryback-skills
```

Non-interactively:

```
claude plugin marketplace add kerryback/skills
claude plugin install voiceover@kerryback-skills
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
| [`slides`](./plugins/slides/skills/slides) | Build a polished Quarto reveal.js deck — HTML slides you render and export to PDF, PPTX, or PNG. |
| [`finance-data`](./plugins/finance-data/skills/finance-data) | Fetch free market/economic data (prices, fundamentals, FRED, factors) and save as CSV. |
| [`critique`](./plugins/critique/skills/critique) | Spawn parallel reviewer agents to critique work from different angles, then synthesize and apply revisions. Heavyweight — fans out subagents. |

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
