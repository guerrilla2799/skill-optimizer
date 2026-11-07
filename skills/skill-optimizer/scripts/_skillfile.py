"""Shared helpers: find skills and read their frontmatter without a YAML dependency."""
from __future__ import annotations

import re
from pathlib import Path

FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse the top-level keys of a SKILL.md frontmatter block.

    Handles plain values, quoted values, and folded or literal blocks (>, >-, |, |-).
    Nested maps are skipped. This covers what skill loaders read: name and description.
    """
    m = FRONT.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not km:
            i += 1
            continue
        key, val = km.group(1), km.group(2).strip()
        if val in (">", ">-", "|", "|-", ">+", "|+"):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            sep = "\n" if val.startswith("|") else " "
            out[key] = sep.join(b for b in block if b).strip()
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if val:
            out[key] = val
        i += 1
    return out


def body(text: str) -> str:
    m = FRONT.match(text)
    return text[m.end():] if m else text


def find_skills(roots: list[str]) -> dict[str, Path]:
    """Map skill name -> SKILL.md path for every <root>/<skill>/SKILL.md."""
    found: dict[str, Path] = {}
    for root in roots:
        r = Path(root).expanduser()
        for p in sorted(r.glob("*/SKILL.md")):
            name = parse_frontmatter(p.read_text(errors="ignore")).get("name") or p.parent.name
            found.setdefault(name, p)
    return found
