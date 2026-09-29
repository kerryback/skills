"""The HTML report: a record of one valuation, with no arithmetic of its own."""

import re

import pytest

from build_app import build_app, fmt
from dcf_engine import run_model, sensitivity_axes, sensitivity_grid
from test_schedule import bundle, const


def rich_bundle():
    """A bundle that exercises every branch the report has to render."""
    b = bundle()
    b["meta"]["ticker"] = "RICH"
    b["meta"]["fiscal_year_end"] = "2025-12-31"
    b["base"]["nol"] = 250.0
    b["base"]["nonoperating_assets"] = {"cash": 50.0, "investments": 12.0}
    b["base"]["debt_claims"] = {"long_term_debt": 400.0, "lease_liabilities": 75.0}
    b["base"]["equity_claims"] = {"noncontrolling_interests": 30.0}
    b["base"]["operating_assets"]["inventories"] = 90.0
    b["assumptions"]["operating_assets"]["inventories"] = const(0.08)
    b["assumptions"]["ebitda_margin"]["explicit"] = [-0.05, 0.02, 0.12, 0.18, 0.21]
    b["assumptions"]["ebitda_margin"]["rationale"] = "A loss year, then a recovery."
    b["assumptions"]["sales_growth"]["explicit"] = [0.30, 0.15, 0.08, 0.05, 0.04]
    b["assumptions"]["sales_to_net_ppe"]["explicit"] = [1.6, 1.7, 1.8, 1.9, 2.4]
    b["classification"] = [
        {"line": "Accounts receivable, net", "bucket": "operating_asset",
         "key": "receivables", "note": "Trade receivables."},
        {"line": "Inventories", "bucket": "operating_asset", "key": "inventories",
         "note": "Finished goods."},
        {"line": "Accounts payable", "bucket": "operating_liability",
         "key": "payables", "note": "Trade payables."},
    ]
    b["rates"]["wacc_derivation"] = "CAPM: 4.2 + 1.1 x 5.0 = 9.7 percent."
    b["history"] = {
        "years": [2021, 2022, 2023, 2024, 2025],
        "ratios": {"sales_growth": {2022: 0.12, 2023: 0.04},
                   "operating_assets": {"receivables": {2022: 0.19}}},
        "notes": ["EBITDA did not cover depreciation in 2025."],
    }
    return b


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    out = tmp_path_factory.mktemp("report") / "report.html"
    build_app(rich_bundle(), str(out))
    return out.read_text(encoding="utf-8")


def test_the_page_carries_no_script_at_all(page):
    """No script means no second engine, so the page cannot drift from the model."""
    assert "<script" not in page.lower()
    assert "javascript:" not in page.lower()
    assert "onclick" not in page.lower()


def test_the_page_is_light_only(page):
    """It gets projected and printed as often as it gets read on a laptop."""
    assert "prefers-color-scheme" not in page
    assert 'data-theme' not in page
    assert "color-scheme: light" in page


def test_the_page_is_self_contained(page):
    assert "http://" not in page
    assert "https://" not in page


def test_no_template_token_survives(page):
    assert not re.search(r"__[A-Z_]+__", page)


def test_the_headline_numbers_are_the_engine_s(page):
    want = run_model(rich_bundle())
    assert fmt(want["ev_ops"], "num") in page
    assert fmt(want["equity_value"], "num") in page
    assert fmt(want["value_per_share"], "share") in page


def test_the_page_says_where_to_go_to_change_anything(page):
    flat = " ".join(page.split())      # the prose is line-wrapped in the template
    assert "not a calculator" in flat
    assert "live formula" in flat


def test_warnings_are_rendered(page):
    assert "carryforward" in page
    assert "absorbs the whole adjustment" in page


def test_the_classification_and_its_reasons_travel_with_the_page(page):
    assert "Accounts receivable, net" in page
    assert "Trade receivables." in page
    assert "operating_liability" in page


def test_rationales_and_history_notes_travel_with_the_page(page):
    assert "A loss year, then a recovery." in page
    assert "did not cover depreciation" in page
    assert "CAPM: 4.2" in page


def test_the_sensitivity_table_centres_on_the_base_case(page):
    b = rich_bundle()
    waccs, growths = sensitivity_axes(b)
    grid = sensitivity_grid(b, waccs, growths)
    assert "sens here" in page
    assert fmt(grid[2][2], "share") in page


def test_historical_columns_show_what_history_there_is(page):
    assert "2021" in page and "2025" in page


def test_html_in_a_company_name_is_escaped(tmp_path):
    b = rich_bundle()
    b["meta"]["company"] = "Smith & Sons <Holdings>"
    out = tmp_path / "escaped.html"
    build_app(b, str(out))
    text = out.read_text(encoding="utf-8")
    assert "<Holdings>" not in text
    assert "&lt;Holdings&gt;" in text
    assert "Smith &amp; Sons" in text


def test_a_company_with_no_history_still_renders(tmp_path):
    b = rich_bundle()
    del b["history"]
    out = tmp_path / "nohistory.html"
    build_app(b, str(out))
    text = out.read_text(encoding="utf-8")
    assert "raised nothing worth flagging" in text
    assert not re.search(r"__[A-Z_]+__", text)
