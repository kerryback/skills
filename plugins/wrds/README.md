# wrds

A data plugin for building empirical asset-pricing samples from WRDS
(CRSP/Compustat) and Open Source Asset Pricing (Chen-Zimmermann).

It is the domain layer that orchestration plugins (e.g. `coauthor`) stay free of:
coauthor is domain-agnostic and delegates all data-source specifics here. Use this
skill whenever a task pulls or constructs market/accounting data from WRDS.

## What it covers (`skills/wrds/SKILL.md`)

- Connecting to WRDS non-interactively — resolve the username at runtime
  (`$WRDS_USER` → `~/.wrds` → `~/.pgpass` field 4), password from `~/.pgpass`, so
  unattended builds don't hang. Resolver at `skills/wrds/wrds_username.py`.
- Installing the `wrds` package without letting it downgrade pandas.
- CRSP v2 table conventions (`crsp.msf_v2`) and common-stock screens.
- Computing market cap correctly across share classes — aggregate `mthcap` by
  `permco` so dual-class firms carry their whole equity value (a construction bug
  that a shared panel hides from estimator-convergence checks).
- The CRSP-Compustat link (`ccmxpf_lnkhist`).
- Field standards that get papers rejected: look-ahead, delisting, survivorship,
  microcaps (value- vs equal-weighted), overlapping-return standard errors,
  multiple testing.
- OpenAP object conventions (char panel vs `PredictorPortsFull`, signed-vs-raw) and
  a red-team checklist.

## Requirements

- WRDS access: the `wrds` Python package, `~/.pgpass` with a wrds line, and a
  resolvable WRDS username.
- OpenAP data is public (download directly).
