"""Two pages: the argument, and the answer. Neither does arithmetic."""

import pathlib
import re

import pytest

from dcf_engine import run_model
from build_pages import (LIVE_RELOAD, build_assumptions, build_pages,
                         build_valuation, fmt)
from dcf_engine import sensitivity_axes, sensitivity_grid
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
    b["assumptions"]["sales_growth"]["guidance"] = (
        "How to think about the margin on volume: guidance covers one year, so "
        "years 2 through 5 are a fade you have to argue for.")
    b["assumptions"]["sales_growth"]["citations"] = [
        {"quote": "Nut costs are the whole story this year.",
         "speaker": "Frank S. Pellegrino",
         "source": "transcripts/FY2026Q4.txt"}]
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
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("pages")
    a, v = build_pages(rich_bundle(), str(out), slug="rich")
    return {"assumptions": pathlib.Path(a).read_text(encoding="utf-8"),
            "valuation": pathlib.Path(v).read_text(encoding="utf-8"),
            "dir": out}


@pytest.fixture(scope="module")
def page(built):
    """The valuation page, for the checks that were written against it."""
    return built["valuation"]





def test_the_page_follows_the_reader_s_appearance_setting(page):
    """The page does not impose a theme; it reads prefers-color-scheme."""
    assert "prefers-color-scheme: dark" in page
    assert "--ground: #ffffff" in page      # the light default


def test_neither_page_is_self_contained_by_accident(built):
    for page in (built["assumptions"], built["valuation"]):
        assert "http://" not in page
        assert "https://" not in page


def test_no_template_token_survives(built):
    for page in (built["assumptions"], built["valuation"]):
        assert not re.search(r"__[A-Z_]+__", page)


def test_the_headline_numbers_are_the_engine_s(page):
    want = run_model(rich_bundle())
    assert fmt(want["ev_ops"], "num") in page
    assert fmt(want["equity_value"], "num") in page
    assert fmt(want["value_per_share"], "share") in page


def test_each_page_says_where_to_go_next(built):
    valuation = " ".join(built["valuation"].split())
    assert "not a recommendation" in valuation
    assert "assumptions.csv" in valuation and "rebuilds" in valuation

    assumptions = " ".join(built["assumptions"].split())
    assert "deliberately shows no valuation" in assumptions


def test_the_numbers_are_presented_as_suggestions_not_conclusions(built):
    flat = " ".join(built["assumptions"].split())
    assert "Suggested assumptions" in flat
    assert "a suggestion, not a conclusion" in flat
    assert "The decision is yours" in flat


def test_each_driver_gets_a_guidance_section(built):
    page = built["assumptions"]
    assert "Driver by driver" in page
    assert "<section class='guide'>" in page
    assert "How to think about the margin" in page
    assert "History" in page and "Suggested" in page


def test_citations_are_quoted_and_attributed(built):
    page = built["assumptions"]
    assert "Nut costs are the whole story" in page
    assert "Frank S. Pellegrino" in page
    assert "<cite>" in page


def test_a_driver_with_only_a_rationale_still_appears(built):
    """Guidance is preferred, but a bare rationale is better than silence."""
    assert "A loss year, then a recovery." in built["assumptions"]


def test_the_assumptions_page_shows_no_valuation(built):
    """Read the case for each driver without the answer pulling you to it.

    The words may appear -- the page explains what the model does -- but none of
    the numbers may.
    """
    page = built["assumptions"]
    want = run_model(rich_bundle())
    assert fmt(want["value_per_share"], "share") not in page
    assert fmt(want["ev_ops"], "num") not in page
    assert fmt(want["equity_value"], "num") not in page
    assert "<h2>Forecast</h2>" not in page
    assert "shareholders" not in page.lower()
    assert "Sensitivity" not in page


def test_the_valuation_page_shows_the_answer(built):
    page = built["valuation"]
    want = run_model(rich_bundle())
    assert fmt(want["value_per_share"], "share") in page
    assert "Free cash flow" in page


def test_the_pages_link_to_each_other(built):
    assert 'href="rich-valuation.html"' in built["assumptions"]
    assert 'href="rich-assumptions.html"' in built["valuation"]


def test_the_guidance_does_not_bloat_the_valuation_page(built):
    """The argument lives on one page and the answer on the other."""
    assert "<section class='guide'>" not in built["valuation"]


def test_neither_page_carries_a_script_by_default(built):
    for page in (built["assumptions"], built["valuation"]):
        assert "<script" not in page.lower()


def test_live_mode_injects_the_reload_poller_and_nothing_else(tmp_path):
    a, v = build_pages(rich_bundle(), str(tmp_path), slug="rich", live=True)
    for path in (a, v):
        page = pathlib.Path(path).read_text(encoding="utf-8")
        assert LIVE_RELOAD in page
        assert page.count("<script") == 1
        # The poller asks whether the file changed. It computes nothing.
        assert "location.reload" in page
        assert "fcf" not in page.split("<script")[1]


def test_the_shipped_pages_stay_script_free(tmp_path):
    """live=False is the default precisely so an artifact cannot leak a script."""
    for path in build_pages(rich_bundle(), str(tmp_path), slug="rich"):
        assert "<script" not in pathlib.Path(path).read_text(encoding="utf-8").lower()


def test_a_bundle_with_no_guidance_at_all_says_so(tmp_path):
    b = rich_bundle()
    for name in ("sales_growth", "ebitda_margin"):
        b["assumptions"][name].pop("rationale", None)
        b["assumptions"][name].pop("guidance", None)
        b["assumptions"][name].pop("citations", None)
    out = tmp_path / "bare.html"
    build_assumptions(b, str(out))
    assert "not enough to choose from" in out.read_text(encoding="utf-8")


def test_warnings_are_rendered(page):
    assert "carryforward" in page
    assert "absorbs the whole adjustment" in page


def test_the_classification_and_its_reasons_sit_with_the_argument(built):
    page = built["assumptions"]
    assert "Accounts receivable, net" in page
    assert "Trade receivables." in page
    assert "operating_liability" in page


def test_history_notes_sit_with_the_argument(built):
    assert "did not cover depreciation" in built["assumptions"]


def test_the_wacc_derivation_is_on_both_pages(built):
    """It is an assumption and it is also the number the answer turns on."""
    assert "CAPM: 4.2" in built["assumptions"]
    assert "CAPM: 4.2" in built["valuation"]


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
    build_valuation(b, str(out))
    text = out.read_text(encoding="utf-8")
    assert "<Holdings>" not in text
    assert "&lt;Holdings&gt;" in text
    assert "Smith &amp; Sons" in text


def test_a_company_with_no_history_still_renders(tmp_path):
    b = rich_bundle()
    del b["history"]
    a, v = build_pages(b, str(tmp_path), slug="nohist")
    assert "raised nothing worth flagging" in pathlib.Path(a).read_text()
    for path in (a, v):
        assert not re.search(r"__[A-Z_]+__", pathlib.Path(path).read_text())
