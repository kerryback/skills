"""Write the valuation as a self-contained one-page report.

The page carries no script at all. Every figure on it is rendered here from
``dcf_engine.run_model`` and ``dcf_engine.sensitivity_grid``, which means the
recursion exists once in Python and once in the workbook's formulas, and the
report cannot drift from the engine because it does no arithmetic.

Driving the model is the workbook's job. This file is the readable record: what
was assumed, why, what the history showed, how every balance-sheet line was
classified, and what the answer is sensitive to.

No network references of any kind -- it has to open in a lab container.
"""

import html
import os

from dcf_engine import (N_EXPLICIT, PERPETUITY_YEAR, TRANSITION_YEAR,
                        run_model, sensitivity_axes, sensitivity_grid)

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "app_template.html")

SCALAR_ROWS = [
    ("group", "Growth and margin"),
    ("sales_growth", "Sales growth", "pct"),
    ("ebitda_margin", "EBITDA margin", "pct"),
    ("group", "Property, plant and equipment"),
    ("sales_to_net_ppe", "Next-year sales / net PP&E", "mult"),
    ("depreciation_rate", "Depreciation / prior net PP&E", "pct"),
]

SCHEDULE_ROWS = [
    ("sales", "Sales", "num"),
    ("ebitda", "EBITDA", "num"),
    ("depreciation", "Depreciation", "num"),
    ("ebit", "EBIT", "num"),
    ("nol_open", "NOL carryforward, opening", "num"),
    ("nol_used", "NOL used", "num"),
    ("taxable_income", "Taxable income", "num"),
    ("tax", "Cash taxes", "num"),
    ("effective_tax_rate", "Effective tax rate", "pct"),
    ("net_ppe", "Net PP&E, closing", "num"),
    ("capex", "Capital expenditure", "num"),
    ("nwc", "Net working capital, closing", "num"),
    ("delta_nwc", "Investment in working capital", "num"),
    ("fcf", "Free cash flow", "num"),
    ("discount_factor", "Discount factor", "factor"),
    ("pv_fcf", "PV of free cash flow", "num"),
]


# --------------------------------------------------------------------------
# formatting
# --------------------------------------------------------------------------

def esc(text):
    return html.escape(str(text), quote=False)


def fmt(value, kind):
    if value is None:
        return "—"
    if kind == "pct":
        return f"{value * 100:,.1f}%"
    if kind == "mult":
        return f"{value:,.2f}×"
    if kind == "factor":
        return f"{value:,.4f}"
    if kind == "share":
        return f"{value:,.2f}"
    return f"{value:,.1f}" if abs(value) < 100 else f"{value:,.0f}"


def _labels(bundle):
    return {c["key"]: c["line"] for c in bundle.get("classification", [])
            if c.get("key")}


def _input_rows(bundle):
    """The assumption rows, in display order, as (key, label, kind, side)."""
    labels = _labels(bundle)
    rows = list(SCALAR_ROWS)
    rows.append(("group", "Operating assets, as a share of next-year sales"))
    for key in bundle["assumptions"]["operating_assets"]:
        rows.append((key, labels.get(key, key), "pct", "operating_assets"))
    rows.append(("group", "Operating liabilities, as a share of next-year sales"))
    for key in bundle["assumptions"]["operating_liabilities"]:
        rows.append((key, labels.get(key, key), "pct", "operating_liabilities"))
    rows.append(("group", "Taxes"))
    rows.append(("cash_tax_rate", "Cash tax rate on taxable income", "pct"))
    return rows


def _spec(bundle, row):
    a = bundle["assumptions"]
    return a[row[3]][row[0]] if len(row) > 3 else a[row[0]]


def _history_series(bundle, row):
    ratios = ((bundle.get("history") or {}).get("ratios") or {})
    if len(row) > 3:
        return (ratios.get(row[3]) or {}).get(row[0]) or {}
    return ratios.get(row[0]) or {}


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------

def _inputs_table(bundle):
    years = ((bundle.get("history") or {}).get("years") or [])[-5:]
    span = len(years) + N_EXPLICIT + 2

    out = ["<table><thead><tr><th>Assumption</th>"]
    out += [f"<th>{esc(y)}</th>" for y in years]
    out += [f"<th class='fc'>Year {t}</th>" for t in range(1, N_EXPLICIT + 1)]
    out.append("<th class='fc'>Terminal</th></tr></thead><tbody>")

    for row in _input_rows(bundle):
        if row[0] == "group":
            out.append(f"<tr class='group'><td colspan='{span}'>{esc(row[1])}</td></tr>")
            continue
        key, label, kind = row[0], row[1], row[2]
        history, spec = _history_series(bundle, row), _spec(bundle, row)
        out.append(f"<tr><td>{esc(label)}</td>")
        for year in years:
            value = history.get(year, history.get(str(year)))
            out.append(f"<td class='hist'>{fmt(value, kind)}</td>")
        for t in range(N_EXPLICIT):
            out.append(f"<td class='fc'>{fmt(spec['explicit'][t], kind)}</td>")
        out.append(f"<td class='fc'>{fmt(spec['terminal'], kind)}</td></tr>")

    return "".join(out) + "</tbody></table>"


def _rates_block(bundle):
    rates, meta, base = bundle["rates"], bundle["meta"], bundle["base"]
    parts = [
        f"WACC <b>{fmt(rates['wacc'], 'pct')}</b>",
        f"terminal growth <b>{fmt(bundle['assumptions']['sales_growth']['terminal'], 'pct')}</b>",
        f"NOL limitation <b>{fmt(rates.get('nol_limitation', 0.80), 'pct')}</b>",
        f"opening NOL <b>{fmt(float(base.get('nol') or 0.0), 'num')}</b>",
        f"diluted shares <b>{fmt(meta.get('diluted_shares'), 'num')}</b>",
    ]
    return "<p class='rates'>" + " &nbsp;·&nbsp; ".join(parts) + "</p>"


def _schedule_table(result):
    out = ["<table><thead><tr><th>Forecast</th>"]
    for row in result["schedule"]:
        label = f"Year {row['year']}"
        if row["year"] == TRANSITION_YEAR:
            label += " · transition"
        elif row["year"] == PERPETUITY_YEAR:
            label += " · perpetuity"
        out.append(f"<th class='fc'>{esc(label)}</th>")
    out.append("</tr></thead><tbody>")

    for key, label, kind in SCHEDULE_ROWS:
        cls = " class='total'" if key == "fcf" else ""
        out.append(f"<tr{cls}><td>{esc(label)}</td>")
        for row in result["schedule"]:
            out.append(f"<td>{fmt(row[key], kind)}</td>")
        out.append("</tr>")
    return "".join(out) + "</tbody></table>"


def _bridge_table(bundle, result):
    shares = bundle["meta"].get("diluted_shares")
    out = ["<table><tbody>"]

    def line(label, value, kind="num", total=False):
        cls = " class='total'" if total else ""
        out.append(f"<tr{cls}><td>{esc(label)}</td>"
                   f"<td>{fmt(value, kind)}</td></tr>")

    line("PV of free cash flow, years 1 to 6", result["pv_explicit"])
    line("Terminal value at the end of year 6", result["terminal_value"])
    line("PV of the terminal value", result["pv_terminal"])
    for i, item in enumerate(result["bridge"]):
        line(item["label"], item["amount"], total=(i == 0))
    line("Equity value", result["equity_value"], total=True)
    line("Diluted shares", shares)
    line("Value per share", result["value_per_share"], "share", total=True)
    return "".join(out) + "</tbody></table>"


def _sensitivity_table(bundle):
    waccs, growths = sensitivity_axes(bundle)
    grid = sensitivity_grid(bundle, waccs, growths)
    base_wacc = bundle["rates"]["wacc"]
    base_growth = bundle["assumptions"]["sales_growth"]["terminal"]

    out = ["<table><thead><tr><th>WACC \\ terminal growth</th>"]
    out += [f"<th>{fmt(g, 'pct')}</th>" for g in growths]
    out.append("</tr></thead><tbody>")
    for i, wacc in enumerate(waccs):
        out.append(f"<tr><td>{fmt(wacc, 'pct')}</td>")
        for j, growth in enumerate(growths):
            here = (abs(wacc - base_wacc) < 1e-12
                    and abs(growth - base_growth) < 1e-12)
            cls = "sens here" if here else "sens"
            out.append(f"<td class='{cls}'>{fmt(grid[i][j], 'share')}</td>")
        out.append("</tr>")
    return "".join(out) + "</tbody></table>"


def _classification_table(bundle):
    rows = bundle.get("classification") or []
    if not rows:
        return "<p class='note'>No classification was recorded.</p>"
    out = ["<table><thead><tr><th>Reported line</th><th>Bucket</th>"
           "<th>Why</th></tr></thead><tbody>"]
    for c in rows:
        out.append(f"<tr><td>{esc(c['line'])}</td>"
                   f"<td class='wrap'>{esc(c['bucket'])}</td>"
                   f"<td class='wrap'>{esc(c.get('note') or '')}</td></tr>")
    return "".join(out) + "</tbody></table>"


def _rationales(bundle):
    out = []
    for row in _input_rows(bundle):
        if row[0] == "group":
            continue
        spec = _spec(bundle, row)
        if spec.get("rationale"):
            out.append(f"<p class='rationale'><b>{esc(row[1])}.</b> "
                       f"{esc(spec['rationale'])}</p>")
    return "".join(out) or \
        "<p class='note'>No rationales were recorded with these assumptions.</p>"


def _warnings(result):
    if not result["warnings"]:
        return ""
    items = "".join(f"<li>{esc(w)}</li>" for w in result["warnings"])
    return f"<ul class='warnings'>{items}</ul>"


def _history_notes(bundle):
    notes = (bundle.get("history") or {}).get("notes") or []
    if not notes:
        return "<p class='note'>The history raised nothing worth flagging.</p>"
    return "".join(f"<p class='note body'>{esc(n)}</p>" for n in notes)


# --------------------------------------------------------------------------

def build_app(bundle, out_path):
    """Render the report for ``bundle`` and return the path written."""
    result = run_model(bundle)
    meta = bundle["meta"]

    company = meta.get("company", "Company")
    if meta.get("ticker"):
        company += f" ({meta['ticker']})"

    subtitle = (
        f"Valued as of the end of fiscal {meta.get('fiscal_year_0', '')}"
        + (f" ({meta['fiscal_year_end']})" if meta.get("fiscal_year_end") else "")
        + f". All figures in {meta.get('units', 'the units of the statements')}. "
        f"A comparison with today's market price is a comparison across that gap."
    )

    with open(TEMPLATE, encoding="utf-8") as fh:
        page = fh.read()

    for token, value in [
        ("__TITLE__", esc(f"{meta.get('company', 'Company')} — two-stage valuation")),
        ("__COMPANY__", esc(company)),
        ("__SUBTITLE__", esc(subtitle)),
        ("__WARNINGS__", _warnings(result)),
        ("__EV__", fmt(result["ev_ops"], "num")),
        ("__EQUITY__", fmt(result["equity_value"], "num")),
        ("__PER_SHARE__", fmt(result["value_per_share"], "share")),
        ("__INPUTS__", _inputs_table(bundle)),
        ("__RATES__", _rates_block(bundle)),
        ("__SCHEDULE__", _schedule_table(result)),
        ("__BRIDGE__", _bridge_table(bundle, result)),
        ("__SENSITIVITY__", _sensitivity_table(bundle)),
        ("__WACC_NOTE__", esc(bundle["rates"].get("wacc_derivation")
                              or "No derivation was recorded for the discount rate.")),
        ("__RATIONALES__", _rationales(bundle)),
        ("__HISTORY_NOTES__", _history_notes(bundle)),
        ("__CLASSIFICATION__", _classification_table(bundle)),
    ]:
        page = page.replace(token, value)

    leftover = [t for t in page.split("__") if t.isupper() and t.isidentifier()]
    if leftover:
        raise RuntimeError(f"template tokens left unfilled: {sorted(set(leftover))}")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return out_path


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("usage: build_app.py <bundle.json> <out.html>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(build_app(json.load(fh), sys.argv[2]))
