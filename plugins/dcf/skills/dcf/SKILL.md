---
name: dcf
description: >-
  Build a two-stage enterprise valuation of a company from its historical
  financial statements and its text — five explicit forecast years on sales
  growth, EBITDA margin, a sales-to-net-PP&E turnover, a depreciation rate, and
  ratios of each operating asset and liability to next-year sales, then those
  ratios held constant forever. Use this whenever the user wants a company
  valued or a discounted cash flow model built: "value ProFrac", "what is ACDC
  worth", "build me a DCF", "two-stage enterprise valuation", "run a DCF on
  this 10-K", "is this stock cheap on a cash flow basis", or when they point at
  a folder of statements and filings and ask what the business is worth.
  Classifies every reported balance-sheet line and gets that approved before
  forecasting, computes the historical ratios with a script, reads the MD&A,
  risk factors, transcripts and press releases for evidence on each driver,
  proposes assumptions and discusses them, then writes an interactive one-page
  HTML app and an Excel workbook with live formulas. Expects the statements and
  text to be staged in a folder already — it fetches nothing.
---

# Two-stage enterprise valuation

Value a company by forecasting five explicit years and then holding every ratio
constant forever. The arithmetic lives in `dcf_engine.py` and is fixed. Your job
is to decide what the company's balance sheet means, what the drivers should be,
and to argue for those choices from the history and the text.

## The one rule

You never write valuation arithmetic. You write a JSON bundle; the scripts do
the rest. If you find yourself computing an enterprise value in your head, in a
message, or in an ad-hoc script, stop — that number will disagree with the
artifacts and you will not know which is wrong.

Historical ratios come from `dcf_history.py`, not from reading figures off a
page. Forecast figures come from `dcf_engine.py`. There is no third source.

## Before you start

Everything is staged; this skill fetches nothing. Read `reference/staging.md`
for the folder layout. If the statements are missing, say exactly what is
missing and stop — do not go looking for it on the web, and do not invent it.

The scripts need `pandas` and `openpyxl`. Run them with whatever Python the
project uses.

## The five phases

Work through them in order. Three of them stop and wait for the user. Do not
run ahead of a gate: the whole value of this skill is that the judgment calls
get made by a person who knows the company.

### Phase 0 — inventory

Load each statement and report what you found:

```bash
python dcf_load.py    # or import load_statements and call it
```

Say which fiscal years each statement covers, how many line items, and which of
the text sources are present. Name what is missing.

### Phase 1 — classify (gate)

Read the balance sheet and assign every reported line to exactly one bucket:
`net_ppe`, `operating_asset`, `operating_liability`, `nonoperating_asset`,
`debt_claim`, `equity_claim`, `excluded`. Give each non-obvious call a one-line
reason. `reference/classification.md` has the buckets and the recurring hard
cases — leases, goodwill, deferred taxes, tax receivable agreements,
related-party balances, noncontrolling interests, mezzanine preferred.

Then foot it:

```python
from dcf_history import check_footing
check_footing(classification, balance_lines, reported_total)
```

This raises if a reported line is unclassified, and names the line and what it
was worth. That is deliberate: a line quietly left out of the table is exactly
how a real liability goes missing from a valuation. `excluded` is a bucket —
use it rather than omitting a line.

Collect here too: diluted shares, the opening federal NOL carryforward from the
tax footnote, and the preferred and noncontrolling interests.

Show the user the table and wait. Do not compute a ratio until they approve it.

### Phase 2 — history

```python
from dcf_history import historical_ratios
out = historical_ratios(financials, classification, sales_line="Revenues",
                        ebitda_line=..., depreciation_line=...)
```

Present every driver year by year, plus realised capex from the PP&E
roll-forward so the depreciation rate can be sanity-checked against what the
company actually spent. Read `out["notes"]` aloud — it names the anchors that
are unusable. An EBITDA margin from a year with negative EBITDA is not a
starting point, and saying so is more useful than averaging it in.

### Phase 3 — the text (gate)

Read the MD&A, risk factors, transcripts and press releases against the driver
list specifically. `reference/reading-text.md` says what to look for, driver by
driver. Output evidence per driver, each citation naming the file and where in
it — not a general summary of the company.

Show the user the evidence and wait, before you propose numbers from it.

### Phase 4 — propose (gate)

Write the assumption table: every driver, years 1 through 5 and terminal, each
with a short rationale naming the history it came from and the text that
supported or contradicted it. Put the rationale in the bundle's `rationale`
fields — it travels into the app's notes panel.

Sanity rules worth stating out loud when you propose:

- Terminal growth is a nominal perpetual rate. Above nominal GDP means the
  company eventually becomes the economy.
- Terminal growth must be below the WACC or there is no perpetuity, and the
  engine will refuse.
- Year 6 runs on the terminal assumptions and absorbs any gap between year 5's
  balance-sheet ratios and the terminal ones. A large gap makes year 6's capex
  lumpy; the engine warns when it exceeds ten percent.
- The WACC is a single editable cell. Show the CAPM and cost-of-debt
  derivation in `rates.wacc_derivation` so it travels with the file.

Discuss, iterate, and only move on when the user is satisfied.

### Phase 5 — build

Write `bundle.json` per `reference/model.md`, then:

```bash
python build_app.py bundle.json <slug>-dcf.html
python build_workbook.py bundle.json <slug>-dcf.xlsx
```

Report the enterprise value, the bridge, the value per share, and every warning
the engine returned. Warnings are not decoration — a negative implied capex or a
non-positive terminal EBIT means the assumptions are describing a company that
does not exist.

Tell the user the app recomputes on every keystroke and the workbook's formulas
are live, so both are theirs to push on.

## What is in the folder

| File | What it does |
|---|---|
| `dcf_engine.py` | the recursion, the terminal value, the NOL, the bridge. Pure. |
| `dcf_load.py` | staged statements into a normalised dict |
| `dcf_history.py` | the footing check, and the historical driver ratios |
| `build_app.py` | the interactive one-page HTML app |
| `build_workbook.py` | the Excel workbook with live formulas |
| `app_template.html` | the app's shell and its JavaScript port of the engine |
| `reference/model.md` | the arithmetic and the bundle schema |
| `reference/classification.md` | the buckets, and the cases that are genuinely hard |
| `reference/staging.md` | the folder layout expected |
| `reference/reading-text.md` | what to look for in the filings, driver by driver |

## Why the artifacts check themselves

The recursion exists three times: in Python, in the app's JavaScript, and in
Excel formulas. The app and the workbook each carry the Python engine's
base-case numbers and re-derive them on open. The app paints a red banner if it
disagrees; the workbook's Check sheet turns red. If you ever see either, the
numbers on that artifact are not to be trusted — say so plainly rather than
working around it.

Run `python -m pytest tests/` after changing any of the three.
