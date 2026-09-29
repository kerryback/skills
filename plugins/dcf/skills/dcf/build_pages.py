"""Write the two pages: how to choose the assumptions, and what they are worth.

They are separate documents on purpose. The assumptions page is an argument --
each driver's history, what makes it move, what would make you choose
differently, and the quoted evidence -- and it shows no valuation at all, so
that reading it does not anchor you to an answer. The valuation page is the
answer, with a link back.

Neither page does arithmetic. Every figure is rendered here from
``dcf_engine.run_model`` and ``dcf_engine.sensitivity_grid``, so the recursion
exists once in Python and once in the workbook's formulas, and a page cannot
disagree with the engine that wrote it.

A shipped page carries no script. The live-reload poller is injected only when
``live=True``, which is the watch loop, never the artifact you send someone.

No network references of any kind -- they have to open in a lab container.
"""

import html
import os

from dcf_engine import (N_EXPLICIT, PERPETUITY_YEAR, TRANSITION_YEAR,
                        run_model, sensitivity_axes, sensitivity_grid)

HERE = os.path.dirname(os.path.abspath(__file__))
STYLES = os.path.join(HERE, "styles.css")
ASSUMPTIONS_TEMPLATE = os.path.join(HERE, "page_assumptions.html")
VALUATION_TEMPLATE = os.path.join(HERE, "page_valuation.html")

#: Injected only in watch mode. It asks the server whether the file it is
#: looking at has changed, and reloads if so -- no arithmetic, and absent from
#: anything anyone receives.
LIVE_RELOAD = """<script>
(function () {
  var seen = null;
  function check() {
    return fetch(location.href, { method: "HEAD", cache: "no-store" })
      .then(function (r) {
        var stamp = r.headers.get("Last-Modified") || r.headers.get("ETag");
        if (!stamp) return;
        if (seen && stamp !== seen) location.reload();
        seen = stamp;
      })
      .catch(function () {});
  }
  // Seed immediately rather than on the first tick. Otherwise a rebuild that
  // lands between load and that tick is recorded as the baseline and the page
  // never reloads -- which is precisely what happens when you rebuild straight
  // after opening the page.
  check();
  setInterval(check, 1000);
})();
</script>"""

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
    rows.append(("group", "Operating assets, as a share of sales"))
    for key in bundle["assumptions"]["operating_assets"]:
        rows.append((key, labels.get(key, key), "pct", "operating_assets"))
    rows.append(("group", "Operating liabilities, as a share of sales"))
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


def _history_strip(bundle, row):
    """The driver's own history and the suggested path, on one line."""
    history = _history_series(bundle, row)
    years = ((bundle.get("history") or {}).get("years") or [])[-6:]
    kind = row[2]
    seen = [(y, history.get(y, history.get(str(y)))) for y in years]
    seen = [(y, v) for y, v in seen if v is not None]

    parts = []
    if seen:
        parts.append("History " + ", ".join(
            f"{y} <b>{fmt(v, kind)}</b>" for y, v in seen))
    spec = _spec(bundle, row)
    parts.append("Suggested " + ", ".join(
        f"<b>{fmt(v, kind)}</b>" for v in spec["explicit"])
        + f", then <b>{fmt(spec['terminal'], kind)}</b> forever")
    return "<p class='strip'>" + " &nbsp;·&nbsp; ".join(parts) + "</p>"


def _citations(spec):
    out = []
    for c in spec.get("citations") or []:
        who = ", ".join(x for x in (c.get("speaker"), c.get("source")) if x)
        out.append(f"<blockquote>&ldquo;{esc(c['quote'])}&rdquo;"
                   + (f"<cite>{esc(who)}</cite>" if who else "")
                   + "</blockquote>")
    return "".join(out)


def _guidance(bundle):
    """The advisory document: how to choose each driver, not a defence of one."""
    out = []
    for row in _input_rows(bundle):
        if row[0] == "group":
            continue
        spec = _spec(bundle, row)
        body = spec.get("guidance") or spec.get("rationale")
        if not body:
            continue
        out.append(f"<section class='guide'><h3>{esc(row[1])}</h3>")
        out.append(_history_strip(bundle, row))
        out.append(f"<p class='how'>{esc(body)}</p>")
        out.append(_citations(spec))
        if spec.get("guidance") and spec.get("rationale"):
            out.append(f"<p class='how'><i>Why the suggestion sits where it "
                       f"does.</i> {esc(spec['rationale'])}</p>")
        out.append("</section>")
    return "".join(out) or (
        "<p class='note'>No guidance was recorded with these assumptions. The "
        "numbers above are then bare suggestions with nothing behind them, which "
        "is not enough to choose from.</p>")


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
# rendering
# --------------------------------------------------------------------------

def _styles():
    with open(STYLES, encoding="utf-8") as fh:
        return fh.read()


def _header_bits(bundle):
    meta = bundle["meta"]
    company = meta.get("company", "Company")
    if meta.get("ticker"):
        company += f" ({meta['ticker']})"
    subtitle = (
        f"Fiscal {meta.get('fiscal_year_0', '')}"
        + (f" ended {meta['fiscal_year_end']}" if meta.get("fiscal_year_end") else "")
        + f" is year 0. All figures in "
        f"{meta.get('units', 'the units of the statements')}."
    )
    return company, subtitle


def _render(template_path, tokens):
    with open(template_path, encoding="utf-8") as fh:
        page = fh.read()
    for token, value in tokens.items():
        page = page.replace(token, value)
    leftover = [t for t in page.split("__") if t.isupper() and t.isidentifier()]
    if leftover:
        raise RuntimeError(f"template tokens left unfilled: {sorted(set(leftover))}")
    return page


def _write(page, out_path):
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(page)
    return out_path


def build_assumptions(bundle, out_path, valuation_href="valuation.html", live=False):
    """The advisory document. Shows no valuation, by design."""
    company, subtitle = _header_bits(bundle)
    page = _render(ASSUMPTIONS_TEMPLATE, {
        "__STYLES__": _styles(),
        "__TITLE__": esc(f"{bundle['meta'].get('company', 'Company')} "
                         f"— choosing the assumptions"),
        "__COMPANY__": esc(company),
        "__SUBTITLE__": esc(subtitle),
        "__VALUATION_HREF__": esc(valuation_href),
        "__INPUTS__": _inputs_table(bundle),
        "__RATES__": _rates_block(bundle),
        "__GUIDANCE__": _guidance(bundle),
        "__HISTORY_NOTES__": _history_notes(bundle),
        "__WACC_NOTE__": esc(bundle["rates"].get("wacc_derivation")
                             or "No derivation was recorded for the discount rate."),
        "__CLASSIFICATION__": _classification_table(bundle),
        "__LIVE__": LIVE_RELOAD if live else "",
    })
    return _write(page, out_path)


def build_valuation(bundle, out_path, assumptions_href="assumptions.html",
                    csv_name="assumptions.csv", live=False):
    """The answer, with a link back to the argument."""
    result = run_model(bundle)
    company, subtitle = _header_bits(bundle)
    page = _render(VALUATION_TEMPLATE, {
        "__STYLES__": _styles(),
        "__TITLE__": esc(f"{bundle['meta'].get('company', 'Company')} "
                         f"— two-stage valuation"),
        "__COMPANY__": esc(company),
        "__SUBTITLE__": esc(
            subtitle + " A comparison with today's market price is a comparison "
            "across that gap."),
        "__ASSUMPTIONS_HREF__": esc(assumptions_href),
        "__CSV_NAME__": esc(csv_name),
        "__WARNINGS__": _warnings(result),
        "__EV__": fmt(result["ev_ops"], "num"),
        "__EQUITY__": fmt(result["equity_value"], "num"),
        "__PER_SHARE__": fmt(result["value_per_share"], "share"),
        "__INPUTS__": _inputs_table(bundle),
        "__RATES__": _rates_block(bundle),
        "__SCHEDULE__": _schedule_table(result),
        "__BRIDGE__": _bridge_table(bundle, result),
        "__SENSITIVITY__": _sensitivity_table(bundle),
        "__WACC_NOTE__": esc(bundle["rates"].get("wacc_derivation")
                             or "No derivation was recorded for the discount rate."),
        "__LIVE__": LIVE_RELOAD if live else "",
    })
    return _write(page, out_path)


def build_pages(bundle, out_dir, slug=None, live=False, csv_name="assumptions.csv"):
    """Both pages, cross-linked. Returns ``(assumptions_path, valuation_path)``."""
    os.makedirs(out_dir, exist_ok=True)
    slug = slug or (bundle["meta"].get("ticker") or "company").lower()
    names = (f"{slug}-assumptions.html", f"{slug}-valuation.html")
    paths = [os.path.join(out_dir, n) for n in names]
    build_assumptions(bundle, paths[0], valuation_href=names[1], live=live)
    build_valuation(bundle, paths[1], assumptions_href=names[0],
                    csv_name=csv_name, live=live)
    return tuple(paths)


if __name__ == "__main__":
    import argparse
    import json

    from dcf_assumptions import apply_assumptions_csv

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle")
    ap.add_argument("out_dir")
    ap.add_argument("--csv", help="assumptions CSV to overlay onto the bundle")
    ap.add_argument("--slug", help="file-name stem; defaults to the ticker")
    ap.add_argument("--live", action="store_true",
                    help="inject the reload poller (watch loop only, never a "
                         "page you send someone)")
    args = ap.parse_args()

    with open(args.bundle, encoding="utf-8") as fh:
        bundle = json.load(fh)
    if args.csv:
        bundle = apply_assumptions_csv(bundle, args.csv)

    for path in build_pages(bundle, args.out_dir, slug=args.slug, live=args.live,
                            csv_name=os.path.basename(args.csv or "assumptions.csv")):
        print(path)
