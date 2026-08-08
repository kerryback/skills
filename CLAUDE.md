# Project Instructions

Plugins for the `kerryback-skills` marketplace. Each lives in
`plugins/<name>/`, with its version in `plugins/<name>/.claude-plugin/plugin.json`.

## Releasing a version bump

Bumping a plugin's version here is only half a release. Academic Studio's Run
Setup page does not read this repo — it reads a separate catalog served from the
`academic_code` repo, and compares each entry's `latestVersion` against what the
user has installed. Until that catalog is updated and pushed, Run Setup shows no
update and nobody upgrades; the new version exists but is invisible.

So whenever you change a `version` in any `plugins/*/.claude-plugin/plugin.json`,
do all of this before considering the release done:

1. Bump `version` in `plugins/<name>/.claude-plugin/plugin.json`.
2. Commit and push this repo. `claude plugin install` writes this version into
   the user's `~/.claude/plugins/installed_plugins.json`, which is the "from"
   side of the comparison.
3. In `~/repos/academic_code`, set `latestVersion` for that plugin to the same
   number in BOTH files — they are meant to be byte-identical:
   - `site/plugins.json` — served at `https://academic-studio.com/plugins.json`,
     which is what a running Academic Studio fetches.
   - `overlay/builtin-extensions/academic-studio-setup/packages.snapshot.json` —
     the offline fallback bundled into the app.
4. Commit and push `academic_code` to `main`. The `pages.yml` workflow re-renders
   the Quarto site and redeploys, so the new catalog goes live on its own.

Do not skip step 3 because "the marketplace is updated" — the marketplace and the
catalog are separate systems, and only the catalog drives Run Setup.

Two version fields sit side by side in the catalog; do not confuse them.
`latestVersion` is the dotted release string that drives update detection, and is
the one to edit. `version` is a small integer used for offering brand-new plugins
once; leave it alone unless you are adding a plugin.

Comparison is a plain numeric dotted compare, no semver prerelease handling, and
an entry whose `latestVersion` is present but does not match `/^\d[0-9.]*$/` is
silently dropped from the catalog.

Leaving the field out entirely is a different thing and is fine. The validator
only objects to a malformed value, so an entry with no `latestVersion` is kept
and shows as v1. That is the intended state for standalone-skill entries that
pin a git tag rather than a release — the `econ-*` skills, for instance — and
`scripts/sync-plugin-versions.mjs` in `academic_code` deliberately leaves them
alone. Do not "fix" them by adding a version.

## Marketplace manifest

`.claude-plugin/marketplace.json` lists the plugins. A `version` field there is
optional and is not what Run Setup reads — keep it out unless there is a reason,
so there is one less copy of the number to drift.
