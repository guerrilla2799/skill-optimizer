#!/usr/bin/env python3
"""Step 7: run the old and new versions of a skill against the same tests and compare.

<work>/tests.json:
  {
    "skill": "my-skill",
    "after": "path/to/the/edited/skill",      # optional, default: the folder snapshot.py copied
    "phrases": [{"text": "fix my hook", "should_trigger": true}, ...],
    "tasks":   [{"prompt": "...", "checks": [{"type": "contains", "value": "..."}]}]
  }
Check types: contains, not_contains, regex, max_words, min_words.

Each version is installed into a scratch project at <work>/run-<before|after>/.claude/skills/,
and every phrase and task runs once through `claude -p` from there. The new version ships only
if it scores at least as well as the old one on both phrases and tasks.

Usage: trigger_test.py <work> [--dry-run | --yes] [--model MODEL] [--claude claude] [--timeout 300]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".git")


def load_tests(work: Path) -> dict:
    t = json.loads((work / "tests.json").read_text())
    if not t.get("skill") or not t.get("phrases"):
        raise SystemExit("tests.json needs 'skill' and 'phrases'")
    return t


def triggered(stream: str, skill: str) -> bool:
    """True when a stream-json transcript shows the Skill tool called with this skill."""
    for line in stream.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        for block in (ev.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                called = str((block.get("input") or {}).get("skill", ""))
                if called.split(":")[-1] == skill:
                    return True
    return False


def apply_check(check: dict, output: str) -> bool:
    kind, val = check.get("type"), check.get("value")
    words = len(output.split())
    if kind == "contains":
        return str(val).lower() in output.lower()
    if kind == "not_contains":
        return str(val).lower() not in output.lower()
    if kind == "regex":
        return re.search(str(val), output, re.S | re.I) is not None
    if kind == "max_words":
        return words <= int(val)
    if kind == "min_words":
        return words >= int(val)
    raise ValueError(f"unknown check type: {kind}")


def score(phrase_results: list[bool], phrases: list[dict], task_results: list[list[bool]]) -> dict:
    hits = sum(1 for r, p in zip(phrase_results, phrases) if r == bool(p.get("should_trigger")))
    checks = [c for t in task_results for c in t]
    return {
        "phrases_correct": hits,
        "phrases_total": len(phrases),
        "checks_passed": sum(checks),
        "checks_total": len(checks),
    }


def verdict(before: dict, after: dict) -> str:
    ok = after["phrases_correct"] >= before["phrases_correct"] and after["checks_passed"] >= before["checks_passed"]
    return "SHIP" if ok else "DO NOT SHIP"


def install(src: Path, project: Path, skill: str) -> None:
    dest = project / ".claude" / "skills" / skill
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, ignore=IGNORE)


def run_claude(cmd: list[str], cwd: Path, timeout: int) -> str:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return ""
    return p.stdout


def run_version(label: str, src: Path, tests: dict, work: Path, a) -> dict:
    project = work / f"run-{label}"
    install(src, project, tests["skill"])
    base = [a.claude, "-p"]
    if a.model:
        base += ["--model", a.model]
    phrase_results = []
    for ph in tests["phrases"]:
        out = run_claude(base + [ph["text"], "--output-format", "stream-json", "--verbose", "--max-turns", "2"], project, a.timeout)
        phrase_results.append(triggered(out, tests["skill"]))
        print(f"  [{label}] {'fired ' if phrase_results[-1] else 'quiet '} {ph['text']}", flush=True)
    task_results = []
    for t in tests.get("tasks", []):
        raw = run_claude(base + [t["prompt"], "--output-format", "json"], project, a.timeout)
        try:
            text = json.loads(raw).get("result", "")
        except json.JSONDecodeError:
            text = raw
        task_results.append([apply_check(c, text) for c in t.get("checks", [])])
        (project / f"task-{len(task_results)}.txt").write_text(text)
    return score(phrase_results, tests["phrases"], task_results)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--yes", action="store_true", help="confirm the model calls")
    ap.add_argument("--model")
    ap.add_argument("--claude", default="claude")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args(argv)

    work = Path(a.work).expanduser().resolve()
    tests = load_tests(work)
    before = work / "before"
    src = work / "source.txt"
    after_path = tests.get("after") or (src.read_text().strip() if src.is_file() else "")
    after = Path(after_path).expanduser().resolve() if after_path else None
    if not before.is_dir():
        raise SystemExit(f"No snapshot at {before}. Run snapshot.py first.")
    if after is None or not (after / "SKILL.md").is_file():
        raise SystemExit("No edited skill found. Set 'after' in tests.json, or run snapshot.py so source.txt exists.")
    calls = 2 * (len(tests["phrases"]) + len(tests.get("tasks", [])))
    if a.dry_run:
        print(f"{calls} model calls: {len(tests['phrases'])} phrases and {len(tests.get('tasks', []))} tasks, run once per version.")
        return 0
    if shutil.which(a.claude) is None:
        raise SystemExit(f"'{a.claude}' not found. Install the Claude Code CLI or pass --claude.")
    glob = Path.home() / ".claude" / "skills" / tests["skill"]
    if glob.exists():
        print(f"WARNING: {glob} is installed globally and can answer instead of the test copy.", file=sys.stderr)
    results = {"before": run_version("before", before, tests, work, a), "after": run_version("after", after, tests, work, a)}
    results["verdict"] = verdict(results["before"], results["after"])
    (work / "results.json").write_text(json.dumps(results, indent=2))
    for k in ("before", "after"):
        r = results[k]
        print(f"{k:>6}: phrases {r['phrases_correct']}/{r['phrases_total']}, task checks {r['checks_passed']}/{r['checks_total']}")
    print(results["verdict"])
    return 0 if results["verdict"] == "SHIP" else 1


if __name__ == "__main__":
    sys.exit(main())
