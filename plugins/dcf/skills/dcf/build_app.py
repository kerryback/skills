"""Write the interactive one-page valuation app.

The app carries its own copy of the recursion in JavaScript, because the input
cells have to recompute in the browser. That is a second implementation of
arithmetic that already exists in ``dcf_engine.py``, so the page checks itself:
``build_app`` embeds the Python engine's base-case result, and the page
recomputes the base case on load and compares every cell against it. A port
that drifts paints a red banner instead of quietly showing a different number.

The file has no network dependencies of any kind. It has to open in a lab
container with no internet.
"""

import json
import os

from dcf_engine import run_model

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "app_template.html")

BUNDLE_TOKEN = "/*__BUNDLE__*/ null"
BASELINE_TOKEN = "/*__BASELINE__*/ null"
ENGINE_START = "// --- engine start ---"
ENGINE_END = "// --- engine end ---"


def _template():
    with open(TEMPLATE, encoding="utf-8") as fh:
        return fh.read()


def _extract_engine(text):
    start = text.index(ENGINE_START) + len(ENGINE_START)
    end = text.index(ENGINE_END)
    return text[start:end]


#: The JavaScript port on its own, so the parity test can run it under node.
JS_ENGINE_SOURCE = _extract_engine(_template())


def _baseline(result):
    """Just the numbers the page checks itself against.

    Warning *text* is deliberately excluded. Python and JavaScript format
    numbers differently, and a page that cried drift over a thousands separator
    would train its reader to ignore the banner.
    """
    return {
        "schedule": result["schedule"],
        "ev_ops": result["ev_ops"],
        "pv_explicit": result["pv_explicit"],
        "pv_terminal": result["pv_terminal"],
        "terminal_value": result["terminal_value"],
        "pv_nol": result["pv_nol"],
        "equity_value": result["equity_value"],
        "value_per_share": result["value_per_share"],
    }


def build_app(bundle, out_path):
    """Render the app for ``bundle`` and return the path written."""
    result = run_model(bundle)
    html = _template()
    html = html.replace(
        BUNDLE_TOKEN, json.dumps(bundle, indent=None, allow_nan=False))
    html = html.replace(
        BASELINE_TOKEN, json.dumps(_baseline(result), indent=None, allow_nan=False))

    if BUNDLE_TOKEN in html or BASELINE_TOKEN in html:
        raise RuntimeError("the template's injection tokens did not both replace")

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        raise SystemExit("usage: build_app.py <bundle.json> <out.html>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(build_app(json.load(fh), sys.argv[2]))
