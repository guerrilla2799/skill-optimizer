#!/usr/bin/env python3
"""Step 2: copy a skill to <run-dir>/before/ so step 7 has something to test against.

Refuses to overwrite an existing snapshot. Use --force only to start over.
Usage: snapshot.py <skill-dir> <run-dir> [--force]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".git")


def snapshot(skill: Path, work: Path, force: bool = False) -> Path:
    if not (skill / "SKILL.md").is_file():
        raise SystemExit(f"{skill} has no SKILL.md")
    dest = work / "before"
    if dest.exists():
        if not force:
            raise SystemExit(f"{dest} already exists. A second snapshot would replace your baseline. Use --force to start over.")
        shutil.rmtree(dest)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill, dest, ignore=IGNORE)
    (work / "source.txt").write_text(str(skill) + "\n")
    return dest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("skill")
    ap.add_argument("work")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    dest = snapshot(Path(a.skill).expanduser().resolve(), Path(a.work).expanduser().resolve(), a.force)
    files = sum(1 for p in dest.rglob("*") if p.is_file())
    print(f"Snapshot: {dest} ({files} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
