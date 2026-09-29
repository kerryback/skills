---
name: two-stage-dcf
description: >-
  Build a two-stage enterprise valuation of a company from its historical
  financial statements and its text — five explicit forecast years on sales
  growth, EBITDA margin, a sales-to-net-PP&E turnover on next year's sales, a
  depreciation rate, and ratios of each operating asset and liability to that
  year's sales, then those ratios held constant forever. Use this whenever the
  user wants a company valued or a discounted cash flow model built: "value ProFrac", "what is ACDC
  worth", "build me a DCF", "two-stage enterprise valuation", "run a DCF on
  this 10-K", "is this stock cheap on a cash flow basis", or when they point at
  a folder of statements and filings and ask what the business is worth.
  Classifies every reported balance-sheet line and gets that approved before
  forecasting, computes the historical ratios with a script, reads the MD&A,
  risk factors, transcripts and press releases for evidence on each driver,
  suggests assumptions and explains how to choose each one, then writes two HTML
  pages -- the argument and the answer -- and waits for the user to say which
  numbers to change. Point it at a folder of statements and filings, or name the
  files. When the assumptions are settled it delivers an Excel workbook with
  live formulas plus sensitivity and driver-ranking sheets. Expects the
  statements and text to be staged in a folder already — it fetches nothing.
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

## The shape of a run

Six steps, in order. Three of them stop and wait, and the fourth stop is the
long one: you build the two pages and then go round the loop with the user until
they are satisfied. Do not run ahead of a gate -- the whole value of this skill
is that the judgement calls get made by someone who knows the company.

```
  inputs -> classify -> history -> text -> propose, build, and WAIT
                                              |
                                    loop on the numbers
                                              |
                                              v
                                    deliver the workbook
```

### Phase 0 — inventory

The user points you at a folder, or names the files. Both work:

```bash
python dcf_inputs.py ~/data/jbss
```

```python
from dcf_inputs import inventory, describe
print(describe(inventory(financials="jbss.xlsx",
                         transcripts=["calls/FY2026Q4.txt"])))
```

Report what was found and what was not. Then load the statements and say which
fiscal years each covers and how many line items.

If there are no statements, stop and say what you need. Do not go looking on the
web — this skill fetches nothing. If there is no text, carry on and say that the
forecast will rest on history alone; that belongs on the assumptions page, not
buried in the conversation.

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

### Phase 4 — propose, then build and wait (gate)

You advise; the user decides. Everything you put in the assumption table is a
suggestion, and the artifacts say so on their face. What the user actually needs
from you is not a defence of your numbers but enough to choose their own.

So for every driver write, into the bundle:

- `guidance` — how to choose this driver. What makes it move, which of the
  methods below fits this company, what the history is and is not evidence for,
  and what would make you pick a different number. Write it to someone who has
  not read the filings.
- `citations` — the passages that bear on it, each a `{quote, speaker, source}`.
  Quote, do not paraphrase, and name the file. Advice with nothing behind it in
  the documents should say so rather than sounding confident.
- `rationale` — one or two sentences on why the suggested path sits where it
  does, given all of the above.

Ways to project a line, worth naming explicitly when you advise: a constant
percent of sales; a percent of sales varying by year, for a ratio in transition;
a driver other than sales, such as inventory as days of cost of sales or
depreciation as a rate on prior-year PP&E; and flat or zero, for one-time items
and balances with no reason to move.

Terminal sales growth starts at 3.5 percent — `dcf_engine.DEFAULT_TERMINAL_GROWTH`
— unless the company gives you a reason to move it. It is a nominal perpetual
rate, so it carries long-run inflation as well as real growth, which is why it
sits well above any plausible real rate and still below nominal GDP. If you
depart from it, say what the reason was.

Then build the two pages and stop.

```bash
python dcf_assumptions.py bundle.json assumptions.csv
python build_pages.py bundle.json . --csv assumptions.csv --live
python serve.py .                     # once, in another shell
```

Give the user the two links and wait. The assumptions page is what they read;
the conversation that follows is them telling you which numbers to change. Do
not build the workbook yet — it is the finished deliverable, not a working
document.

### The loop

Each time the user gives you numbers: edit `assumptions.csv`, rebuild with
`--live`, and say what moved and by how much. Never hand-edit the HTML, and
never edit the numbers inside `bundle.json` — the CSV is where numbers live.

If they ask why a driver matters, `dcf_engine.driver_ranking(bundle)` tells you
which ones actually move the answer and which are not worth the argument.

Keep going until they say the assumptions are settled.

Sanity rules worth stating out loud when you propose:

- Terminal growth is a nominal perpetual rate. Above nominal GDP means the
  company eventually becomes the economy.
- Terminal growth must be below the WACC or there is no perpetuity, and the
  engine will refuse.
- Year 6 runs on the terminal assumptions and absorbs any gap between year 5's
  balance-sheet ratios and the terminal ones. A large gap makes year 6's capex
  lumpy; the engine warns when it exceeds ten percent.
- Working capital is a ratio to the same year's sales. Net PP&E is the one
  exception, a turnover on next year's sales, because capacity is built ahead of
  the volume it serves.
- The WACC is a single number, editable on the workbook's Inputs sheet. Put
  the CAPM and cost-of-debt derivation in `rates.wacc_derivation` so the
  reasoning travels with both artifacts.

Discuss, iterate, and only move on when the user is satisfied.

### Phase 5 — deliver

Only once the user says the assumptions are settled. Rebuild the pages *without*
`--live`, so nothing you hand over carries a script, and write the workbook:

```bash
python build_pages.py bundle.json . --csv assumptions.csv
python build_workbook.py bundle.json <slug>-dcf.xlsx --csv assumptions.csv
```

Three artifacts, with different jobs.

`<slug>-assumptions.html` is the argument: the suggested numbers beside the
history that informed them, then a section per driver on how to choose it with
the quoted evidence, plus the classification table and the cost of capital. It
deliberately shows no valuation, so reading it does not anchor the reader to an
answer.

`<slug>-valuation.html` is the answer: the assumptions in force, the forecast,
the bridge, the sensitivity grid and any warnings, with a link back.

`assumptions.csv` holds the numbers and nothing else. It is the thing that
changes. Everything slow-moving stays in `bundle.json`.

The workbook is the deliverable. Eight sheets: Inputs, Model, Bridge,
Sensitivity, Drivers, Historical, NOL schedule, Check. Every cell on Model,
Bridge and NOL schedule is a live formula over Inputs, so the user can drive it
without you. Sensitivity and Drivers hold computed values — each cell there is a
whole re-run of the model, which Excel cannot do from a formula — and both
sheets say so on their face.

Report the enterprise value, the bridge, the value per share, every warning, and
the two or three drivers the Drivers sheet says the answer actually turns on.

Warnings are not decoration — a negative implied capex or a non-positive
terminal EBIT means the assumptions are describing a company that does not
exist. If they settle on
different assumptions, edit the bundle and rebuild both rather than hand-editing
either artifact — and update the `rationale` to match what they chose, including
where they overruled you.

## What is in the folder

| File | What it does |
|---|---|
| `dcf_engine.py` | the recursion, the terminal value, the NOL, the bridge. Pure. |
| `dcf_inputs.py` | find the staged inputs, from a folder or filenames |
| `dcf_load.py` | staged statements into a normalised dict |
| `dcf_history.py` | the footing check, and the historical driver ratios |
| `dcf_assumptions.py` | the numbers, to and from `assumptions.csv` |
| `build_pages.py` | the assumptions page and the valuation page |
| `build_workbook.py` | the Excel workbook with live formulas |
| `serve.py` | a no-cache static server for the watch loop |
| `page_assumptions.html`, `page_valuation.html`, `styles.css` | their shells |
| `reference/model.md` | the arithmetic and the bundle schema |
| `reference/classification.md` | the buckets, and the cases that are genuinely hard |
| `reference/staging.md` | the folder layout expected |
| `reference/reading-text.md` | what to look for in the filings, driver by driver |

## Why the workbook checks itself

The recursion exists twice: in Python, and in the workbook's Excel formulas. The
HTML is not a third — it carries no script and renders numbers the engine
already computed, so it cannot drift.

The workbook therefore carries the Python engine's base-case figures on a Check
sheet, beside formulas that resolve to FAIL and turn red. If you ever see a
FAIL, the numbers in that workbook are not to be trusted — say so plainly rather
than working around it.

Run `python -m pytest tests/` after changing either implementation.
