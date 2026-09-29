# What this skill expects to find

It fetches nothing. Point it at a folder that already holds the statements and,
ideally, the text. If the statements are missing, it says so and stops rather
than going to look.

## The layout

```
<company>/
  financials.xlsx          three sheets, or three CSVs — see below
  10k/            *.htm    the filings themselves
  transcripts/    *        earnings call transcripts
  press/          *        press releases
```

Nothing but the statements is required. With no text, the skill forecasts off
history alone and says that is what it did.

## Statement shape

Line labels down the first column, fiscal years across one row. Both of these
parse, and the loader finds the header row itself:

```
,2025-12-31,2024-12-31,2023-12-31
Cash and cash equivalents,22.9,14.8,25.3
Accounts receivable, net,266.8,312.7,346.1
```

```
ProFrac Holding Corp. — Consolidated Balance Sheets
Fiscal years ending December 31. $ millions.
Source: SEC EDGAR, XBRL financial statements.

Line item,FY2023,FY2024,FY2025
Cash and cash equivalents,25.3,14.8,22.9
```

Metadata rows above the header are fine. Blank rows and section headers such as
`Current assets:` are dropped. Values may carry thousands separators, currency
symbols, or the accounting convention of parenthesising negatives.

A workbook is read one sheet at a time:

```python
from dcf_load import load_statements
balance = load_statements("financials.xlsx", sheet="Balance Sheet")
income  = load_statements("financials.xlsx", sheet="Income Statement")
cash    = load_statements("financials.xlsx", sheet="Cash Flow Statement")
```

Fiscal years come back ascending however the file ordered them. Duplicate line
labels are disambiguated as `Other`, `Other (2)`.

## What gets used

- Balance sheet: every line, classified. This is the gate.
- Income statement: revenue, and enough to construct EBITDA and depreciation.
- Cash flow statement: reported depreciation and capex, to check the PP&E
  roll-forward against what the company actually spent.
- Tax footnote: the opening federal NOL carryforward, and whether there is a
  valuation allowance against it.
- Cover or equity note: diluted shares.

## When it will not load

```
no row looks like a fiscal year header
```

means no row had a cell that parses as a year in any column but the first.
Check that the years are across a row rather than down a column, and that the
file is the statement rather than a summary of it.

## A note for the course

Five or six fiscal years is the right window. Fewer than three and the
historical ratios have nothing to say; more and you are averaging across a
different company.

Where each year comes from matters. The ACDC workbook takes each year from the
most recent 10-K that reports it, so the figures are restated. That is the right
choice for valuation, where you want the best current estimate of what happened,
and the wrong one for backtesting a signal, where you want what was knowable at
the time.
