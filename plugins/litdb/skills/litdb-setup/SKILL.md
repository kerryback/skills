---
name: litdb-setup
description: One-time bootstrap for the litdb literature knowledge base. Use when the user installs litdb, asks to "set up litdb", hits a "litdb not installed / no runtime" error, or wants to check/repair litdb's dependencies. Creates a fixed per-user runtime at ~/.litdb/.venv and installs the litdb package into it, after showing a plan and getting consent. Never installs system software silently.
---

# litdb setup

Prepare or repair the litdb runtime. litdb installs into a fixed per-user home,
`~/.litdb` (venv at `~/.litdb/.venv`), so it never depends on a project or repo
folder. Orchestrate the bundled script; do not improvise install commands.

Find the setup script (call it SETUP), the litdb plugin's `scripts/setup.py`:
- If the `CLAUDE_PLUGIN_ROOT` environment variable is set, SETUP is
  `$CLAUDE_PLUGIN_ROOT/scripts/setup.py`.
- Otherwise this file is at `<plugin>/skills/litdb-setup/SKILL.md`, so SETUP is
  `scripts/setup.py` two directories up from this file's real (symlink-resolved)
  path.
Run it with `python3`.

## Steps

1. Check status:
   ```
   python3 SETUP --check
   ```
   Report the result. If `READY` is yes and the skill is installed, stop.

2. If not ready, show the plan (this changes nothing):
   ```
   python3 SETUP
   ```
   It will create `~/.litdb/.venv`, install the litdb package (from GitHub, or a
   local checkout if you are running from one), verify FTS5, and initialize the
   database.
   - If Python < 3.10: offer to install a newer Python for them (with consent —
     macOS: `brew install python`; Windows: `winget install Python.Python.3.12`;
     or via `uv python install`). If they decline, give the command and stop.
   - `uv` is optional (setup falls back to venv+pip). If it's missing and they'd
     like faster installs, offer to install it (`curl -LsSf
     https://astral.sh/uv/install.sh | sh`, or `brew install uv`) — ask first.

3. After the user agrees, execute:
   ```
   python3 SETUP --yes
   ```

4. Confirm with `python3 SETUP --check`, then report the runtime path
   (`python3 SETUP --runtime-path`) — the fixed `~/.litdb/.venv` Python the
   `litdb` skill uses.

## Notes

- The package installs non-editable, so any source checkout used to run setup is
  disposable afterward — the runtime lives entirely in `~/.litdb`.
- Ollama is only needed for local embeddings (from the semantic-search step); its
  absence is not a setup error.
- To repair a broken runtime, re-run `--yes`; it is idempotent.
