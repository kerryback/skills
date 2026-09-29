# dcf

Two-stage enterprise valuation from staged financial statements and company
text.

Five explicit forecast years on sales growth, EBITDA margin, a sales-to-net-PP&E
turnover on next year's sales, a depreciation rate, and ratios of each operating
asset and liability to that year's sales; then those ratios held constant
forever. PP&E leads sales by a year because capacity is built ahead of the volume
it serves; working capital arises from the volume itself. Capex is the plug,
so steady-state capex lands at (g + d) times prior net PP&E and cannot go
negative on ordinary inputs. Year 6 runs on the terminal assumptions and absorbs
the balance-sheet transition; the perpetuity sits on year 7, which is genuinely
steady state. A running NOL carryforward shelters the explicit years, and
anything surviving year 6 is valued separately and shown in the bridge rather
than contaminating the perpetuity.

A run classifies every reported balance-sheet line and gets that approved,
computes the historical ratios with a script, reads the MD&A, risk factors,
transcripts and press releases for evidence on each driver, proposes assumptions
and discusses them, then writes:

- `<slug>-assumptions.html`, the argument: the suggested numbers beside the
  history that informed them, then a section per driver on how to choose it with
  the quoted evidence, plus the classification table. It shows no valuation, so
  reading it does not anchor you to an answer.
- `<slug>-valuation.html`, the answer: assumptions in force, forecast, bridge,
  sensitivity, warnings, and a link back.
- `assumptions.csv`, the numbers and nothing else — the part that changes. Edit
  it and rebuild; everything slow-moving stays in `bundle.json`.
- an Excel workbook whose every model cell is a live formula.

Neither page carries a script or a network reference. `build_pages.py --live`
adds a small reload poller for the edit-and-watch loop, served by `serve.py`;
rebuild without the flag before sending anything to anyone.

The recursion exists twice — Python and Excel formulas — so the workbook carries
the Python engine's base-case figures on a Check sheet beside formulas that
resolve to FAIL and turn red. The HTML does no arithmetic, so it cannot drift.

It fetches nothing. Point it at a folder that already holds the statements.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install two-stage-dcf@kerryback
```

## Tests

```
cd skills/dcf && python -m pytest tests/
```

The workbook recalculation test needs LibreOffice; it skips cleanly without it,
and the workbook's own Check sheet covers that case the moment someone opens the
file in Excel.
