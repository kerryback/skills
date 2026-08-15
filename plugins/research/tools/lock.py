"""One round at a time, enforced by git rather than by memory.

`project/global/state.md` is long prose that the Coordinator rewrites wholesale
at every gate. Git cannot merge that, so two coauthors running rounds at once
produce a conflict on the one file that defines what the paper is — discovered
hours later, at merge time.

A `git push` is atomic, which makes it a usable mutex: claiming the round means
committing a lock file and pushing it. Exactly one push can win. The loser finds
out immediately, at the moment of claiming, instead of after a round's work.

    python -m tools.debate.lock claim  "peer rule for microcaps"
    python -m tools.debate.lock status
    python -m tools.debate.lock release

This guards the round, not the file: nothing stops someone editing state.md
outside a round. It is a coordination protocol between people who have agreed to
use it, not a permission system.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .runid import user_slug


def find_project_root(start=None) -> Path:
    p = Path(start or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "CLAUDE.md").exists():
            return cand
    return Path.cwd().resolve()

LOCK_REL = Path("project") / "global" / "ROUND_LOCK"


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args],
                          capture_output=True, text=True, check=check)


def _read(root: Path) -> dict | None:
    f = root / LOCK_REL
    if not f.exists():
        return None
    d = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def _sync(root: Path) -> None:
    """Get level with the remote so the lock we read is the current one."""
    _git(root, "fetch", "--quiet", "origin", check=False)
    _git(root, "merge", "--ff-only", "--quiet", "origin/main", check=False)


def cmd_status(root: Path, _note: str | None) -> int:
    _sync(root)
    lock = _read(root)
    if not lock:
        print("unlocked — no round in progress")
        return 0
    mine = lock.get("author") == user_slug()
    print(f"LOCKED by {lock.get('author')} ({'you' if mine else 'not you'})")
    print(f"  since : {lock.get('claimed')}")
    if lock.get("note"):
        print(f"  round : {lock['note']}")
    if not mine:
        print("\nIf that looks stale, ask them before releasing it. A lock is a claim on\n"
              "state.md, and clearing someone else's mid-round discards their gate.")
    return 0 if mine else 1


def cmd_claim(root: Path, note: str | None) -> int:
    _sync(root)
    lock = _read(root)
    me = user_slug()
    if lock:
        if lock.get("author") == me:
            print(f"already yours (since {lock.get('claimed')}) — carry on")
            return 0
        print(f"REFUSED: {lock.get('author')} holds the round since {lock.get('claimed')}",
              file=sys.stderr)
        if lock.get("note"):
            print(f"         working on: {lock['note']}", file=sys.stderr)
        return 1

    f = root / LOCK_REL
    body = f"author: {me}\nclaimed: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
    if note:
        body += f"note: {note}\n"
    f.write_text(body, encoding="utf-8")

    _git(root, "add", str(LOCK_REL))
    # --only: commit just the lock, never sweep up whatever else is staged.
    _git(root, "commit", "--only", str(LOCK_REL), "-m", f"round lock: {me}", check=False)
    push = _git(root, "push", "origin", "HEAD:main", check=False)
    if push.returncode != 0:
        # Someone else's push landed first. Undo ours and report who won.
        _git(root, "reset", "--hard", "HEAD~1", check=False)
        _sync(root)
        other = _read(root)
        who = other.get("author", "someone") if other else "someone"
        print(f"REFUSED: lost the race — {who} claimed the round first", file=sys.stderr)
        return 1
    print(f"claimed by {me}" + (f" — {note}" if note else ""))
    return 0


def _warn_if_undocumented(root: Path, claimed: str | None) -> None:
    """Releasing the round is the last moment the reason is still in someone's head.

    The changelog is written by `/refresh`, and `/refresh` only runs when
    somebody invokes it — so a round that ends any other way leaves the work
    committed and the WHY unrecorded. Nothing else notices, because the commits
    look perfectly fine.

    This warns and never blocks. Refusing to release would strand the lock and
    block the other coauthors, which is a worse failure than a thin changelog,
    and this is a coordination protocol rather than a permission system.
    """
    try:
        from .chronology import gaps
    except Exception:
        return
    try:
        g = gaps(root, (claimed or "")[:10] or None)
    except Exception:
        return
    if not g["count"]:
        return
    print(f"\nNOTE: {g['count']} commit(s) in this round have no changelog entry "
          f"after them.", file=sys.stderr)
    for c in g["undocumented_commits"][:5]:
        print(f"  {c['date']}  {c['summary']}", file=sys.stderr)
    if g["count"] > 5:
        print(f"  … and {g['count'] - 5} more", file=sys.stderr)
    print("Git has what changed; nothing has why. Add an entry to\n"
          "project/global/state.md before the reason is gone — /refresh writes one.\n"
          "See the full list with: python3 -m tools.chronology --gap --human",
          file=sys.stderr)


def cmd_release(root: Path, _note: str | None) -> int:
    _sync(root)
    lock = _read(root)
    if not lock:
        print("already unlocked")
        return 0
    me = user_slug()
    if lock.get("author") != me:
        print(f"REFUSED: the round is {lock.get('author')}'s, not yours. Ask them.",
              file=sys.stderr)
        return 1
    _warn_if_undocumented(root, lock.get("claimed"))
    (root / LOCK_REL).unlink()
    _git(root, "add", "--all", str(LOCK_REL), check=False)
    _git(root, "commit", "--only", str(LOCK_REL), "-m", f"round unlock: {me}", check=False)
    push = _git(root, "push", "origin", "HEAD:main", check=False)
    if push.returncode != 0:
        print("released locally, but the push failed — pull and push before the next round.",
              file=sys.stderr)
        return 1
    print("released")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="claim the round, so only one runs at a time")
    ap.add_argument("action", choices=["claim", "status", "release"])
    ap.add_argument("note", nargs="?", help="what this round is about (claim only)")
    ap.add_argument("--project", default=None)
    args = ap.parse_args()
    root = Path(args.project).resolve() if args.project else find_project_root()
    raise SystemExit({"claim": cmd_claim, "status": cmd_status, "release": cmd_release}
                     [args.action](root, args.note))


if __name__ == "__main__":
    main()
