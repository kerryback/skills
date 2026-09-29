"""The JavaScript port must agree with the Python engine.

Warning text is not compared: the two languages format numbers differently, and
the page would cry drift over a thousands separator. Numbers are compared, and
those are what anyone acts on.
"""

import json
import shutil
import subprocess

import pytest

from build_app import JS_ENGINE_SOURCE, build_app
from dcf_engine import run_model
from test_schedule import bundle, const

NODE = shutil.which("node")

PARITY_KEYS = ["sales", "ebitda", "net_ppe", "depreciation", "capex", "nwc",
               "delta_nwc", "ebit", "tax", "nol_used", "nol_close",
               "taxable_income", "effective_tax_rate", "fcf", "pv_fcf"]

HEADLINE_KEYS = ["ev_ops", "pv_explicit", "pv_terminal", "terminal_value",
                 "pv_nol", "equity_value", "value_per_share"]


def rich_bundle():
    """A bundle that exercises every branch the port could get wrong."""
    b = bundle()
    b["base"]["nol"] = 250.0
    b["base"]["nonoperating_assets"] = {"cash": 50.0, "investments": 12.0}
    b["base"]["debt_claims"] = {"long_term_debt": 400.0, "lease_liabilities": 75.0}
    b["base"]["equity_claims"] = {"noncontrolling_interests": 30.0}
    b["base"]["operating_assets"]["inventories"] = 90.0
    b["assumptions"]["operating_assets"]["inventories"] = const(0.08)
    # A year of losses, a ramp, and a year-5 turnover away from terminal, so the
    # carryforward, the transition and the warnings all get exercised.
    b["assumptions"]["ebitda_margin"]["explicit"] = [-0.05, 0.02, 0.12, 0.18, 0.21]
    b["assumptions"]["sales_growth"]["explicit"] = [0.30, 0.15, 0.08, 0.05, 0.04]
    b["assumptions"]["sales_to_net_ppe"]["explicit"] = [1.6, 1.7, 1.8, 1.9, 2.4]
    b["assumptions"]["cash_tax_rate"]["explicit"] = [0.25, 0.25, 0.24, 0.23, 0.23]
    return b


def run_under_node(b, tmp_path):
    script = tmp_path / "run.js"
    script.write_text(
        JS_ENGINE_SOURCE
        + "\nprocess.stdout.write(JSON.stringify(runModel("
        + json.dumps(b) + ")));\n")
    proc = subprocess.run([NODE, str(script)], capture_output=True, text=True)
    if proc.returncode:
        raise AssertionError("the JS engine would not run:\n" + proc.stderr)
    return json.loads(proc.stdout)


@pytest.mark.skipif(
    not NODE,
    reason="node is not installed; the app's own on-load banner is the "
           "guarantee that matters here")
@pytest.mark.parametrize("make", [bundle, rich_bundle], ids=["steady", "rich"])
def test_js_port_matches_python(make, tmp_path):
    b = make()
    got, want = run_under_node(b, tmp_path), run_model(b)

    for a, e in zip(got["schedule"], want["schedule"]):
        assert a["year"] == e["year"]
        for key in PARITY_KEYS:
            assert a[key] == pytest.approx(e[key], rel=1e-9, abs=1e-12), \
                f"year {e['year']}, {key}"

    for key in HEADLINE_KEYS:
        assert got[key] == pytest.approx(want[key], rel=1e-9, abs=1e-12), key

    assert len(got["bridge"]) == len(want["bridge"])
    for a, e in zip(got["bridge"], want["bridge"]):
        assert a["label"] == e["label"]
        assert a["amount"] == pytest.approx(e["amount"], rel=1e-9, abs=1e-12)

    assert len(got["warnings"]) == len(want["warnings"])


@pytest.mark.skipif(not NODE, reason="node is not installed")
def test_js_port_refuses_the_same_bundles_python_refuses(tmp_path):
    b = bundle()
    b["rates"]["wacc"] = 0.04
    script = tmp_path / "bad.js"
    script.write_text(
        JS_ENGINE_SOURCE
        + "\ntry { runModel(" + json.dumps(b) + "); process.stdout.write('NO ERROR'); }"
        + "\ncatch (e) { process.stdout.write(e.message); }\n")
    out = subprocess.run([NODE, str(script)], capture_output=True, text=True).stdout
    assert "perpetuity does not exist" in out


def test_built_app_is_self_contained(tmp_path):
    out = tmp_path / "app.html"
    build_app(rich_bundle(), str(out))
    text = out.read_text(encoding="utf-8")
    assert "http://" not in text
    assert "https://" not in text
    assert "/*__BUNDLE__*/" not in text
    assert "/*__BASELINE__*/" not in text


def test_built_app_embeds_the_python_baseline(tmp_path):
    b = rich_bundle()
    out = tmp_path / "app.html"
    build_app(b, str(out))
    text = out.read_text(encoding="utf-8")
    want = run_model(b)["ev_ops"]
    assert repr(want)[:12] in text or json.dumps(want)[:12] in text
