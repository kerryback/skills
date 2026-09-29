# DCF Two-Stage Valuation Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Claude Code plugin whose skill turns a staged folder of financial statements and company text into a discussed set of forecast assumptions, a self-contained interactive HTML valuation app, and an Excel workbook with live formulas.

**Architecture:** One Python engine is the reference implementation of the two-stage recursion. Claude never writes valuation arithmetic — it writes a JSON input bundle that the engine consumes. Two ports (a JavaScript engine inside the HTML app, and Excel formulas in the workbook) each embed the Python engine's base-case schedule and check themselves against it when the artifact is opened, so a port that drifts announces itself.

**Tech Stack:** Python 3.11+, stdlib only for the engine; `openpyxl` for the workbook; `pandas` for statement loading; vanilla JavaScript with no dependencies in the app; `pytest` for tests.

**Spec:** `docs/superpowers/specs/2026-09-28-dcf-two-stage-valuation-design.md`

## Global Constraints

- Plugin lives at `plugins/dcf/`, skill at `plugins/dcf/skills/dcf/`, matching the `wrds` plugin's shape.
- The engine (`dcf_engine.py`) is pure: no file I/O, no network, no printing. Stdlib only.
- The skill does no network work anywhere. Statements and text are staged by the user.
- Five explicit forecast years. `N_EXPLICIT = 5`, `TRANSITION_YEAR = 6`, `PERPETUITY_YEAR = 7`.
- Every balance-sheet ratio in forecast column `t` is stated against year `t+1` sales.
- Net PP&E is entered as a turnover `S_{t+1} / NPPE_t`; every other operating balance as a ratio to `S_{t+1}`.
- Depreciation is `d(t) * NPPE_{t-1}`. Capex is the plug.
- Taxes are unlevered — on EBIT, not on pretax income. Default NOL limitation `L = 0.80`.
- `wacc <= terminal growth` raises `ValueError`. Every other anomaly is a warning string in the result.
- Parity tolerance between ports: relative 1e-9.
- The HTML app has zero network dependencies — no CDN, no webfont, no fetch.

## Review Focus

1. `explicit` arrays that are not exactly 5 long — must raise with the driver's name, not silently index past the end or pad. Covered in Task 2.
2. `base.nol` of zero, or absent — shield PV must be exactly 0.0 with no "NOL alive" warning. Covered in Task 4.
3. An empty `operating_liabilities` dict (a company with none retained) — NWC must still compute rather than raising on `max()`/`sum()` of empty. Covered in Task 2.
4. A classification table whose bucket totals do not foot to the reported balance-sheet totals — must error and name the difference, never proceed with a silently dropped line. Covered in Task 6.
5. Statements in raw dollars combined with a share count in millions — per-share value is off by 1e6 and looks plausible. `meta.units` must be checked against the magnitude of `base.sales` and warn. Covered in Task 4.

---

## File Structure

| File | Responsibility |
|---|---|
| `plugins/dcf/.claude-plugin/plugin.json` | plugin manifest |
| `plugins/dcf/README.md` | what it is, how to install |
| `plugins/dcf/skills/dcf/SKILL.md` | the five phases, the three gates |
| `plugins/dcf/skills/dcf/dcf_engine.py` | the reference recursion; pure |
| `plugins/dcf/skills/dcf/dcf_load.py` | staged statements → `financials.json` |
| `plugins/dcf/skills/dcf/dcf_history.py` | financials + classification → historical ratios |
| `plugins/dcf/skills/dcf/build_app.py` | bundle + template → `<slug>-dcf.html` |
| `plugins/dcf/skills/dcf/build_workbook.py` | bundle → `<slug>-dcf.xlsx` |
| `plugins/dcf/skills/dcf/app_template.html` | app shell and the JS port |
| `plugins/dcf/skills/dcf/reference/model.md` | the arithmetic, written out |
| `plugins/dcf/skills/dcf/reference/classification.md` | buckets and the hard cases |
| `plugins/dcf/skills/dcf/reference/staging.md` | expected folder layout |
| `plugins/dcf/skills/dcf/reference/reading-text.md` | what to look for per driver |
| `plugins/dcf/skills/dcf/tests/` | pytest suite |

---

### Task 1: Plugin scaffold

**Files:**
- Create: `plugins/dcf/.claude-plugin/plugin.json`
- Create: `plugins/dcf/README.md`
- Create: `plugins/dcf/skills/dcf/tests/__init__.py` (empty)
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: nothing
- Produces: the directory layout every later task writes into

- [ ] **Step 1: Create the manifest**

```json
{
  "name": "dcf",
  "version": "0.1.0",
  "description": "Two-stage enterprise valuation from staged financial statements and company text: forecast sales growth, EBITDA margin, a sales-to-net-PP&E turnover, a depreciation rate, and ratios of each operating asset and liability to next-year sales for five explicit years and then constant forever, with capex as the plug and a running NOL carryforward. Classifies every reported balance-sheet line before forecasting, proposes assumptions grounded in history and in the 10-K and transcripts, and emits an interactive one-page HTML app and an Excel workbook with live formulas that both check themselves against the Python engine.",
  "author": { "name": "Kerry Back" },
  "license": "MIT",
  "keywords": ["dcf", "valuation", "enterprise-value", "corporate-finance", "financial-modeling"]
}
```

- [ ] **Step 2: Register in the marketplace**

Append a fourth entry to the `plugins` array of `.claude-plugin/marketplace.json` with `"name": "dcf"`, `"source": "./plugins/dcf"`, and a one-sentence description. Update the marketplace `description` to mention valuation.

- [ ] **Step 3: Commit**

```bash
git add plugins/dcf .claude-plugin/marketplace.json
git commit -m "Scaffold the dcf plugin"
```

---

### Task 2: The forecast schedule

**Files:**
- Create: `plugins/dcf/skills/dcf/dcf_engine.py`
- Test: `plugins/dcf/skills/dcf/tests/test_schedule.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `N_EXPLICIT = 5`, `TRANSITION_YEAR = 6`, `PERPETUITY_YEAR = 7`, `LAST_YEAR = 7`
  - `driver(spec: dict, t: int) -> float`
  - `sales_path(base_sales: float, growth: dict, through: int) -> list[float]` — index `t` is year `t`
  - `build_schedule(bundle: dict) -> list[dict]` — one row per year 1..7, before taxes; keys `year, sales, next_sales, ebitda, net_ppe, depreciation, capex, nwc, delta_nwc, ebit`
  - `validate_bundle(bundle: dict) -> None` — raises `ValueError`

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from dcf_engine import driver, sales_path, build_schedule, validate_bundle, N_EXPLICIT


def const(v):
    return {"explicit": [v] * N_EXPLICIT, "terminal": v}


def bundle(**over):
    b = {
        "meta": {"company": "Test", "fiscal_year_0": 2025,
                 "units": "USD millions", "diluted_shares": 100.0},
        "base": {"sales": 1000.0, "net_ppe": 500.0,
                 "operating_assets": {"receivables": 200.0},
                 "operating_liabilities": {"payables": 100.0},
                 "nonoperating_assets": {}, "debt_claims": {}, "equity_claims": {},
                 "nol": 0.0},
        "assumptions": {
            "sales_growth": const(0.05), "ebitda_margin": const(0.20),
            "sales_to_net_ppe": const(2.0), "depreciation_rate": const(0.10),
            "cash_tax_rate": const(0.25),
            "operating_assets": {"receivables": const(0.20)},
            "operating_liabilities": {"payables": const(0.10)},
        },
        "rates": {"wacc": 0.10, "nol_limitation": 0.80},
    }
    for k, v in over.items():
        b[k] = v
    return b


def test_driver_uses_explicit_then_terminal():
    spec = {"explicit": [1, 2, 3, 4, 5], "terminal": 9}
    assert [driver(spec, t) for t in range(1, 9)] == [1, 2, 3, 4, 5, 9, 9, 9]


def test_sales_compound_from_year_zero():
    s = sales_path(1000.0, const(0.10), through=3)
    assert s[0] == pytest.approx(1000.0)
    assert s[3] == pytest.approx(1331.0)


def test_net_ppe_is_next_year_sales_over_turnover():
    rows = build_schedule(bundle())
    r1 = rows[0]
    assert r1["net_ppe"] == pytest.approx(r1["next_sales"] / 2.0)


def test_depreciation_is_rate_times_prior_net_ppe():
    rows = build_schedule(bundle())
    assert rows[0]["depreciation"] == pytest.approx(0.10 * 500.0)
    assert rows[1]["depreciation"] == pytest.approx(0.10 * rows[0]["net_ppe"])


def test_capex_is_the_plug():
    rows = build_schedule(bundle())
    assert rows[0]["capex"] == pytest.approx(
        rows[0]["net_ppe"] - 500.0 + rows[0]["depreciation"])


def test_steady_state_capex_is_growth_plus_depreciation_rate():
    rows = build_schedule(bundle())
    r7, r6 = rows[6], rows[5]
    assert r7["capex"] == pytest.approx((0.05 + 0.10) * r6["net_ppe"])


def test_schedule_runs_to_year_seven():
    assert [r["year"] for r in build_schedule(bundle())] == [1, 2, 3, 4, 5, 6, 7]


def test_empty_operating_liabilities_is_fine():
    b = bundle()
    b["base"]["operating_liabilities"] = {}
    b["assumptions"]["operating_liabilities"] = {}
    rows = build_schedule(b)
    assert rows[0]["nwc"] == pytest.approx(0.20 * rows[0]["next_sales"])


def test_wrong_length_explicit_array_raises_with_driver_name():
    b = bundle()
    b["assumptions"]["ebitda_margin"]["explicit"] = [0.2, 0.2]
    with pytest.raises(ValueError, match="ebitda_margin"):
        validate_bundle(b)
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_schedule.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'dcf_engine'`

- [ ] **Step 3: Implement**

`dcf_engine.py`, module docstring then:

```python
N_EXPLICIT = 5
TRANSITION_YEAR = 6
PERPETUITY_YEAR = 7
LAST_YEAR = 7

SCALAR_DRIVERS = ("sales_growth", "ebitda_margin", "sales_to_net_ppe",
                  "depreciation_rate", "cash_tax_rate")


def driver(spec, t):
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
        raise ValueError(f"{name}: 'explicit' must hold exactly {N_EXPLICIT} "
                         f"values, got {n}")


def validate_bundle(bundle):
    a = bundle["assumptions"]
    for name in SCALAR_DRIVERS:
        if name not in a:
            raise ValueError(f"assumptions is missing '{name}'")
        _check_spec(a[name], name)
    for side in ("operating_assets", "operating_liabilities"):
        base_keys = set(bundle["base"][side])
        spec_keys = set(a.get(side, {}))
        if base_keys != spec_keys:
            raise ValueError(
                f"{side}: base has {sorted(base_keys)} but assumptions has "
                f"{sorted(spec_keys)}; they must name the same lines")
        for key, spec in a.get(side, {}).items():
            _check_spec(spec, f"{side}.{key}")
    overlap = set(bundle["base"]["operating_assets"]) & \
        set(bundle["base"]["operating_liabilities"])
    if overlap:
        raise ValueError(f"keys used on both sides of NWC: {sorted(overlap)}")
    if bundle["rates"]["wacc"] <= a["sales_growth"]["terminal"]:
        raise ValueError(
            f"wacc ({bundle['rates']['wacc']:.4f}) must exceed terminal growth "
            f"({a['sales_growth']['terminal']:.4f}); the perpetuity does not exist")


def sales_path(base_sales, growth, through):
    s = [base_sales]
    for t in range(1, through + 1):
        s.append(s[-1] * (1.0 + driver(growth, t)))
    return s


def _nwc(assets, liabilities, next_sales, t):
    a = sum(driver(spec, t) for spec in assets.values()) * next_sales
    l = sum(driver(spec, t) for spec in liabilities.values()) * next_sales
    return a - l


def build_schedule(bundle):
    validate_bundle(bundle)
    a, base = bundle["assumptions"], bundle["base"]
    s = sales_path(base["sales"], a["sales_growth"], through=LAST_YEAR + 1)

    nppe_prev = base["net_ppe"]
    nwc_prev = (sum(base["operating_assets"].values())
                - sum(base["operating_liabilities"].values()))

    rows = []
    for t in range(1, LAST_YEAR + 1):
        sales, next_sales = s[t], s[t + 1]
        nppe = next_sales / driver(a["sales_to_net_ppe"], t)
        dep = driver(a["depreciation_rate"], t) * nppe_prev
        capex = nppe - nppe_prev + dep
        nwc = _nwc(a["operating_assets"], a["operating_liabilities"], next_sales, t)
        ebitda = driver(a["ebitda_margin"], t) * sales
        rows.append({
            "year": t, "sales": sales, "next_sales": next_sales,
            "ebitda": ebitda, "net_ppe": nppe, "depreciation": dep,
            "capex": capex, "nwc": nwc, "delta_nwc": nwc - nwc_prev,
            "ebit": ebitda - dep,
        })
        nppe_prev, nwc_prev = nppe, nwc
    return rows
```

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_schedule.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/dcf_engine.py plugins/dcf/skills/dcf/tests/test_schedule.py
git commit -m "Build the two-stage forecast schedule, with capex as the plug"
```

---

### Task 3: Taxes and the NOL carryforward

**Files:**
- Modify: `plugins/dcf/skills/dcf/dcf_engine.py`
- Test: `plugins/dcf/skills/dcf/tests/test_nol.py`

**Interfaces:**
- Consumes: `build_schedule` from Task 2
- Produces: `apply_taxes(rows: list[dict], bundle: dict) -> list[dict]` — adds `nol_open, nol_used, nol_close, taxable_income, tax, effective_tax_rate, fcf` to each row. Years 1..6 use the carryforward; year 7 is taxed at the full terminal rate with no NOL usage.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from dcf_engine import build_schedule, apply_taxes, N_EXPLICIT
from test_schedule import bundle, const


def taxed(b):
    return apply_taxes(build_schedule(b), b)


def test_no_tax_in_a_loss_year_and_the_loss_is_banked():
    b = bundle()
    b["assumptions"]["ebitda_margin"] = const(0.01)   # EBITDA below depreciation
    rows = taxed(b)
    assert rows[0]["ebit"] < 0
    assert rows[0]["tax"] == 0.0
    assert rows[0]["nol_close"] == pytest.approx(-rows[0]["ebit"])


def test_carryforward_shelters_eighty_percent_of_later_income():
    b = bundle()
    b["base"]["nol"] = 1_000_000.0          # far more than can be used
    rows = taxed(b)
    r = rows[0]
    assert r["nol_used"] == pytest.approx(0.80 * r["ebit"])
    assert r["tax"] == pytest.approx(0.25 * 0.20 * r["ebit"])


def test_carryforward_is_exhausted_not_overdrawn():
    b = bundle()
    b["base"]["nol"] = 1.0
    rows = taxed(b)
    assert rows[0]["nol_used"] == pytest.approx(1.0)
    assert rows[0]["nol_close"] == 0.0


def test_hand_worked_two_loss_years_then_profit():
    # EBIT = -100, -50, +500 with L = 0.8 and tau = 0.25
    # year 3 usable = min(0.8*500, 150) = 150 -> taxable 350 -> tax 87.5
    b = bundle()
    b["assumptions"]["sales_growth"] = {"explicit": [0, 0, 0, 0, 0], "terminal": 0}
    b["assumptions"]["depreciation_rate"] = {"explicit": [0] * 5, "terminal": 0}
    b["assumptions"]["ebitda_margin"] = {"explicit": [-0.10, -0.05, 0.50, 0.50, 0.50],
                                         "terminal": 0.50}
    rows = taxed(b)
    assert [round(r["ebit"], 6) for r in rows[:3]] == [-100.0, -50.0, 500.0]
    assert rows[2]["nol_used"] == pytest.approx(150.0)
    assert rows[2]["tax"] == pytest.approx(87.5)
    assert rows[2]["nol_close"] == 0.0


def test_year_seven_ignores_the_carryforward():
    b = bundle()
    b["base"]["nol"] = 1_000_000.0
    rows = taxed(b)
    r7 = rows[6]
    assert r7["nol_used"] == 0.0
    assert r7["tax"] == pytest.approx(0.25 * r7["ebit"])


def test_free_cash_flow_identity():
    rows = taxed(bundle())
    for r in rows:
        assert r["fcf"] == pytest.approx(
            r["ebitda"] - r["tax"] - r["capex"] - r["delta_nwc"])


def test_no_depreciation_no_growth_gives_ebitda_after_tax():
    b = bundle()
    b["assumptions"]["sales_growth"] = {"explicit": [0] * 5, "terminal": 0}
    b["assumptions"]["depreciation_rate"] = {"explicit": [0] * 5, "terminal": 0}
    rows = taxed(b)
    r = rows[3]
    assert r["capex"] == pytest.approx(0.0)
    assert r["delta_nwc"] == pytest.approx(0.0)
    assert r["fcf"] == pytest.approx(r["ebitda"] * (1 - 0.25))
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_nol.py -v`
Expected: FAIL, `ImportError: cannot import name 'apply_taxes'`

- [ ] **Step 3: Implement**

Append to `dcf_engine.py`:

```python
def apply_taxes(rows, bundle):
    a = bundle["assumptions"]
    limitation = bundle["rates"].get("nol_limitation", 0.80)
    nol = float(bundle["base"].get("nol") or 0.0)

    for row in rows:
        t, ebit = row["year"], row["ebit"]
        rate = driver(a["cash_tax_rate"], t)
        row["nol_open"] = nol

        if t >= PERPETUITY_YEAR:
            # The perpetuity is taxed at the full rate; any carryforward still
            # alive is valued separately so the steady state stays steady.
            used = 0.0
            taxable = ebit
            tax = rate * ebit
        elif ebit <= 0.0:
            used = 0.0
            taxable = 0.0
            tax = 0.0
            nol -= ebit
        else:
            used = min(limitation * ebit, nol)
            taxable = ebit - used
            tax = rate * taxable
            nol -= used

        row["nol_used"] = used
        row["nol_close"] = nol if t < PERPETUITY_YEAR else nol
        row["taxable_income"] = taxable
        row["tax"] = tax
        row["effective_tax_rate"] = tax / ebit if ebit else 0.0
        row["fcf"] = row["ebitda"] - tax - row["capex"] - row["delta_nwc"]
    return rows
```

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`
Expected: 16 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/dcf_engine.py plugins/dcf/skills/dcf/tests/test_nol.py
git commit -m "Shelter the explicit years with a running NOL carryforward"
```

---

### Task 4: Terminal value, the NOL shield, and the bridge

**Files:**
- Modify: `plugins/dcf/skills/dcf/dcf_engine.py`
- Test: `plugins/dcf/skills/dcf/tests/test_engine.py`

**Interfaces:**
- Consumes: `build_schedule`, `apply_taxes`
- Produces: `run_model(bundle: dict) -> dict` with keys `schedule, ev_ops, pv_explicit, pv_terminal, terminal_value, pv_nol, bridge, equity_value, value_per_share, warnings`. `bridge` is a list of `{"label": str, "amount": float}`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from dcf_engine import run_model, N_EXPLICIT
from test_schedule import bundle, const


def test_all_years_at_terminal_matches_closed_form_gordon():
    b = bundle()
    r = run_model(b)
    g, wacc = 0.05, 0.10
    # Independent closed form: every year is steady state, so FCF_t = FCF_1(1+g)^(t-1)
    fcf1 = r["schedule"][0]["fcf"]
    expected = fcf1 / (wacc - g)
    assert r["ev_ops"] == pytest.approx(expected, rel=1e-9)


def test_perpetuity_year_is_genuinely_steady_state():
    b = bundle()
    b["assumptions"]["sales_to_net_ppe"]["explicit"] = [3.0, 2.8, 2.6, 2.4, 2.2]
    rows = run_model(b)["schedule"]
    # year 6 absorbs the transition; 7 onward grows at g
    assert rows[6]["net_ppe"] == pytest.approx(rows[5]["net_ppe"] * 1.05)


def test_wacc_below_terminal_growth_raises():
    b = bundle()
    b["rates"]["wacc"] = 0.04
    with pytest.raises(ValueError, match="perpetuity does not exist"):
        run_model(b)


def test_no_nol_gives_zero_shield_and_no_warning():
    r = run_model(bundle())
    assert r["pv_nol"] == 0.0
    assert not any("carryforward" in w for w in r["warnings"])


def test_surviving_nol_is_valued_and_flagged():
    b = bundle()
    b["base"]["nol"] = 1_000_000.0
    r = run_model(b)
    assert r["pv_nol"] > 0.0
    assert any("carryforward" in w for w in r["warnings"])


def test_nol_shield_closed_form_when_limitation_does_not_bind():
    # NOL small enough to be fully used in year 7: PV = tau * NOL / (1+r)^7
    b = bundle()
    b["base"]["nol"] = 0.0
    r0 = run_model(b)
    ebit7 = r0["schedule"][6]["ebit"]
    small = 0.5 * 0.80 * ebit7
    b["base"]["nol"] = small
    # The explicit years consume it first, so force losses out of the way by
    # making years 1-6 exactly break even on EBIT.
    b["assumptions"]["ebitda_margin"]["explicit"] = [
        run_model(b)["schedule"][i]["depreciation"]
        / run_model(b)["schedule"][i]["sales"] for i in range(N_EXPLICIT)]
    r = run_model(b)
    assert r["pv_nol"] > 0.0


def test_bridge_nets_claims_against_enterprise_value():
    b = bundle()
    b["base"]["nonoperating_assets"] = {"cash": 50.0}
    b["base"]["debt_claims"] = {"long_term_debt": 400.0}
    b["base"]["equity_claims"] = {"noncontrolling_interests": 30.0}
    r = run_model(b)
    assert r["equity_value"] == pytest.approx(
        r["ev_ops"] + r["pv_nol"] + 50.0 - 400.0 - 30.0)
    assert r["value_per_share"] == pytest.approx(r["equity_value"] / 100.0)


def test_negative_capex_warns():
    b = bundle()
    b["assumptions"]["sales_to_net_ppe"]["explicit"] = [20.0] * N_EXPLICIT
    r = run_model(b)
    assert any("capex" in w for w in r["warnings"])


def test_unit_mismatch_warns():
    b = bundle()
    b["base"]["sales"] = 1_941_800_000.0
    r = run_model(b)
    assert any("units" in w.lower() for w in r["warnings"])
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_engine.py -v`
Expected: FAIL, `ImportError: cannot import name 'run_model'`

- [ ] **Step 3: Implement**

Append to `dcf_engine.py`:

```python
def _nol_shield_pv(nol, ebit7, growth, rate, wacc, limitation, max_years=200):
    """PV, as of year 0, of the tax shield on a carryforward still alive after
    year 6. Year 7 onward is taxed at the full rate in the perpetuity, so the
    shield is valued here instead and added to the bridge."""
    if nol <= 0.0 or ebit7 <= 0.0:
        return 0.0, nol > 0.0 and ebit7 <= 0.0
    pv, ebit, s = 0.0, ebit7, PERPETUITY_YEAR
    while nol > 0.0 and s < PERPETUITY_YEAR + max_years:
        used = min(limitation * ebit, nol)
        pv += rate * used / (1.0 + wacc) ** s
        nol -= used
        ebit *= 1.0 + growth
        s += 1
    return pv, nol > 0.0


def run_model(bundle):
    rows = apply_taxes(build_schedule(bundle), bundle)
    a, base = bundle["assumptions"], bundle["base"]
    wacc = bundle["rates"]["wacc"]
    g = a["sales_growth"]["terminal"]
    limitation = bundle["rates"].get("nol_limitation", 0.80)
    warnings = []

    for row in rows:
        row["discount_factor"] = 1.0 / (1.0 + wacc) ** row["year"]
        row["pv_fcf"] = row["fcf"] * row["discount_factor"]

    explicit = rows[:TRANSITION_YEAR]           # years 1..6
    perpetuity_row = rows[PERPETUITY_YEAR - 1]  # year 7

    pv_explicit = sum(r["pv_fcf"] for r in explicit)
    terminal_value = perpetuity_row["fcf"] / (wacc - g)
    pv_terminal = terminal_value / (1.0 + wacc) ** TRANSITION_YEAR
    ev_ops = pv_explicit + pv_terminal

    nol_at_six = rows[TRANSITION_YEAR - 1]["nol_close"]
    pv_nol, unexhausted = _nol_shield_pv(
        nol_at_six, perpetuity_row["ebit"], g,
        driver(a["cash_tax_rate"], PERPETUITY_YEAR), wacc, limitation)

    if nol_at_six > 0.0:
        warnings.append(
            f"A carryforward of {nol_at_six:,.1f} survives year 6. Its shield is "
            f"valued separately at {pv_nol:,.1f} and shown in the bridge, so the "
            f"perpetuity is taxed at the full rate.")
    if unexhausted:
        warnings.append(
            "The carryforward is not exhausted within 200 years of steady state; "
            "the shield above is a lower bound.")
    if perpetuity_row["ebit"] <= 0.0:
        warnings.append(
            "Terminal EBIT is not positive, so the perpetuity is negative. The "
            "model cannot value this company as a going concern on these "
            "assumptions.")
    if any(r["capex"] < 0.0 for r in rows):
        years = [r["year"] for r in rows if r["capex"] < 0.0]
        warnings.append(
            f"Implied capex is negative in year(s) {years}: the sales-to-PP&E "
            f"turnover is shrinking the asset base faster than it depreciates.")
    if any(r["sales"] <= 0.0 for r in rows):
        warnings.append("Sales go to zero or below inside the forecast.")

    k5 = driver(a["sales_to_net_ppe"], N_EXPLICIT)
    kt = a["sales_to_net_ppe"]["terminal"]
    if kt and abs(k5 - kt) / abs(kt) > 0.10:
        warnings.append(
            f"Year 5's sales-to-PP&E turnover ({k5:.2f}) is more than 10 percent "
            f"from terminal ({kt:.2f}); year 6 absorbs the whole adjustment.")

    units = str(bundle["meta"].get("units", "")).lower()
    if "million" in units and base["sales"] > 1e7:
        warnings.append(
            f"meta.units says millions but base sales is {base['sales']:,.0f}. "
            f"If the statements are in dollars and the share count is in "
            f"millions, value per share is wrong by a factor of a million.")

    bridge = [{"label": "Enterprise value of operations", "amount": ev_ops}]
    if pv_nol:
        bridge.append({"label": "PV of remaining NOL carryforward", "amount": pv_nol})
    for k, v in base.get("nonoperating_assets", {}).items():
        bridge.append({"label": f"Plus {k}", "amount": v})
    for k, v in base.get("debt_claims", {}).items():
        bridge.append({"label": f"Less {k}", "amount": -v})
    for k, v in base.get("equity_claims", {}).items():
        bridge.append({"label": f"Less {k}", "amount": -v})

    equity_value = sum(item["amount"] for item in bridge)
    shares = bundle["meta"].get("diluted_shares") or 0.0

    return {
        "schedule": rows, "ev_ops": ev_ops,
        "pv_explicit": pv_explicit, "pv_terminal": pv_terminal,
        "terminal_value": terminal_value, "pv_nol": pv_nol,
        "bridge": bridge, "equity_value": equity_value,
        "value_per_share": equity_value / shares if shares else None,
        "warnings": warnings,
    }
```

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/dcf_engine.py plugins/dcf/skills/dcf/tests/test_engine.py
git commit -m "Value the perpetuity on year 7 and the surviving NOL in the bridge"
```

---

### Task 5: Loading staged statements

**Files:**
- Create: `plugins/dcf/skills/dcf/dcf_load.py`
- Test: `plugins/dcf/skills/dcf/tests/test_load.py`

**Interfaces:**
- Consumes: nothing
- Produces: `load_statements(path: str) -> dict` returning `{"years": [...], "income": {line: {year: value}}, "balance": {...}, "cashflow": {...}, "source": str}`. Handles a CSV or xlsx whose first column holds line items and whose remaining columns are fiscal years, with metadata rows above a header row, in either chronological direction. Years are normalized to `int`.

- [ ] **Step 1: Write the failing tests**

Fixtures written inline to a `tmp_path`: one CSV shaped like `data/acdc_balance_annual.csv` (blank first header cell, ISO dates newest first) and one xlsx with five metadata rows above a `Line item` header row.

```python
import pytest
from dcf_load import load_statements


def test_csv_with_iso_date_columns_newest_first(tmp_path):
    p = tmp_path / "balance.csv"
    p.write_text(",2025-12-31,2024-12-31\nCash,22.9,14.8\nInventories,150.0,160.0\n")
    out = load_statements(str(p))
    assert out["years"] == [2024, 2025]
    assert out["lines"]["Cash"][2025] == pytest.approx(22.9)


def test_header_row_is_found_below_metadata(tmp_path):
    p = tmp_path / "bs.csv"
    p.write_text("Some Company - Balance Sheets\nnotes\n\n"
                 "Line item,FY2024,FY2025\nCash,14.8,22.9\n")
    out = load_statements(str(p))
    assert out["years"] == [2024, 2025]
    assert out["lines"]["Cash"][2024] == pytest.approx(14.8)


def test_blank_and_section_header_rows_are_dropped(tmp_path):
    p = tmp_path / "bs.csv"
    p.write_text("Line item,FY2025\nCurrent assets:,\nCash,22.9\n,\n")
    out = load_statements(str(p))
    assert "Current assets:" not in out["lines"]
    assert list(out["lines"]) == ["Cash"]


def test_unparseable_file_names_what_it_wanted(tmp_path):
    p = tmp_path / "junk.csv"
    p.write_text("no,columns,here\n")
    with pytest.raises(ValueError, match="fiscal year"):
        load_statements(str(p))
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_load.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'dcf_load'`

- [ ] **Step 3: Implement**

`dcf_load.py` reads with `pandas.read_csv(header=None)` or `pandas.read_excel(header=None)`, scans rows top-down for the first row where at least two cells parse as a fiscal year (a four-digit year inside the string, whether `2025-12-31`, `FY2025`, or `2025`), treats that as the header, takes column 0 of every row below as the line label, drops rows whose label is blank or whose every value is blank, coerces values with `pandas.to_numeric(errors="coerce")`, and sorts years ascending. Raises `ValueError("no row looks like a fiscal year header; ...")` naming the expected shape when no header row is found.

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_load.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/dcf_load.py plugins/dcf/skills/dcf/tests/test_load.py
git commit -m "Load staged statements in either of the two shapes we see"
```

---

### Task 6: Historical ratios and the footing check

**Files:**
- Create: `plugins/dcf/skills/dcf/dcf_history.py`
- Test: `plugins/dcf/skills/dcf/tests/test_history.py`

**Interfaces:**
- Consumes: `load_statements` from Task 5
- Produces:
  - `check_footing(classification, balance_lines, totals, tol=0.01) -> None` — raises `ValueError` naming the difference
  - `historical_ratios(financials, classification, sales_line) -> dict` with keys `years` and `ratios`, the latter holding `sales_growth, ebitda_margin, sales_to_net_ppe, depreciation_rate, cash_tax_rate, operating_assets, operating_liabilities`, each a `{year: value}` map, plus `realized_capex` and `implied_depreciation_rate` as the cross-check.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from dcf_history import check_footing, historical_ratios


def test_unfooted_classification_names_the_difference():
    classification = [{"line": "Cash", "bucket": "nonoperating_asset"}]
    with pytest.raises(ValueError, match="150"):
        check_footing(classification, {"Cash": 100.0, "Inventories": 150.0},
                      {"total_assets": 250.0})


def test_footed_classification_passes():
    classification = [{"line": "Cash", "bucket": "nonoperating_asset"},
                      {"line": "Inventories", "bucket": "operating_asset"}]
    check_footing(classification, {"Cash": 100.0, "Inventories": 150.0},
                  {"total_assets": 250.0})


def test_ratios_are_stated_against_next_year_sales():
    fin = {"years": [2024, 2025],
           "lines": {"Revenues": {2024: 1000.0, 2025: 1200.0},
                     "Receivables": {2024: 200.0, 2025: 240.0}}}
    classification = [{"line": "Receivables", "bucket": "operating_asset",
                       "key": "receivables"}]
    out = historical_ratios(fin, classification, sales_line="Revenues")
    # 2024's receivables support 2025 sales
    assert out["ratios"]["operating_assets"]["receivables"][2024] == \
        pytest.approx(200.0 / 1200.0)
    # the last year has no next-year sales, so no ratio
    assert 2025 not in out["ratios"]["operating_assets"]["receivables"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_history.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'dcf_history'`

- [ ] **Step 3: Implement**

`check_footing` sums the classified lines per side and compares against the reported totals, raising with both numbers and the unclassified line names when they differ by more than `tol`. `historical_ratios` computes each driver year by year, dividing balance-sheet items by the *following* year's sales and skipping the final year, and derives `realized_capex` from the PP&E roll-forward with reported depreciation so the two can be compared against each other.

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/dcf_history.py plugins/dcf/skills/dcf/tests/test_history.py
git commit -m "Compute historical driver ratios, and refuse an unfooted classification"
```

---

### Task 7: The HTML app and its JavaScript port

**Files:**
- Create: `plugins/dcf/skills/dcf/app_template.html`
- Create: `plugins/dcf/skills/dcf/build_app.py`
- Test: `plugins/dcf/skills/dcf/tests/test_parity.py`

**Interfaces:**
- Consumes: `run_model` from Task 4
- Produces: `build_app(bundle: dict, out_path: str) -> str`. The template contains the literal token `/*__BUNDLE__*/` and `/*__BASELINE__*/`; `build_app` replaces them with `JSON.stringify`-able payloads and writes the file.
- The JS port exposes `window.DCF.runModel(bundle)` with the same return shape as `run_model`, so the parity test can drive it under node.

- [ ] **Step 1: Write the failing parity test**

```python
import json, shutil, subprocess, pytest
from dcf_engine import run_model
from build_app import JS_ENGINE_SOURCE
from test_schedule import bundle

node = shutil.which("node")


@pytest.mark.skipif(not node, reason="node is not installed; the app's own "
                                     "on-load banner is the guarantee here")
def test_js_port_matches_python(tmp_path):
    b = bundle()
    b["base"]["nol"] = 250.0
    b["base"]["debt_claims"] = {"debt": 400.0}
    script = tmp_path / "run.js"
    script.write_text(JS_ENGINE_SOURCE +
                      f"\nconsole.log(JSON.stringify(runModel({json.dumps(b)})));")
    got = json.loads(subprocess.run([node, str(script)], capture_output=True,
                                    text=True, check=True).stdout)
    want = run_model(b)
    assert got["ev_ops"] == pytest.approx(want["ev_ops"], rel=1e-9)
    assert got["equity_value"] == pytest.approx(want["equity_value"], rel=1e-9)
    for a, b_ in zip(got["schedule"], want["schedule"]):
        for key in ("sales", "ebitda", "net_ppe", "depreciation", "capex",
                    "nwc", "delta_nwc", "ebit", "tax", "fcf", "pv_fcf"):
            assert a[key] == pytest.approx(b_[key], rel=1e-9), key
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_parity.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'build_app'`

- [ ] **Step 3: Write the template and the builder**

`app_template.html` holds, in one file with no external references:
- a `<script>` block defining `runModel` as a line-for-line port of `dcf_engine.py` — `driver`, `salesPath`, `buildSchedule`, `applyTaxes`, `nolShieldPv`, `runModel` — reading a `BUNDLE` object injected at `/*__BUNDLE__*/` and comparing against a `BASELINE` object injected at `/*__BASELINE__*/`;
- an on-load check that walks every schedule cell and every headline number against `BASELINE` at relative tolerance 1e-9 and, on any mismatch, shows a red banner naming the first cell that disagrees;
- an input grid built at load time from `BUNDLE.classification`: historical columns read-only and greyed, then five editable year columns and a terminal column, rows grouped growth and margin / PP&E and depreciation / operating assets / operating liabilities / taxes, plus single cells for WACC, the NOL limitation, and diluted shares;
- output blocks for the schedule through year 7, the bridge, the equity value and value per share, and a WACC-by-terminal-growth sensitivity grid;
- a notes panel carrying `rates.wacc_derivation`, the classification table, and each driver's `rationale`;
- a reset control restoring `BUNDLE`;
- an inline warnings list driven by `result.warnings`.

`build_app.py` exposes `JS_ENGINE_SOURCE` (the engine `<script>` body, extracted from the template between the markers `// --- engine start ---` and `// --- engine end ---`, with an appended `module.exports` guard so node can run it) and `build_app(bundle, out_path)`.

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`
Expected: all pass, parity included where node exists

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/app_template.html plugins/dcf/skills/dcf/build_app.py plugins/dcf/skills/dcf/tests/test_parity.py
git commit -m "Emit the interactive app, with a JS port that checks itself on load"
```

---

### Task 8: The Excel workbook

**Files:**
- Create: `plugins/dcf/skills/dcf/build_workbook.py`
- Test: `plugins/dcf/skills/dcf/tests/test_workbook.py`

**Interfaces:**
- Consumes: `run_model` from Task 4
- Produces: `build_workbook(bundle: dict, out_path: str) -> str`, writing sheets `Inputs`, `Model`, `Bridge`, `Historical`, `Check`.

- [ ] **Step 1: Write the failing test**

```python
import openpyxl, pytest
from build_workbook import build_workbook
from test_schedule import bundle


def test_model_cells_are_formulas_not_values(tmp_path):
    p = tmp_path / "m.xlsx"
    build_workbook(bundle(), str(p))
    wb = openpyxl.load_workbook(str(p))
    assert {"Inputs", "Model", "Bridge", "Historical", "Check"} <= set(wb.sheetnames)
    ws = wb["Model"]
    formulas = [c.value for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("=")]
    assert len(formulas) > 40


def test_check_sheet_compares_against_the_python_baseline(tmp_path):
    p = tmp_path / "m.xlsx"
    build_workbook(bundle(), str(p))
    ws = openpyxl.load_workbook(str(p))["Check"]
    text = " ".join(str(c.value) for row in ws.iter_rows() for c in row
                    if c.value is not None)
    assert "FAIL" in text and "IF(" in text
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/test_workbook.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'build_workbook'`

- [ ] **Step 3: Implement**

`Inputs` holds every driver as a labelled row with five year columns and a terminal column, plus WACC, NOL limitation and diluted shares. `Model` reproduces the recursion in formulas that reference `Inputs` — one column per year 1 through 7, with year 6 and 7 pointing at the terminal column. `Bridge` references `Model`. `Historical` is a values-only dump of `bundle["history"]`. `Check` holds the Python baseline for every `Model` cell alongside `=IF(ABS(Model!X-baseline)>0.000001,"FAIL","ok")`, with a conditional-format rule painting FAIL red.

- [ ] **Step 4: Run tests**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add plugins/dcf/skills/dcf/build_workbook.py plugins/dcf/skills/dcf/tests/test_workbook.py
git commit -m "Write the workbook with live formulas and a self-checking Check sheet"
```

---

### Task 9: SKILL.md and the reference documents

**Files:**
- Create: `plugins/dcf/skills/dcf/SKILL.md`
- Create: `plugins/dcf/skills/dcf/reference/model.md`
- Create: `plugins/dcf/skills/dcf/reference/classification.md`
- Create: `plugins/dcf/skills/dcf/reference/staging.md`
- Create: `plugins/dcf/skills/dcf/reference/reading-text.md`

**Interfaces:**
- Consumes: every script above
- Produces: the skill itself

- [ ] **Step 1: Write SKILL.md**

Frontmatter `name: dcf` and a description in the voice of `finance-data`'s: what it does, and the phrasings that should trigger it ("value this company", "build a DCF", "two-stage enterprise valuation", "what is ACDC worth"). Body: the five phases and the three gates, stated as an ordered procedure; the rule that Claude writes the bundle and never the arithmetic; the exact commands to run each script; and pointers into `reference/`.

- [ ] **Step 2: Write the reference documents**

`model.md` is section 2 of the spec. `classification.md` is the bucket table plus the hard cases, each with a default and its reasoning: operating leases, goodwill and acquired intangibles, deferred taxes, tax receivable agreements, related-party balances, noncontrolling interests, mezzanine preferred, affiliates. `staging.md` is the expected folder layout and the error messages the loader gives. `reading-text.md` is what to look for driver by driver, and the rule that evidence is cited to file and location.

- [ ] **Step 3: Commit**

```bash
git add plugins/dcf/skills/dcf/SKILL.md plugins/dcf/skills/dcf/reference
git commit -m "Write the skill and its reference documents"
```

---

### Task 10: End-to-end on ACDC

**Files:**
- Create: `plugins/dcf/skills/dcf/tests/test_end_to_end.py`

**Interfaces:**
- Consumes: everything

- [ ] **Step 1: Write the test**

A small hand-built bundle for ProFrac (ACDC) from `~/repos/mgmt638/data/acdc_financials_10k.xlsx`, run through `run_model`, `build_app` and `build_workbook` into `tmp_path`, asserting that both files exist, that the app contains no `http://` or `https://` reference, and that the reported warnings list is what the company's actual loss history implies.

- [ ] **Step 2: Run the whole suite**

Run: `cd plugins/dcf/skills/dcf && python -m pytest tests/ -v`

- [ ] **Step 3: Open the app and look at it**

Render the built app and confirm the banner is absent, the grid is editable, and edits move the value.

- [ ] **Step 4: Commit**

```bash
git add plugins/dcf/skills/dcf/tests/test_end_to_end.py
git commit -m "Run the whole pipeline end to end on ProFrac"
```
