---
name: skill-optimizer
description: >-
  Use when saved AI skills or prompts need a tune-up. Phrases: "optimize my skills",
  "tune up this skill", "which skills do I actually use", "test this skill against the
  old one". Ranks, repairs, tests old vs new. Do NOT use to write a new skill.
license: MIT
metadata:
  version: "1.0.0"
  author: Brandon Redlinger
---

# Skill Optimizer

Tunes up the skills you already run, most-used first, so they trigger on the right request,
cost fewer tokens to load, and get proven better before they replace the old version.

Seven steps. Scripts do the counting, the copying, and the comparing. You (the model) do the
judgment: rewriting descriptions, moving rules, writing gotchas.

`<work>` is a work folder outside the skill being tuned, default `./skill-optimizer-work/<skill>/`.
Every snapshot, report, and test file goes there. Never write work files into the target skill.

## Scripts

All are Python 3.9+ standard library. Paths are relative to this skill's folder.

- `scripts/rank_usage.py` ranks skills by how often they ran, from Claude Code transcripts or a CSV
- `scripts/snapshot.py` copies a skill to `<work>/before/` and refuses to overwrite one
- `scripts/check_skill.py` runs the countable checks on one skill: description length and shape, root size, broken links, pasted rule blocks
- `scripts/collide.py` finds trigger phrases that two skills both claim
- `scripts/trigger_test.py` runs the old and new versions against the same phrases and tasks and compares the scores

## Workflow

1. **Rank by usage.** Run `python3 scripts/rank_usage.py --roots <skill-roots...>`. Show the user the top 10 and the zero-run list. Work the top of the list first. Offer to archive zero-run skills, because every installed skill's description loads into context and competes for selection. Archive only on the user's yes, and move the folder rather than deleting it.
2. **Snapshot.** Run `python3 scripts/snapshot.py <skill-dir> <work>`. Step 7 compares against this copy, so never skip it.
3. **Check.** Run `python3 scripts/check_skill.py <skill-dir> --shared <shared-rules-dir>` and `python3 scripts/collide.py --roots <skill-roots...> --focus <name>`. Save both outputs to `<work>/check-before.txt`. These are the countable findings.
4. **Rewrite the description.** Read [the description guide](references/description-guide.md). Write one that says when to use the skill, the exact phrases the user types, what it returns, and when not to use it, in 250 characters or fewer. Re-run `collide.py`, then fix every collision it reports.
5. **One home per rule set.** Any voice guide, brand rule, or client fact pasted into the skill moves to one shared file, and the skill links to it. `check_skill.py --shared` flags the pasted blocks. Move text word for word. Never paraphrase a rule while moving it.
6. **Scripts for counting, gotchas from failures.** Anything countable in the instructions (word counts, character limits, slide counts, required fields) becomes a small script with a test. Then add a `## Gotchas` section with one line per real failure, written as "You'll want to do X. Don't, because last time Y happened." Ask the user for failures they've seen. Never invent one.
7. **Test old against new.** Read [the test guide](references/test-guide.md). Write `<work>/tests.json` with 18 phrases (9 that should trigger, 9 that should not) and 3 real tasks with pass/fail checks. Show the user the call count from `python3 scripts/trigger_test.py <work> --dry-run`, because the run uses model time. With their yes, run it with `--yes`. If the new version scores lower on either half, it does not ship. Go back to step 4.

Then run `check_skill.py` again, save it to `<work>/check-after.txt`, and give the user the before-and-after counts, the description length, both test scores, and a list of everything you moved or cut.

## Gotchas

- You'll want to delete a paragraph that looks redundant. Don't. Move it to a reference file, and list every true removal for the user to approve. Silent cuts are how skills lose the one rule that mattered.
- You'll want to judge trigger accuracy by reading the description. Don't. Run step 7. A description that reads well can still lose to a neighbor skill on the same phrase.
- `rank_usage.py` only sees what transcripts recorded. A skill can show zero runs because it ran in another tool. Ask before archiving.
- `trigger_test.py` installs each version into a scratch project. A copy of the same skill installed globally can answer instead. The script warns when it finds one, so tell the user.
- One skill per work folder. Never share `<work>` between two skills.

If Python is unavailable, read [the manual fallback](references/manual-fallback.md) and run the same seven steps by hand.
