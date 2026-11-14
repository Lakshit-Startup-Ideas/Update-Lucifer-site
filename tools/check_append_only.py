#!/usr/bin/env python3
"""Enforces that data/milestones.json only ever grows.

    python3 tools/check_append_only.py [--base <git ref>]      (default base: HEAD)

Rules, checked against the version of the file at the base ref:
  - the "schema" and "rule" fields are unchanged;
  - every earlier version and entry is still there, in the same order, byte-for-byte equal, except that an entry's "updates" list may be extended
    (earlier updates unchanged and in order);
  - new versions and entries may only be added at the end;
  - ids are unique and every entry belongs to a declared version.
An edit or a removal of anything published is a failure. Exit code 1 on any problem.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

FILE = "data/milestones.json"
REQUIRED = ("id", "version", "label", "date", "title", "status", "summary", "points", "not_shown", "links", "updates")
STATUSES = {"done", "partly", "blocked", "planned"}


def check(previous: dict | None, current: dict) -> list[str]:
    problems: list[str] = []
    ids = [e.get("id") for e in current.get("entries", [])]
    if len(ids) != len(set(ids)):
        problems.append("duplicate entry ids")
    declared = {v.get("id") for v in current.get("versions", [])}
    for e in current.get("entries", []):
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            problems.append(f"{e.get('id')}: missing fields {missing}")
        if e.get("version") not in declared:
            problems.append(f"{e.get('id')}: version {e.get('version')!r} is not declared")
        if e.get("status") not in STATUSES:
            problems.append(f"{e.get('id')}: unknown status {e.get('status')!r}")
    if previous is None:
        return problems
    for key in ("schema", "rule"):
        if previous.get(key) != current.get(key):
            problems.append(f"{key} changed")
    old_v, new_v = previous.get("versions", []), current.get("versions", [])
    if new_v[:len(old_v)] != old_v:
        problems.append("an earlier version block was edited, reordered or removed")
    old_e, new_e = previous.get("entries", []), current.get("entries", [])
    if len(new_e) < len(old_e):
        problems.append(f"{len(old_e) - len(new_e)} entries removed")
    for old, new in zip(old_e, new_e):
        if old.get("id") != new.get("id"):
            problems.append(f"entry order changed at {old.get('id')!r}")
            break
        rest_old, rest_new = {k: v for k, v in old.items() if k != "updates"}, {k: v for k, v in new.items() if k != "updates"}
        if rest_old != rest_new:
            problems.append(f"{old['id']}: published fields were edited (add an update instead)")
        if new.get("updates", [])[:len(old.get("updates", []))] != old.get("updates", []):
            problems.append(f"{old['id']}: an earlier update was edited or removed")
    return problems


def load_base(ref: str) -> dict | None:
    out = subprocess.run(["git", "show", f"{ref}:{FILE}"], capture_output=True, text=True, cwd=Path(__file__).resolve().parent.parent)
    return json.loads(out.stdout) if out.returncode == 0 else None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD")
    args = ap.parse_args()
    current = json.loads((Path(__file__).resolve().parent.parent / FILE).read_text())
    problems = check(load_base(args.base), current)
    for p in problems:
        print("FAIL:", p)
    print("append-only check:", "FAILED" if problems else f"ok ({len(current['entries'])} entries, base {args.base})")
    sys.exit(1 if problems else 0)
