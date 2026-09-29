# Two-stage enterprise valuation skill — design

Date: 2026-09-28
Status: approved, ready for implementation planning

## 1. Purpose

A Claude Code skill that takes a company's staged historical financial statements
and staged text (10-K, transcripts, press releases), proposes a set of forecast
assumptions grounded in both, discusses them with the user, and emits two
artifacts: a self-contained one-page HTML app with editable year-by-year input
cells, and an Excel workbook with live formulas.

It is the reference implementation of the DCF template from MGMT 638's
September 17 session, and it must run on a lab container driven by a weaker
model (GLM 4.7) without producing silently wrong numbers. Its calculation engine
must be callable as a function so the same skill can be wrapped in a Claude Agent
SDK app later.

Distributed as a plugin in the `kerryback` marketplace, alongside `finance-data`,
`wrds`, and `litdb`.

## 2. The model

Two stages: five explicit forecast years, then constant growth and constant
ratios. Year 0 is the last actual fiscal year.

### 2.1 Conventions

Every balance-sheet row in forecast column `t` is the balance at the *end* of
year `t`, stated against year `t+1` sales — the assets and liabilities that
support next year's sales. Net PP&E is edited as a turnover, `S_{t+1} / NPPE_t`,
because that is the conventional way to state it; the reciprocal is displayed
beside it. All other operating balances are edited as a ratio to next-year sales.

Assumption lookup: for driver `a`, `a(t)` is `explicit[t-1]` for `t` in 1..5 and
the terminal value for `t >= 6`. Year 6 therefore runs entirely on terminal
assumptions and is computed, not entered.

### 2.2 Recursion

```
  S_t      = S_{t-1} (1 + g(t))                      sales, t = 1..8
  EBITDA_t = m(t) S_t
  NPPE_t   = S_{t+1} / k(t)                          net PP&E, t = 1..7
  D_t      = d(t) NPPE_{t-1}                         depreciation
  X_t      = NPPE_t - NPPE_{t-1} + D_t               capex, the plug
  A_t^i    = a^i(t) S_{t+1}                          each retained operating asset
  L_t^j    = l^j(t) S_{t+1}                          each retained operating liability
  NWC_t    = sum_i A_t^i - sum_j L_t^j
  EBIT_t   = EBITDA_t - D_t
  FCF_t    = EBITDA_t - Tax_t - X_t - (NWC_t - NWC_{t-1})
```

`NPPE_0`, `NWC_0`, `S_0` and the opening NOL balance are actuals from the
balance sheet, so year 1's capex and working-capital investment are anchored to
the real balance sheet rather than to a ratio.

Sales are computed out to year 8 because `NPPE_7` needs `S_8`.

### 2.3 Taxes and the NOL carryforward

Taxes are unlevered — computed on EBIT, with the interest shield left in the
WACC. `tau(t)` is the marginal cash tax rate on taxable income, not an effective
rate; the effective rate is derived and displayed.

For `t = 1..6`, a running federal NOL balance:

```
  EBIT_t <= 0:   Tax_t  = 0
                 NOL_t  = NOL_{t-1} - EBIT_t
  EBIT_t >  0:   used_t = min( L * EBIT_t, NOL_{t-1} )
                 Tax_t  = tau(t) * (EBIT_t - used_t)
                 NOL_t  = NOL_{t-1} - used_t
```

`L` is the post-2017 federal limitation, default 0.80, editable.

From year 7 onward the perpetuity is taxed at the full terminal rate with no NOL
usage, so that the steady state is genuinely steady. Any carryforward surviving
year 6 is valued separately (section 2.5) and appears as its own line in the
bridge.

### 2.4 Terminal value

Year 5's balance sheet supports year 6 sales, so if year 5's ratios differ from
the terminal ratios, year 6's capex and working-capital investment contain a
one-time level adjustment. Capitalizing that into a perpetuity would be wrong.

Year 6 is therefore run explicitly on terminal assumptions — it absorbs the
transition — and the perpetuity is placed on year 7, which is a clean steady
state because `NPPE_6` and `NWC_6` are both set by terminal ratios against
`S_7`:

```
  EV_ops = sum_{t=1..6} FCF_t / (1+r)^t  +  [ FCF_7 / (r - g) ] / (1+r)^6
```

If the user sets year 5's ratios equal to the terminal ratios, year 6 is already
steady state and this collapses to the textbook formula. The user still fills in
only five explicit columns plus a terminal column.

In steady state, capex is `(g + d)` times prior net PP&E, positive for any
sensible `g` — which is why capex is the plug and depreciation the assumption,
rather than the reverse.

### 2.5 Value of a surviving NOL

Starting from `NOL_6` and `EBIT_7`, with EBIT growing at `g`:

```
  for s = 7, 8, ...:
      used_s   = min( L * EBIT_s, NOL_{s-1} )
      saving_s = tau_T * used_s
      NOL_s    = NOL_{s-1} - used_s
      PV      += saving_s / (1+r)^s
  until NOL_s = 0, or 200 iterations
```

If `EBIT_7 <= 0` the shield is worth zero and a warning is raised, because a
company with negative terminal EBIT has a negative enterprise value and the
model is being asked a question it cannot answer.

### 2.6 Bridge

```
  Enterprise value of operations
  + PV of remaining NOL carryforward
  + non-operating assets          (cash, investments, ...)
  - debt claims                   (all debt, leases if classified as debt, TRA, ...)
  - other equity claims           (preferred, noncontrolling interests, ...)
  = equity value to common
  / diluted shares                = value per share
```

Items classified as excluded contribute nothing. They are classified only to keep
them out of the sales ratios.

### 2.7 Valuation date

As of the end of fiscal year 0. Comparisons to a current market price are
comparisons across a gap, and the app says so.

No mid-year convention. Out of scope.

## 3. Classification

The first deliverable of any run, and the first approval gate. Every reported
balance-sheet line is assigned exactly one bucket:

| Bucket | Meaning |
|---|---|
| `net_ppe` | the productive asset base; driven by the sales-to-PP&E turnover |
| `operating_asset` | driven by a ratio to next-year sales; enters NWC |
| `operating_liability` | driven by a ratio to next-year sales; enters NWC |
| `nonoperating_asset` | added in the bridge at book value |
| `debt_claim` | subtracted in the bridge |
| `equity_claim` | subtracted in the bridge (preferred, NCI, mezzanine) |
| `excluded` | no cash-flow effect and no bridge effect |

Bucket totals are footed against the reported totals so that no line is silently
dropped. A line that appears on the statement and not in the table is an error,
not an omission.

`reference/classification.md` documents the recurring hard cases and states a
default with its reasoning: operating leases, goodwill and acquired intangibles,
deferred tax assets and liabilities, tax receivable agreements, related-party
receivables and payables, noncontrolling interests, mezzanine preferred,
investments in and income from affiliates.

## 4. The run

Five phases. Three stop and wait for the user.

**Phase 0 — inventory.** Report what was found in the staged folder and what is
missing. If statements are absent, fail with the exact layout expected
(`reference/staging.md`) rather than improvising or fetching. The skill does no
network work.

**Phase 1 — classify. GATE.** The reconciliation table of section 3, every line
assigned with a one-line reason for each non-obvious call, footed against
reported totals. Also collected here: diluted shares, the opening NOL from the
tax footnote, preferred and noncontrolling interests. The user approves before
any ratio is computed.

**Phase 2 — history.** `dcf_history.py` computes every driver ratio for all
available fiscal years, plus realized capex and the implied depreciation rate as
a cross-check. Ratios come from a script, never from the model reading numbers
off a page. The output names the anchors that are unusable — an EBITDA margin
from a year with negative EBITDA is not a starting point.

**Phase 3 — text. GATE.** MD&A, risk factors, transcripts and press releases read
against the driver list specifically: guidance, backlog, pricing, announced
capex, capacity, cost programs. The output is evidence per driver, cited to file
and location, not a general summary. The user weighs the evidence before numbers
are proposed from it.

**Phase 4 — propose. GATE.** A table of every driver for years 1..5 and terminal,
each cell with a short rationale naming the history it came from and the text
that supported or contradicted it. Iterates until the user is satisfied.

**Phase 5 — build.** Run the engine, write the app and the workbook, report the
value, the bridge, and a sensitivity grid.

## 5. Repository layout

```
~/repos/skills/plugins/dcf/
  .claude-plugin/plugin.json
  README.md
  skills/dcf/
    SKILL.md
    dcf_load.py          staged statements -> normalized financials.json
    dcf_history.py       financials.json + classification -> historical ratios
    dcf_engine.py        the reference implementation; pure, no I/O
    build_app.py         bundle + template -> <slug>-dcf.html
    build_workbook.py    bundle -> <slug>-dcf.xlsx
    app_template.html    fixed shell, JS port of the engine
    reference/
      model.md
      classification.md
      staging.md
      reading-text.md
    tests/
      test_engine.py
      test_nol.py
      test_parity.py
```

Registered in `.claude-plugin/marketplace.json`.

## 6. The input bundle

The single artifact Claude writes. Claude never writes valuation arithmetic; it
writes this file, and the engine does the rest.

```json
{
  "meta": {
    "company": "...", "ticker": "...",
    "fiscal_year_0": 2025, "fiscal_year_end": "2025-12-31",
    "units": "USD millions", "diluted_shares": 160.4
  },
  "classification": [
    {"line": "Accounts receivable, net", "bucket": "operating_asset",
     "key": "receivables", "note": "..."}
  ],
  "base": {
    "sales": 0.0, "net_ppe": 0.0,
    "operating_assets": {"key": 0.0},
    "operating_liabilities": {"key": 0.0},
    "nonoperating_assets": {"key": 0.0},
    "debt_claims": {"key": 0.0},
    "equity_claims": {"key": 0.0},
    "nol": 0.0
  },
  "assumptions": {
    "sales_growth":      {"explicit": [5 values], "terminal": 0.0, "rationale": "..."},
    "ebitda_margin":     {"explicit": [5 values], "terminal": 0.0, "rationale": "..."},
    "sales_to_net_ppe":  {"explicit": [5 values], "terminal": 0.0, "rationale": "..."},
    "depreciation_rate": {"explicit": [5 values], "terminal": 0.0, "rationale": "..."},
    "cash_tax_rate":     {"explicit": [5 values], "terminal": 0.0, "rationale": "..."},
    "operating_assets":      {"key": {"explicit": [5], "terminal": 0.0, "rationale": "..."}},
    "operating_liabilities": {"key": {"explicit": [5], "terminal": 0.0, "rationale": "..."}}
  },
  "rates": {
    "wacc": 0.096, "wacc_derivation": "...", "nol_limitation": 0.80
  },
  "history": { "years": [...], "ratios": {...} }
}
```

`history` is carried through only so the artifacts can show historical columns
beside the forecast columns; the engine ignores it.

The engine exposes one function:

```python
run_model(bundle) -> {
    "schedule": [ per-year dict, years 1..7 ],
    "ev_ops": float, "pv_explicit": float, "pv_terminal": float,
    "pv_nol": float, "bridge": [ {label, amount} ],
    "equity_value": float, "value_per_share": float,
    "warnings": [ str ]
}
```

`wacc <= terminal growth` raises `ValueError` — the perpetuity does not exist and
there is no number to return. Everything else is a warning string returned
alongside a full result: non-positive sales, negative implied capex in any year,
an NOL alive at year 6, a year-5-to-terminal ratio discontinuity larger than 10
percent, non-positive terminal EBIT.

## 7. The HTML app

One self-contained file. No network dependencies of any kind — it has to open in
a lab container.

Layout: historical columns on the left, greyed and read-only; five editable
forecast years; a terminal column. Input rows grouped as growth and margin, PP&E
and depreciation, operating assets (one row per retained line, built at load time
from the classification table), operating liabilities, taxes. WACC, the NOL
limitation, and diluted shares are single editable cells.

Below the inputs: the schedule out to year 7, the bridge, the equity value and
value per share, and a WACC-by-terminal-growth sensitivity grid that recomputes
with everything else. A notes panel carries the WACC derivation, the
classification table, and the phase-4 rationales, so the reasoning travels with
the file.

Every edit recomputes. A reset control restores the proposed assumptions. The
warnings of section 6 are shown inline.

The input grid is data-driven from the classification table, so a company with
eight retained operating lines gets eight rows and one with four gets four,
without Claude writing any UI code.

## 8. The Excel workbook

The same model with live formulas, not pasted values, written by
`build_workbook.py` with the same row structure driven by the same classification
table. Sheets: Inputs, Model, Bridge, Historical, Check.

## 9. Consistency self-checks

Three implementations of one recursion — Python, JavaScript, Excel formulas —
must agree. Each port carries the Python engine's base-case schedule and checks
itself against it at the moment someone opens the artifact.

The app recomputes in JS on load and compares every schedule cell to the embedded
baseline within a relative tolerance of 1e-9; a mismatch paints a red banner.

The workbook's Check sheet holds the same baseline with formulas that resolve to
FAIL and turn red in Excel when a computed cell disagrees.

A port that drifts announces itself rather than quietly showing a different
number.

## 10. Tests

Against the Python engine, which is the only one that has to be right in the
first place.

1. Set all five explicit years to the terminal values; enterprise value must
   equal a closed-form Gordon calculation written independently in the test.
   Catches a discount-exponent error or a botched year-6 transition.
2. Zero growth, zero depreciation, no NOL: FCF must equal EBITDA times one minus
   the tax rate.
3. Steady state: FCF_8 must equal FCF_7 times (1 + g).
4. A hand-worked NOL case — two loss years then profit — checked against
   arithmetic written out in the test.
5. The NOL shield PV against a closed-form sum for a case where the 80%
   limitation does not bind.
6. Bridge arithmetic, including a company with preferred and noncontrolling
   interests.
7. Warnings fire on each of their conditions.
8. Parity: run the JS engine under node and compare to Python. Skipped with a
   clear message where node is not installed; the in-browser banner is the
   guarantee that matters.

## 11. Out of scope

Data retrieval of any kind — the skill expects a staged folder. Mid-year
convention. Multi-currency and multi-segment models. Scenario management beyond
the single sensitivity grid. Round-tripping edited assumptions from the browser
back into the conversation; the user retypes what they changed, or edits the
bundle.
