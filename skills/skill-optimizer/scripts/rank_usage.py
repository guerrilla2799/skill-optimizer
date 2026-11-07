#!/usr/bin/env python3
"""Step 1: rank installed skills by how often they ran.

Sources:
  --transcripts DIR   Claude Code transcripts (default ~/.claude/projects). Counts Skill tool
                      calls and /slash-command invocations.
  --csv FILE          Your own counts, one "name,count" per line, for any other tool.
Skills found under --roots with no recorded runs are listed as zero-run.

Usage: rank_usage.py --roots ~/.claude/skills [--top 10] [--json]
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _skillfile import find_skills  # noqa: E402

SKILL_CALL = re.compile(r'"name"\s*:\s*"Skill"\s*,\s*"input"\s*:\s*\{\s*"skill"\s*:\s*"([^"]+)"')
SLASH = re.compile(r"<command-name>/?([\w:.-]+)</command-name>")


def count_transcripts(folder: Path) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    for f in folder.rglob("*.jsonl"):
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for name in SKILL_CALL.findall(text):
            counts[name] += 1
        for name in SLASH.findall(text):
            counts[name] += 1
    return counts


def count_csv(path: Path) -> collections.Counter:
    counts: collections.Counter = collections.Counter()
    with path.open(newline="") as fh:
        for row in csv.reader(fh):
            if len(row) >= 2 and row[1].strip().isdigit():
                counts[row[0].strip()] += int(row[1])
    return counts


def rank(counts: collections.Counter, installed: list[str]) -> dict:
    # A plugin skill is recorded as "plugin:name"; credit it to the bare name too.
    bare: collections.Counter = collections.Counter()
    for k, v in counts.items():
        bare[k.split(":")[-1]] += v
    rows = sorted(((n, bare.get(n, 0)) for n in installed), key=lambda r: (-r[1], r[0]))
    return {
        "ranked": [{"skill": n, "runs": c} for n, c in rows if c > 0],
        "zero_runs": [n for n, c in rows if c == 0],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roots", nargs="+", required=True, help="folders that hold <skill>/SKILL.md")
    ap.add_argument("--transcripts", default="~/.claude/projects")
    ap.add_argument("--csv", help="name,count file instead of transcripts")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    installed = sorted(find_skills(a.roots))
    if not installed:
        print("No skills found under --roots.", file=sys.stderr)
        return 1
    counts = count_csv(Path(a.csv)) if a.csv else count_transcripts(Path(a.transcripts).expanduser())
    result = rank(counts, installed)
    if a.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"{len(installed)} installed skills, {len(result['ranked'])} with recorded runs\n")
    print(f"Top {a.top}:")
    for r in result["ranked"][: a.top]:
        print(f"  {r['runs']:>5}  {r['skill']}")
    print(f"\nZero recorded runs ({len(result['zero_runs'])}):")
    for n in result["zero_runs"]:
        print(f"         {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
