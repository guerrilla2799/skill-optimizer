# Skill Optimizer

**A Claude Code skill that tunes up the skills you already run, most-used first.**

Every skill you install costs tokens on every request, because its description loads whether
the skill runs or not. Bloated descriptions, rules pasted into ten places, and skills nobody
uses all pay that cost, and the model picks the wrong skill more often.

I run about 200 skills and saved prompts. When I opened 13 of them, each had between 7 and 13
errors. This is the process I now run on them, packaged so you can run it on yours.

---

## The seven steps

1. **Rank by usage.** `rank_usage.py` counts how often each skill ran in your Claude Code
   transcripts and lists the ones with zero recorded runs. Fix the top 10 first. Archive the
   zero-run skills so they stop loading on every request.
2. **Save a copy.** `snapshot.py` copies the skill before you touch it and refuses to overwrite
   that copy. Step 7 needs it.
3. **Check the countable things.** `check_skill.py` measures the description, the size of
   SKILL.md, broken links, rule blocks pasted from your shared files, and counting rules left
   in prose. `collide.py` finds trigger phrases that two skills both claim.
4. **Rewrite the description.** When to use it, the exact phrases you type, what it returns,
   and when not to use it, in 250 characters or fewer.
5. **Give every rule set one home.** Your voice guide, brand rules, and client facts each live in
   one file, and skills link to it. Shorter skills load fewer tokens, and an update to the voice
   guide reaches every skill at once.
6. **Move counting into scripts, and write gotchas from real failures.** The model miscounts
   words and characters. A short script doesn't. Each gotcha reads "You'll want to do X. Don't,
   because last time Y happened."
7. **Test old against new.** `trigger_test.py` runs both versions against 18 phrases (9 should
   trigger, 9 shouldn't) and 3 real tasks with pass/fail checks. If the new version scores
   lower, it doesn't ship.

The model does the judgment work (rewrites, moves, gotchas). The scripts count the runs and
characters and score both versions, so the result doesn't depend on the model's guess.

---

## Install

```bash
git clone https://github.com/guerrilla2799/skill-optimizer.git
mkdir -p ~/.claude/skills
cp -r skill-optimizer/skills/skill-optimizer ~/.claude/skills/
```

Start a new Claude Code session and say "optimize my skills" or "tune up my linkedin-hooks skill".

For Codex or another agent that reads `SKILL.md` folders, copy the same folder into that
agent's skills directory.

## Requirements

- Python 3.9 or later. The scripts use the standard library only.
- The `claude` CLI, for step 7 only. Step 7 makes 2 calls per phrase and task (42 for the
  standard 18 + 3), and it won't run until you pass `--yes`.
  `--dry-run` prints the count, and the skill shows you that count and asks before it runs.

No Python? `references/manual-fallback.md` walks the same seven steps by hand.

## Run the scripts yourself

```bash
cd ~/.claude/skills/skill-optimizer
python3 scripts/rank_usage.py --roots ~/.claude/skills
python3 scripts/snapshot.py ~/.claude/skills/my-skill ~/skill-optimizer-work/my-skill
python3 scripts/check_skill.py ~/.claude/skills/my-skill --shared ~/my-rules
python3 scripts/collide.py --roots ~/.claude/skills --focus my-skill
python3 scripts/trigger_test.py ~/skill-optimizer-work/my-skill --dry-run
```

Tests: `python3 -m unittest discover -s skills/skill-optimizer/tests`

## License

MIT licensed. Fork it and use it in your own work.

Built by [Brandon Redlinger](https://www.stackandscale.ai). More AI workflows for marketing
leaders at [Stack & Scale](https://www.stackandscale.ai).
