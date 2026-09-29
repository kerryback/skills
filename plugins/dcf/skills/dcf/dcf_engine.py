"""Two-stage enterprise valuation: the reference implementation.

Five explicit forecast years on sales growth, EBITDA margin, a sales-to-net-PP&E
turnover, a depreciation rate, and a ratio of each retained operating asset and
liability to next-year sales; then the same ratios held constant forever.

Timing. Year 0 is the last actual fiscal year. Every balance-sheet quantity in
forecast year ``t`` is the balance at the *end* of year ``t``, stated against
year ``t+1`` sales -- the assets and liabilities that support next year's sales.
Net PP&E is entered as a turnover ``S(t+1) / NPPE(t)`` because that is how the
ratio is conventionally quoted; every other operating balance is entered as a
ratio to ``S(t+1)``.

    S(t)      = S(t-1) (1 + g(t))
    EBITDA(t) = m(t) S(t)
    NPPE(t)   = S(t+1) / k(t)
    D(t)      = d(t) NPPE(t-1)
    X(t)      = NPPE(t) - NPPE(t-1) + D(t)          capex, the plug
    NWC(t)    = (sum a_i(t) - sum l_j(t)) S(t+1)
    EBIT(t)   = EBITDA(t) - D(t)
    FCF(t)    = EBITDA(t) - Tax(t) - X(t) - (NWC(t) - NWC(t-1))

Capex is the plug rather than an assumption because in steady state it lands at
``(g + d)`` times prior net PP&E, which is positive for any sensible growth
rate. Making depreciation the plug instead lets it go negative.

Year 5's balance sheet is what supports year 6 sales, so unless year 5's ratios
already equal the terminal ratios, year 6 carries a one-time level adjustment
that must not be capitalised into a perpetuity. Year 6 therefore runs entirely
on terminal assumptions and absorbs the transition, and the perpetuity sits on
year 7, whose net PP&E and working capital are both set by terminal ratios
against year-7 sales:

    EV = sum over t = 1..6 of FCF(t) / (1+r)^t
         + [ FCF(7) / (r - g) ] / (1+r)^6

Set year 5's ratios equal to the terminal ratios and year 6 is already steady
state, collapsing this to the textbook formula.

Taxes are unlevered -- computed on EBIT, with the interest shield left in the
discount rate. A running NOL carryforward shelters the explicit years. The
perpetuity is taxed at the full rate with no carryforward usage, because a
carryforward burning off is not a steady state; anything still alive after year
6 is valued separately and added to the bridge.

Pure: no file I/O, no network, no printing, stdlib only.
"""

import copy

N_EXPLICIT = 5
TRANSITION_YEAR = 6
PERPETUITY_YEAR = 7
LAST_YEAR = 7

SCALAR_DRIVERS = (
    "sales_growth",
    "ebitda_margin",
    "sales_to_net_ppe",
    "depreciation_rate",
    "cash_tax_rate",
)

SCHEDULE_KEYS = (
    "year", "sales", "next_sales", "ebitda", "net_ppe", "depreciation",
    "capex", "nwc", "delta_nwc", "ebit", "nol_open", "nol_used", "nol_close",
    "taxable_income", "tax", "effective_tax_rate", "fcf", "discount_factor",
    "pv_fcf",
)


# --------------------------------------------------------------------------
# assumption lookup and validation
# --------------------------------------------------------------------------

def driver(spec, t):
    """The value of a driver in forecast year ``t``, 1-based.

    Years 6 and later take the terminal value, which is what makes year 6 the
    transition year and year 7 a clean steady state.
    """
    if t < 1:
        raise ValueError(f"forecast year must be >= 1, got {t}")
    if t <= N_EXPLICIT:
        return spec["explicit"][t - 1]
    return spec["terminal"]


def _check_spec(spec, name):
    if "explicit" not in spec or "terminal" not in spec:
        raise ValueError(f"{name}: needs both 'explicit' and 'terminal'")
    n = len(spec["explicit"])
    if n != N_EXPLICIT:
        raise ValueError(
            f"{name}: 'explicit' must hold exactly {N_EXPLICIT} values, got {n}")


def validate_bundle(bundle):
    """Raise ValueError on anything that would otherwise fail silently."""
    a = bundle["assumptions"]
    base = bundle["base"]

    for name in SCALAR_DRIVERS:
        if name not in a:
            raise ValueError(f"assumptions is missing '{name}'")
        _check_spec(a[name], name)

    for side in ("operating_assets", "operating_liabilities"):
        base_keys = set(base.get(side, {}))
        spec_keys = set(a.get(side, {}))
        if base_keys != spec_keys:
            raise ValueError(
                f"{side}: base names {sorted(base_keys)} but assumptions names "
                f"{sorted(spec_keys)}; they must name the same lines")
        for key, spec in a.get(side, {}).items():
            _check_spec(spec, f"{side}.{key}")

    overlap = set(base.get("operating_assets", {})) & \
        set(base.get("operating_liabilities", {}))
    if overlap:
        raise ValueError(
            f"these keys sit on both sides of working capital: {sorted(overlap)}")

    wacc = bundle["rates"]["wacc"]
    g = a["sales_growth"]["terminal"]
    if wacc <= g:
        raise ValueError(
            f"wacc ({wacc:.4f}) must exceed terminal growth ({g:.4f}); "
            f"the perpetuity does not exist")


# --------------------------------------------------------------------------
# the forecast schedule
# --------------------------------------------------------------------------

def sales_path(base_sales, growth, through):
    """Sales indexed by year, element 0 being the last actual year."""
    s = [base_sales]
    for t in range(1, through + 1):
        s.append(s[-1] * (1.0 + driver(growth, t)))
    return s


def _nwc(assets, liabilities, next_sales, t):
    a = sum(driver(spec, t) for spec in assets.values())
    l = sum(driver(spec, t) for spec in liabilities.values())
    return (a - l) * next_sales


def build_schedule(bundle):
    """Years 1 through 7, everything above the tax line."""
    validate_bundle(bundle)
    a, base = bundle["assumptions"], bundle["base"]

    # Year 7's net PP&E needs year 8 sales.
    s = sales_path(base["sales"], a["sales_growth"], through=LAST_YEAR + 1)

    nppe_prev = base["net_ppe"]
    nwc_prev = (sum(base.get("operating_assets", {}).values())
                - sum(base.get("operating_liabilities", {}).values()))

    rows = []
    for t in range(1, LAST_YEAR + 1):
        sales, next_sales = s[t], s[t + 1]
        nppe = next_sales / driver(a["sales_to_net_ppe"], t)
        dep = driver(a["depreciation_rate"], t) * nppe_prev
        capex = nppe - nppe_prev + dep
        nwc = _nwc(a["operating_assets"], a["operating_liabilities"], next_sales, t)
        ebitda = driver(a["ebitda_margin"], t) * sales
        rows.append({
            "year": t,
            "sales": sales,
            "next_sales": next_sales,
            "ebitda": ebitda,
            "net_ppe": nppe,
            "depreciation": dep,
            "capex": capex,
            "nwc": nwc,
            "delta_nwc": nwc - nwc_prev,
            "ebit": ebitda - dep,
        })
        nppe_prev, nwc_prev = nppe, nwc
    return rows


# --------------------------------------------------------------------------
# taxes
# --------------------------------------------------------------------------

def apply_taxes(rows, bundle):
    """Add the tax lines and free cash flow, in place, and return the rows.

    Years 1 through 6 draw on the carryforward. Year 7 does not: it stands for
    the perpetuity, and a perpetuity whose tax rate is still rising as a
    carryforward burns off is not a steady state. Whatever survives year 6 is
    valued in ``_nol_shield_pv`` and shown as its own line in the bridge.
    """
    a = bundle["assumptions"]
    limitation = bundle["rates"].get("nol_limitation", 0.80)
    nol = float(bundle["base"].get("nol") or 0.0)

    for row in rows:
        t, ebit = row["year"], row["ebit"]
        rate = driver(a["cash_tax_rate"], t)
        row["nol_open"] = nol

        if t >= PERPETUITY_YEAR:
            used, taxable, tax = 0.0, ebit, rate * ebit
        elif ebit <= 0.0:
            used, taxable, tax = 0.0, 0.0, 0.0
            nol -= ebit                      # a loss enlarges the carryforward
        else:
            used = min(limitation * ebit, nol)
            taxable = ebit - used
            tax = rate * taxable
            nol -= used

        row["nol_used"] = used
        row["nol_close"] = nol
        row["taxable_income"] = taxable
        row["tax"] = tax
        row["effective_tax_rate"] = tax / ebit if ebit else 0.0
        row["fcf"] = row["ebitda"] - tax - row["capex"] - row["delta_nwc"]
    return rows


def _nol_shield_pv(nol, ebit7, growth, rate, wacc, limitation, max_years=200):
    """PV as of year 0 of the shield on a carryforward alive after year 6.

    Returns ``(pv, unexhausted)``. EBIT grows at the terminal rate from year 7,
    so with a positive limitation the balance normally clears in a few years.
    """
    if nol <= 0.0:
        return 0.0, False
    if ebit7 <= 0.0:
        return 0.0, True
    pv, ebit, s = 0.0, ebit7, PERPETUITY_YEAR
    while nol > 0.0 and s < PERPETUITY_YEAR + max_years:
        used = min(limitation * ebit, nol)
        pv += rate * used / (1.0 + wacc) ** s
        nol -= used
        ebit *= 1.0 + growth
        s += 1
    return pv, nol > 0.0


# --------------------------------------------------------------------------
# valuation
# --------------------------------------------------------------------------

def _label(key):
    """Turn a bundle key into something a reader can put in a sentence."""
    text = str(key).replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else text


def _warnings(bundle, rows, perpetuity_row, nol_at_six, pv_nol, unexhausted):
    a, base = bundle["assumptions"], bundle["base"]
    out = []

    if nol_at_six > 0.0:
        out.append(
            f"A carryforward of {nol_at_six:,.1f} survives year 6. Its shield is "
            f"valued separately at {pv_nol:,.1f} and shown in the bridge, so the "
            f"perpetuity is taxed at the full rate.")
    if unexhausted:
        out.append(
            "The carryforward is not exhausted within 200 years of steady "
            "state; the shield above is a lower bound.")
    if perpetuity_row["ebit"] <= 0.0:
        out.append(
            "Terminal EBIT is not positive, so the perpetuity is negative. The "
            "model cannot value this company as a going concern on these "
            "assumptions.")
    negative_capex = [r["year"] for r in rows if r["capex"] < 0.0]
    if negative_capex:
        out.append(
            f"Implied capex is negative in year(s) {negative_capex}: the "
            f"sales-to-PP&E turnover is shrinking the asset base faster than it "
            f"depreciates.")
    if any(r["sales"] <= 0.0 for r in rows):
        out.append("Sales reach zero or below inside the forecast.")

    k5 = driver(a["sales_to_net_ppe"], N_EXPLICIT)
    kt = a["sales_to_net_ppe"]["terminal"]
    if kt and abs(k5 - kt) / abs(kt) > 0.10:
        out.append(
            f"Year 5's sales-to-PP&E turnover ({k5:.2f}) is more than 10 percent "
            f"from terminal ({kt:.2f}), so year 6 absorbs the whole adjustment.")

    units = str(bundle["meta"].get("units", "")).lower()
    if "million" in units and base["sales"] > 1e7:
        out.append(
            f"meta.units says millions but base sales is {base['sales']:,.0f}. "
            f"If the statements are in dollars and the share count is in "
            f"millions, value per share is wrong by a factor of a million.")
    return out


def run_model(bundle):
    """Value the company. Returns the schedule, the bridge, and any warnings."""
    rows = apply_taxes(build_schedule(bundle), bundle)
    a, base = bundle["assumptions"], bundle["base"]
    wacc = bundle["rates"]["wacc"]
    g = a["sales_growth"]["terminal"]
    limitation = bundle["rates"].get("nol_limitation", 0.80)

    for row in rows:
        row["discount_factor"] = 1.0 / (1.0 + wacc) ** row["year"]
        row["pv_fcf"] = row["fcf"] * row["discount_factor"]

    perpetuity_row = rows[PERPETUITY_YEAR - 1]
    pv_explicit = sum(r["pv_fcf"] for r in rows[:TRANSITION_YEAR])
    terminal_value = perpetuity_row["fcf"] / (wacc - g)
    pv_terminal = terminal_value / (1.0 + wacc) ** TRANSITION_YEAR
    ev_ops = pv_explicit + pv_terminal

    nol_at_six = rows[TRANSITION_YEAR - 1]["nol_close"]
    pv_nol, unexhausted = _nol_shield_pv(
        nol_at_six, perpetuity_row["ebit"], g,
        driver(a["cash_tax_rate"], PERPETUITY_YEAR), wacc, limitation)

    bridge = [{"label": "Enterprise value of operations", "amount": ev_ops}]
    if pv_nol:
        bridge.append({"label": "PV of remaining NOL carryforward", "amount": pv_nol})
    for k, v in base.get("nonoperating_assets", {}).items():
        bridge.append({"label": f"Plus {_label(k).lower()}", "amount": float(v)})
    for k, v in base.get("debt_claims", {}).items():
        bridge.append({"label": f"Less {_label(k).lower()}", "amount": -float(v)})
    for k, v in base.get("equity_claims", {}).items():
        bridge.append({"label": f"Less {_label(k).lower()}", "amount": -float(v)})

    equity_value = sum(item["amount"] for item in bridge)
    shares = bundle["meta"].get("diluted_shares") or 0.0

    return {
        "schedule": rows,
        "ev_ops": ev_ops,
        "pv_explicit": pv_explicit,
        "pv_terminal": pv_terminal,
        "terminal_value": terminal_value,
        "pv_nol": pv_nol,
        "bridge": bridge,
        "equity_value": equity_value,
        "value_per_share": equity_value / shares if shares else None,
        "warnings": _warnings(bundle, rows, perpetuity_row, nol_at_six,
                              pv_nol, unexhausted),
    }


def sensitivity_grid(bundle, waccs, growths, key="value_per_share"):
    """``key`` at each (WACC, terminal growth) pair, as rows by column.

    Lives here rather than in the artifacts so that every number they show
    comes out of this module. A pair with no perpetuity -- growth at or above
    the discount rate -- yields None rather than raising, because a grid is
    expected to run off the edge of what can be valued.
    """
    rows = []
    for wacc in waccs:
        row = []
        for growth in growths:
            trial = copy.deepcopy(bundle)
            trial["rates"]["wacc"] = wacc
            trial["assumptions"]["sales_growth"]["terminal"] = growth
            try:
                row.append(run_model(trial)[key])
            except ValueError:
                row.append(None)
        rows.append(row)
    return rows


def sensitivity_axes(bundle, wacc_steps=(-0.02, -0.01, 0.0, 0.01, 0.02),
                     growth_steps=(-0.01, -0.005, 0.0, 0.005, 0.01)):
    """The default axes: the base case, bracketed."""
    wacc = bundle["rates"]["wacc"]
    growth = bundle["assumptions"]["sales_growth"]["terminal"]
    return ([wacc + d for d in wacc_steps],
            [growth + d for d in growth_steps])
