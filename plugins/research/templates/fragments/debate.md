
---

## The debate team

A proposer and adversaries, each a different model family, called through
OpenRouter. They are stateless: one call each, charter plus brief in, JSON out.
The brief you write IS their context.

```bash
OPENROUTER_API_KEY=$OPENROUTER_API_KEY python3 -m tools.debate.debate \
    --seats proposer --brief-file <path> --project .

OPENROUTER_API_KEY=$OPENROUTER_API_KEY python3 -m tools.debate.debate \
    --seats adversary,adversary_2 --brief-file <path> --project .   # concurrent
```

Each coauthor needs their own key; calls are billed to whoever runs them. The
roster is `project/global/config.toml`, shared and committed so everyone debates
against the same panel. A seat that errors returns `{"error": ...}` — note it and
carry on; one bad voice never sinks a round.

### Briefs are committed — this one is not optional

Write every brief you send a seat to
`project/<author>/logs/brief-<seat>-<stamp>.md`, never a temp file. Stamp it with
`python3 -m tools.runid --stamp`, since briefs are rewritten each pass of the
loop and would otherwise overwrite each other.

**Then commit them, in the same commit as whatever the round produced.** The
`.gitignore` un-ignores `brief-*.md` for exactly this reason. They are the
written record of which directions were proposed and which were attacked, they
run to tens of kilobytes for an entire project, and they are the thing a
coauthor reaches for when they ask whether the team ever looked at X. A brief
sitting uncommitted on one laptop answers that question for nobody.

Every call — the messages sent and the response, with its model, usage and
latency — is appended to `logs/debate-<run>.jsonl`. That file stays local: it
carries full model responses and gets bulky. If a voice says something that
changes the project's direction, that belongs in `state.md` with the reason, not
left in a log on one machine.
