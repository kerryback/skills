# coauthor

A reusable, coordinated multi-agent system for producing empirical research
papers. Claude Code is the coordinator you talk to; everything else is a role it
orchestrates.

## The roles

| Role | Kind | Runs on | Job |
|---|---|---|---|
| Coordinator | you + Claude Code | Anthropic (direct) | Converse, adjudicate, hold the human gate, own canonical state |
| Proposer | debate voice | OpenRouter | Generate and advance ideas (creative lead) |
| Adversary | debate voice | OpenRouter (different family) | Attack ideas, severity-ranked, name resolving evidence |
| Verifier | Claude subagent | Anthropic | Corpus-first fact-checking over litdb; import papers as you go |
| Analyst | Claude subagent | Anthropic | Independently build the sample, run the empirics against the frozen method spec |
| Replicator | Claude subagent | Anthropic (or external) | Independently build the sample and implement the same frozen spec in its own code (both should converge); hunt the standard biases |

Design rationale lives in the code comments and `skills/coauthor/SKILL.md`. Key
principles: corpus-first (search litdb before any external source); evidence, not
rhetoric (disputes escalate as checkable questions); the human is editor-in-chief;
diversity where it pays (debate voices) and reliability where it's mandatory
(tool-using coders).

## Self-contained: no "coauthor project", no repos

coauthor is a skill any directory can use. It is *active* in a directory when a
`.coauthor/` folder exists there (created by `/coauthor:init`). It creates no repo,
runs no `git`, and writes no `CLAUDE.md`/`README.md`/root files. Everything it owns
lives in `.coauthor/`; the only thing at the repo root is `workspace/` (the
analyst's code/data/results).

## Memory — three tiers

- Project truth (committed): `.coauthor/state.md` (thesis, open questions, settled
  facts, killed ideas) + litdb notes. The durable, human-gated record.
- Working memory (committed, curated, rewritten often): `.coauthor/session.md`
  (orchestrator state = the cross-session handoff), `.coauthor/analyst.md`,
  `.coauthor/replicator.md` (each subagent's curated state, re-read on every fresh
  spawn). This is how ephemeral subagents resume without context rot.
- Exhaustive: `.coauthor/logs/log-<user>-<date>-<time>.jsonl` — every debate
  call and subagent tool call, appended as it happens. The full record, written
  automatically; large, and gitignored. Named by run rather than by round number,
  so a shared repo holds several coauthors' logs side by side with nothing
  overwriting anything.

  Nothing under `logs/` is committed — it outgrows what GitHub will take.
  `state.md` + litdb notes are the shared record. There is no transcript format:
  the JSONL is line-delimited, so ask Claude for the slice you want and it filters
  the file.

## Requirements

- litdb — REQUIRED. The Verifier is corpus-first over your litdb library, and
  corpus-first is a core principle: every "known result" is checked against litdb
  before any external source. Install the litdb plugin/skill first (the Verifier
  drives `~/.litdb/.venv/bin/python -m litdb …`). Without it, verification — half
  of every round — does not work.
- Data sources — required only for empirical rounds, and supplied by whatever data
  plugin/skill the project uses (connection details, credentials, and field-level
  standards live there, not in coauthor). Debate-and-verify-only rounds don't need
  any of that.
- Two API keys — see below.

## Credentials (two secrets)

- `ANTHROPIC_API_KEY` — Coordinator, Verifier, Analyst, Replicator (all Claude).
- `OPENROUTER_API_KEY` — the debate voices (Proposer, Adversary, extra voices).

Set an OpenRouter data policy that excludes training/logging, and pin provider
routes for open models so debater behavior is reproducible.

## Usage

1. `/coauthor:init` — activate coauthor in the current directory (creates
   `.coauthor/` + `workspace/`, nothing else).
2. `/coauthor:roster` — pick the debate lineup in a browser from the live
   OpenRouter catalog (writes `.coauthor/config.toml`). Adversaries run
   concurrently.
3. Converse with Claude Code to set the working angle; it seeds
   `.coauthor/state.md` and runs a litdb discovery pass.
4. `/coauthor:round` — one debate → verify → (if it turns on a number, freeze the
   method spec → optional empirics, same spec to Analyst and Replicator) →
   synthesize → human-gate cycle. Repeat as the direction evolves.

## Layout

```
agents/       Claude subagents (Verifier, Analyst, Replicator) — charters as system prompts
charters/     OpenRouter debate-voice charters (Proposer, Adversary) — versioned prompts
commands/     /coauthor:init, /coauthor:roster, /coauthor:round, /coauthor:autonomy, /coauthor:refresh, /coauthor:stop
skills/       coordinator orchestration guidance
src/coauthor/ debate client (OpenRouter, concurrent), roster picker, logger, run stamps, config
hooks/        tool-call logging hook (silent unless .coauthor/ exists)
project-template/  what /coauthor:init copies in: .coauthor/ + workspace/
config.example.toml  the starter model roster for the debate voices
```
