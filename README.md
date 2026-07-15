# Rice Business Skills

A shared collection of [Claude Code](https://claude.com/claude-code) skills for
Rice Business faculty — reusable building blocks for course materials, data
workflows, deck production, and teaching agents.

Each folder in this repo is one skill: a `SKILL.md` file (instructions Claude
follows) plus any supporting scripts, references, or assets it needs.

## Prerequisites

This is a **private** repo in the Rice GitHub organization. Before installing,
make sure you're authenticated to GitHub so the installer can clone it:

```
gh auth login          # or have SSH keys / a git credential helper configured
```

If `npx skills add` fails with a permission or authentication error, this is
almost always the cause.

## Install

From any project (or your home directory for a global install), run:

```
npx skills@latest add rice-business/skills
```

You'll get an interactive menu. Use the arrow keys to move, `space` to select
the skills you want, and `enter` to confirm. Selected skills are copied into:

- `~/.claude/skills/<name>/` — available in **every** project, or
- `<project>/.claude/skills/<name>/` — scoped to one project (run the command
  from inside that project)

Start a new Claude Code session and the skills appear automatically.

> Note: `rice-business/skills` is a placeholder — replace it with the actual
> `org/repo` once this is pushed to GitHub.

## Using a skill

- **Automatically** — just describe your task. Claude loads any installed skill
  whose description matches what you're doing.
- **Explicitly** — type `/<skill-name>` (e.g. `/create_deck`) to invoke it on
  demand.

## Available skills

| Skill | What it does |
|-------|--------------|
| [`create_deck`](./create_deck) | Build a PowerPoint bar-chart deck of Northwind revenue by country. |
| [`finance-data`](./finance-data) | Fetch free market/economic data (prices, fundamentals, FRED, factors) and save as CSV. |

## Contributing a skill

1. Create a folder named after your skill (kebab- or snake-case).
2. Add a `SKILL.md` with YAML frontmatter:

   ```
   ---
   name: my-skill
   description: >-
     One or two sentences. Lead with what it does, then the trigger phrases
     ("Use this whenever the user wants to ..."). This text is what Claude
     matches against, so make it specific.
   ---

   Instructions for Claude go here. Reference supporting files with relative
   links like [helper.py](./scripts/helper.py) — they load on demand, not up
   front, so keep the frontmatter lean and push detail into linked files.
   ```

3. Put any scripts/data/assets in subfolders (`scripts/`, `references/`,
   `assets/`) and link to them from `SKILL.md`.
4. Add a row to the table above.
5. Open a PR.

### Tips

- Keep the `description` sharp — it's the only part always in context, and it's
  what decides whether the skill triggers.
- Use **relative paths** everywhere inside the skill so it works regardless of
  where it's installed.
- Test locally by copying your folder into `~/.claude/skills/` and starting a
  fresh session before you push.
