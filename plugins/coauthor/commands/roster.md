---
description: Pick the debate roster (number of adversaries + a model per seat) in a browser, from the live OpenRouter catalog. Writes config.toml and remembers your choice.
argument-hint: ""
---

You are the Coordinator. Let the human choose this project's debate lineup with
the roster picker, then confirm what got written. Do NOT invent model slugs —
the picker fetches the live OpenRouter catalog.

## Steps

1. Confirm coauthor is active here (a `.coauthor/` folder exists). If not, tell the
   user to run `/coauthor:init` first. (The picker will create
   `.coauthor/config.toml` if it is missing.)

2. Launch the picker. It opens a browser window on the user's machine, shows the
   live model list, and BLOCKS until they click Submit (or the timeout):

   ```
   PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python3 -m coauthor.roster_app \
     --config "$(pwd)/.coauthor/config.toml" --out "$(pwd)/.coauthor/logs/roster_echo.json" --timeout 900
   ```

   Tell the user plainly: "A browser window is opening — pick your proposer,
   how many adversaries, and a model for each (keep the families different),
   then click Submit. Or click 'Use most recent' to reuse last time's lineup."
   The picker needs no API key (the catalog endpoint is public); only the debate
   calls later need `OPENROUTER_API_KEY`.

3. When the command returns, it has written `.coauthor/config.toml` (the roster the
   debate client reads) and updated the global "last roster"
   (`~/.coauthor/last_roster.json`, so a brand-new directory can "Use most
   recent"). Read `.coauthor/config.toml` and confirm the lineup back to the user:
   each seat, its model, and its family — and flag it if any two seats share a
   family (that reduces the cross-family diversity the design depends on).

## Notes
- The picker is dependency-free (stdlib http.server); nothing to install.
- If the user never submits, the command exits after the timeout and the roster
  is left unchanged — say so rather than guessing a lineup.
- Extra adversary seats (`adversary_2`, …) automatically reuse the `adversary`
  charter; you don't need a separate charter file per voice.
