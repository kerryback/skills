"""Native "choose folder" dialog.

The browser deliberately cannot hand a real filesystem path to a web page, but
this app only ever runs on the instructor's own machine, so the server can open
the OS dialog directly. Falls back to typing a path if no dialog is available.
"""

from __future__ import annotations

import subprocess
import sys

TIMEOUT = 180


def choose_folder(prompt: str = "Choose the folder for this course") -> str | None:
    """Return the chosen folder, or None if the instructor cancelled."""
    if sys.platform == "darwin":
        return _macos(prompt)
    return _tk(prompt)


def _macos(prompt: str) -> str | None:
    script = f'POSIX path of (choose folder with prompt "{prompt}")'
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _tk(prompt)
    if result.returncode != 0:
        return None  # cancelled
    return result.stdout.strip().rstrip("/") or None


def _tk(prompt: str) -> str | None:
    code = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)\n"
        f"print(filedialog.askdirectory(title={prompt!r}) or '')\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, timeout=TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() or None
