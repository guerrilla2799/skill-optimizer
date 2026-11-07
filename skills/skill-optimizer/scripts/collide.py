#!/usr/bin/env python3
"""Step 4: find trigger phrases that more than one skill claims.

Reads every quoted phrase in every description under --roots. EXACT means two skills quote
the same phrase. NEAR means the phrases share the same content words in a different order.
Either one means the model has to guess which skill you meant.

Usage: collide.py --roots DIR [DIR ...] [--focus NAME] [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _skillfile import find_skills, parse_frontmatter  # noqa: E402

STOP = set("the a an and or of to for in on at is it this that with your you we our my me do does what how when which who".split())


def norm(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())


def content_words(s: str) -> frozenset:
    return frozenset(w for w in norm(s).split() if w not in STOP)


def collisions(descs: dict[str, str]) -> dict:
    owners: dict[str, set] = collections.defaultdict(set)
    for name, d in descs.items():
        for q in re.findall(r"\"([^\"]{3,90})\"", d):
            owners[norm(q)].add(name)
    exact = {p: sorted(o) for p, o in owners.items() if len(o) > 1}
    bykey: dict[frozenset, set] = collections.defaultdict(set)
    for p, os_ in owners.items():
        k = content_words(p)
        if len(k) >= 2:
            for o in os_:
                bykey[k].add((o, p))
    near = []
    for v in bykey.values():
        if len({o for o, _ in v}) > 1 and len({p for _, p in v}) > 1:
            near.append(sorted(v))
    return {"phrases": len(owners), "exact": exact, "near": near}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--focus", help="only report collisions involving this skill")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    descs = {}
    for name, path in find_skills(a.roots).items():
        d = parse_frontmatter(path.read_text(errors="ignore")).get("description")
        if d:
            descs[name] = d
    r = collisions(descs)
    if a.focus:
        r["exact"] = {p: o for p, o in r["exact"].items() if a.focus in o}
        r["near"] = [v for v in r["near"] if any(o == a.focus for o, _ in v)]
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        print(f"{len(descs)} descriptions, {r['phrases']} quoted phrases")
        for p, o in sorted(r["exact"].items()):
            print(f"EXACT  \"{p}\"  {', '.join(o)}")
        for v in r["near"]:
            print("NEAR   " + "  |  ".join(f"{o}: \"{p}\"" for o, p in v))
        if not r["exact"] and not r["near"]:
            print("No collisions.")
    return 1 if (r["exact"] or r["near"]) else 0


if __name__ == "__main__":
    sys.exit(main())
