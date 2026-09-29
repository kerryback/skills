# dcf

Two-stage enterprise valuation from staged financial statements and company
text.

Five explicit forecast years on sales growth, EBITDA margin, a sales-to-net-PP&E
turnover, a depreciation rate, and ratios of each operating asset and liability
to next-year sales; then those ratios held constant forever. Capex is the plug,
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

- a self-contained one-page HTML app with editable year-by-year input cells and
  an editable terminal column, recomputing on every keystroke, with no network
  dependencies of any kind
- an Excel workbook whose every model cell is a live formula

The recursion exists three times — Python, JavaScript, Excel formulas — so both
artifacts carry the Python engine's base-case numbers and re-derive them on
open. The app paints a red banner if it disagrees; the workbook's Check sheet
turns red.

It fetches nothing. Point it at a folder that already holds the statements.

## Install

```
/plugin marketplace add kerryback/skills
/plugin install dcf@kerryback
```

## Tests

```
cd skills/dcf && python -m pytest tests/
```

The JavaScript parity test needs `node` and the workbook recalculation test
needs LibreOffice; both skip cleanly without them, and the artifacts' own
self-checks cover those cases at the moment someone opens them.
