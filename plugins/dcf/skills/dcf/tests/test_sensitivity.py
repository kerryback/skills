"""The sensitivity grid, which both artifacts display and neither computes."""

import pytest

from dcf_engine import run_model, sensitivity_axes, sensitivity_grid
from test_schedule import bundle


def test_the_grid_is_rows_of_waccs_by_columns_of_growths():
    b = bundle()
    waccs, growths = [0.09, 0.10, 0.11], [0.02, 0.03]
    grid = sensitivity_grid(b, waccs, growths)
    assert len(grid) == 3 and all(len(row) == 2 for row in grid)


def test_the_centre_of_the_default_grid_is_the_base_case():
    b = bundle()
    waccs, growths = sensitivity_axes(b)
    assert waccs[2] == pytest.approx(b["rates"]["wacc"])
    assert growths[2] == pytest.approx(b["assumptions"]["sales_growth"]["terminal"])
    grid = sensitivity_grid(b, waccs, growths)
    assert grid[2][2] == pytest.approx(run_model(b)["value_per_share"])


def test_value_falls_as_the_discount_rate_rises():
    b = bundle()
    grid = sensitivity_grid(b, [0.08, 0.10, 0.12], [0.05])
    assert grid[0][0] > grid[1][0] > grid[2][0]


def test_a_pair_with_no_perpetuity_is_none_not_an_exception():
    b = bundle()
    grid = sensitivity_grid(b, [0.04], [0.05, 0.02])
    assert grid[0][0] is None          # growth at the discount rate
    assert grid[0][1] is not None


def test_the_grid_does_not_disturb_the_bundle():
    b = bundle()
    before = b["rates"]["wacc"], b["assumptions"]["sales_growth"]["terminal"]
    sensitivity_grid(b, *sensitivity_axes(b))
    assert (b["rates"]["wacc"], b["assumptions"]["sales_growth"]["terminal"]) == before
