"""Writing the results out when the class is over.

One CSV per session, next to the poll file, one row per answer option so it
opens as something you can read rather than nested JSON. Anonymous throughout:
there is no student column because there is no student data.
"""

from __future__ import annotations

import csv
import io
from datetime import date
from pathlib import Path
from typing import Any

from . import tally as tally_mod

HEADER = ["question", "type", "responses", "item", "count", "share", "note"]


def rows_for(index: int, question: dict[str, Any], answers: list[Any]) -> list[list[Any]]:
    result = tally_mod.tally(question, answers)
    number = index + 1
    kind = question["type"]
    total = result["responses"]
    rows: list[list[Any]] = []

    def row(item: Any, count: Any = "", share: Any = "", note: str = "") -> None:
        rows.append([f"{number}. {question['text']}", kind, total, item, count, share, note])

    if kind == "choice":
        correct = set(result.get("answer") or [])
        for position, option in enumerate(result["options"]):
            row(option["text"], option["count"], round(option["share"], 4),
                "correct" if position in correct else "")
    elif kind == "wordcloud":
        for entry in result["words"]:
            row(entry["word"], entry["count"])
    elif kind == "scale":
        for point in result["points"]:
            row(point["value"], point["count"])
        row("mean", result["mean"])
    elif kind == "number":
        row("mean", result["mean"])
        row("median", result["median"])
        if result.get("answer") is not None:
            row("actual", result["answer"], "", "the right answer")
    elif kind == "rank":
        for position, entry in enumerate(result["rows"]):
            row(entry["text"], entry["average"], "", f"ranked {position + 1}")

    if not rows:  # a question nobody answered still deserves a line
        row("", 0, "", "no responses")
    return rows


def write_csv(session: Any, when: date | None = None) -> str:
    """Write the CSV beside the poll file and return its path."""
    deck = session.deck
    if deck is None:
        raise ValueError("No poll is loaded.")

    source = Path(deck["path"])
    day = (when or date.today()).isoformat()
    target = source.with_name(f"{source.stem}-results-{day}.csv")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(HEADER)
    for index, question in enumerate(deck["questions"]):
        writer.writerows(rows_for(index, question, session.answers(index)))

    target.write_text(buffer.getvalue())
    return str(target)
