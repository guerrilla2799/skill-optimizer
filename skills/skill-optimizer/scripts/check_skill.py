#!/usr/bin/env python3
"""Steps 3 and 5: the countable checks on one skill.

Errors (exit 1): missing frontmatter, name, or description; description over the limit;
broken relative links. Warnings: no quoted trigger phrases, no "do not use" boundary,
a long SKILL.md body, rule blocks pasted from a shared file, counting rules left in prose.

Usage: check_skill.py <skill-dir> [--shared DIR ...] [--limit 250] [--max-lines 150] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _skillfile import body, parse_frontmatter  # noqa: E402

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
COUNTING = re.compile(
    r"\b(under|at most|no more than|max(imum)?|exactly|between)\s+\d[\d,]*\s*(-|to|and)?\s*\d*\s*"
    r"(words?|characters?|chars?|lines?|slides?|bullets?|sentences?)\b",
    re.I,
)
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml", ".toml", ".tmpl"}


def norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def paragraphs(text: str, min_chars: int = 120) -> list[str]:
    out = []
    for p in re.split(r"\n\s*\n", text):
        n = norm(p)
        if len(n) >= min_chars:
            out.append(n)
    return out


def pasted_blocks(skill: Path, shared: list[Path]) -> list[dict]:
    index: dict[str, str] = {}
    for d in shared:
        for f in d.expanduser().rglob("*"):
            if f.is_file() and f.suffix in TEXT_EXT and skill not in f.parents:
                for p in paragraphs(f.read_text(errors="ignore")):
                    index.setdefault(p, str(f))
    hits = []
    for f in skill.rglob("*"):
        if f.is_file() and f.suffix in TEXT_EXT:
            for p in paragraphs(f.read_text(errors="ignore")):
                if p in index:
                    hits.append({"file": str(f.relative_to(skill)), "copy_of": index[p], "starts": p[:60]})
    return hits


def check(skill: Path, shared: list[Path], limit: int, max_lines: int) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    info: dict = {}
    root = skill / "SKILL.md"
    if not root.is_file():
        return {"errors": [f"{skill} has no SKILL.md"], "warnings": [], "info": {}}
    text = root.read_text(errors="ignore")
    fm = parse_frontmatter(text)
    if not fm:
        errors.append("SKILL.md has no frontmatter block")
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not name:
        errors.append("frontmatter has no name")
    elif name != skill.name:
        warnings.append(f"name '{name}' differs from folder '{skill.name}'; some loaders use one, some the other")
    if not desc:
        errors.append("frontmatter has no description")
    else:
        info["description_chars"] = len(desc)
        if len(desc) > limit:
            errors.append(f"description is {len(desc)} characters, limit {limit}")
        if not re.search(r"\"[^\"]{3,}\"", desc):
            warnings.append("description quotes no trigger phrases the user would type")
        if not re.search(r"\b(do not|don't|not for)\b", desc, re.I):
            warnings.append("description has no 'do not use' boundary")
    b = body(text)
    lines = b.count("\n") + 1
    info["body_lines"] = lines
    info["approx_tokens_loaded_on_trigger"] = len(text) // 4
    if lines > max_lines:
        warnings.append(f"SKILL.md body is {lines} lines, over {max_lines}; move detail into references/")
    for f in skill.rglob("*.md"):
        for target in LINK.findall(f.read_text(errors="ignore")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if path and not (f.parent / path).exists():
                errors.append(f"{f.relative_to(skill)}: broken link {target}")
    for hit in COUNTING.finditer(b):
        warnings.append(f"counting rule in prose, give it a script: \"{hit.group(0).strip()}\"")
    if shared:
        for h in pasted_blocks(skill, shared):
            warnings.append(f"{h['file']}: pasted copy of {h['copy_of']} (\"{h['starts']}...\"), link to it instead")
    return {"errors": errors, "warnings": warnings, "info": info}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill")
    ap.add_argument("--shared", nargs="*", default=[], help="folders holding your single-source rule files")
    ap.add_argument("--limit", type=int, default=250, help="description character limit")
    ap.add_argument("--max-lines", type=int, default=150)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = check(Path(a.skill).expanduser().resolve(), [Path(s) for s in a.shared], a.limit, a.max_lines)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        for e in r["errors"]:
            print(f"ERROR    {e}")
        for w in r["warnings"]:
            print(f"WARNING  {w}")
        for k, v in r["info"].items():
            print(f"INFO     {k}: {v}")
        print(f"\n{len(r['errors'])} errors, {len(r['warnings'])} warnings")
    return 1 if r["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
