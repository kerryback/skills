
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

Write every brief you send a seat to `project/<author>/logs/` rather than a temp
file. They are the actual prompts the debate answered, and they are the one part
of a round nothing else records.
