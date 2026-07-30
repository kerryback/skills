---
name: wrds
description: Build empirical asset-pricing samples from WRDS (CRSP/Compustat) and Open Source Asset Pricing. Use whenever a task pulls or constructs market/accounting data from WRDS — connecting non-interactively, installing the wrds package without breaking pandas, CRSP v2 table conventions, computing market cap correctly across share classes (permco), the CRSP-Compustat link, and the field-level standards (delisting, survivorship, microcaps, overlapping-return standard errors) and pitfalls (OpenAP signed-vs-raw, char-panel vs. portfolio-returns) that get asset-pricing papers rejected.
---

# wrds — building asset-pricing data from WRDS and OpenAP

This skill is the domain guidance for pulling and constructing empirical
asset-pricing data. It pairs with any orchestration that asks for a sample (e.g.
the coauthor plugin, whose Analyst and Replicator each build the sample
independently and reconcile it before analysis). Keep every pull re-runnable and
standalone, and state exactly which sources, objects, and vintages you used.

## Connecting to WRDS non-interactively (or an unattended run HANGS)
`~/.pgpass` supplies the PASSWORD (robust — no secret in code), but the wrds library
does NOT read the username from it, so you MUST pass the username or the connection
prompts and an unattended run hangs forever. NEVER hardcode a username (code must
work for anyone) — resolve it per user, first hit wins: `$WRDS_USER` → `~/.wrds`
(a `WRDS_USER=<id>` or bare-username line) → `~/.pgpass` field 4 of the wrds line
(zero setup — anyone with WRDS already has it). This skill ships the resolver at
`wrds_username.py`; copy the small function INLINE into your build script so it
stays standalone:
```python
import wrds
# (paste the wrds_username() resolver from wrds_username.py here)
conn = wrds.Connection(wrds_username=wrds_username())   # password from ~/.pgpass
```

## Installing wrds — do NOT let it downgrade pandas
The `wrds` package pins an OLD pandas in its metadata; installed normally it
uninstalls your current pandas and drops to that old version, which breaks numpy /
statsmodels / much else. wrds runs fine on current pandas, so never accept the
downgrade. Pick one approach:
- Clean install (preferred): install wrds alone, touching nothing else —
  `<interp> -m pip install --no-deps wrds` — then, only if `import wrds` reports a
  genuinely missing module (e.g. `psycopg2`, `sqlalchemy`, `mock`), install just
  that one package. NEVER reinstall/downgrade pandas.
- Snapshot + restore: `<interp> -m pip freeze > /tmp/env-before.txt` BEFORE
  installing wrds; `pip install wrds`; then restore the downgraded packages
  (`<interp> -m pip install -r /tmp/env-before.txt`). Ignore pip's "wrds requires
  pandas==X" conflict warnings — harmless here.
Verify: `<interp> -c "import wrds, pandas; print(pandas.__version__)"` — pandas
should be your CURRENT version and wrds should import.

## CRSP: prefer the v2 tables
Prefer the CRSP v2 monthly file `crsp.msf_v2` (`permno, permco, mthcaldt, yyyymm,
mthcap, mthret, mthprc, shrout, sharetype, securitytype, securitysubtype,
issuertype, primaryexch`) — there `mthret` is a proper float; the older `crsp.msf`
returns returns as strings. Common-stock screens in v2: `sharetype='NS'`,
`securitytype='EQTY'`, `securitysubtype='COM'`, `issuertype in ('CORP','ACOR')`,
`primaryexch in ('N','A','Q')`. Always use delisting-adjusted returns for
return work.

## Market cap done right — aggregate across share classes (permco)
CRSP `mthcap` is per-PERMNO — one share CLASS. A company with multiple share
classes (dual-class firms: Alphabet's GOOGL+GOOG, Berkshire's BRK.A+BRK.B, Fox,
News Corp, …) has several permnos under ONE `permco`, and the CRSP-Compustat link
maps a gvkey to a single (primary) permno. If you take that permno's `mthcap` as
the firm's market cap, you get only one class and understate the company — often by
roughly half. This silently corrupts market cap and everything derived from it
(enterprise value, size, book-to-market, breakpoints, value-weighting).

The fix: a company's market cap = the SUM of `mthcap` over all permnos sharing its
`permco` in that month; retain the largest-cap permno as the representative. Pull
`permco` in the msf query, aggregate per `(permco, month)`, and attach the
permco-total to the gvkey. Apply it consistently to the current cap, any LAGGED cap
used for matching/sorting, AND to NYSE breakpoints (compute breakpoints on
permco-aggregated caps too). This is exactly the kind of construction bug that two
estimators reading one shared panel both inherit and never catch — so it belongs in
the independent data build and the build-reconciliation check.

## The CRSP-Compustat link
Use `crsp.ccmxpf_lnkhist` (`gvkey, lpermno as permno, linktype, linkprim, linkdt,
linkenddt`), keep `linktype in ('LC','LU')` and `linkprim in ('P','C')`, and respect
the date validity window (`linkdt`/`linkenddt`). Note the link is gvkey↔permno; the
permco-aggregation above is what carries a firm's full equity value across its
classes.

## Standards (these are what get asset-pricing papers rejected — get them right)
- No look-ahead: signals available at t predict returns at t+1; align timing and
  lags explicitly. Accounting data is public only after a reporting lag.
- Use delisting returns; don't silently drop delisted firms (survivorship).
- Handle microcaps deliberately — report BOTH value- and equal-weighted, and a
  price/size screen; a result that lives only equal-weighted in microcaps is a
  small-firm effect, say so.
- Overlapping returns → Newey-West / correct standard errors.
- Winsorize/trim deliberately and state it; the target/return is usually not
  winsorized.
- If you touch many signals/specs, acknowledge multiple-testing exposure.
- State every sample decision in a short data appendix as you go.

## Open Source Asset Pricing (openassetpricing.com, Chen-Zimmermann)
~200 documented predictor signals with code and portfolio returns, public and
un-gated (download directly). Be explicit about which object you use and its
pitfalls:
- The firm-level characteristic panel vs. `PredictorPortsFull` (portfolio returns) —
  don't confuse the two.
- Signed-vs-raw versions of a signal.
- Don't use a "not predictor" flagged signal as if validated.
- Watch sample/rebalancing alignment against your own return series and vintage.

## Red-team an asset-pricing result (run these explicitly)
- Look-ahead / timing: is the signal genuinely lagged relative to the return?
- Survivorship / delisting: are delisted firms handled? drop them and see if it moves.
- Microcaps: does the effect survive value-weighting and a price/size screen?
- Overlapping returns / t-stat inflation: are the standard errors correct?
- Data-snooping: how many signals/specs were tried to get here?
- Market cap / identifiers: is cap aggregated across share classes (permco)? are
  links and merges keeping the rows you think they are?
- OpenAP pitfalls: signed-vs-raw, char-panel vs. portfolio-returns, sample and
  rebalancing misalignment.
