"""Run with: python3 -m unittest discover -s tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import _skillfile  # noqa: E402
import check_skill  # noqa: E402
import collide  # noqa: E402
import rank_usage  # noqa: E402
import snapshot  # noqa: E402
import trigger_test  # noqa: E402

SHARED_RULE = ("Never use the words unlock, leverage, or supercharge in any copy. They read as filler "
               "to experienced buyers and they flag the draft as machine-written.")


def make_skill(root: Path, name: str, desc: str, body: str = "# Skill\n") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: >-\n  {desc}\n---\n{body}")
    return d


class Frontmatter(unittest.TestCase):
    def test_folded_description(self):
        fm = _skillfile.parse_frontmatter('---\nname: x\ndescription: >-\n  one\n  two\nlicense: MIT\n---\nbody')
        self.assertEqual(fm, {"name": "x", "description": "one two", "license": "MIT"})

    def test_quoted_value(self):
        self.assertEqual(_skillfile.parse_frontmatter('---\ndescription: "a: b"\n---\n')["description"], "a: b")

    def test_no_frontmatter(self):
        self.assertEqual(_skillfile.parse_frontmatter("# just a doc"), {})


class Rank(unittest.TestCase):
    def test_counts_and_zero_runs(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "a.jsonl").write_text(
                '{"name":"Skill","input":{"skill":"alpha"}}\n{"name":"Skill","input":{"skill":"plug:alpha"}}\n'
                '<command-name>/beta</command-name>\n')
            r = rank_usage.rank(rank_usage.count_transcripts(t), ["alpha", "beta", "gamma"])
            self.assertEqual(r["ranked"], [{"skill": "alpha", "runs": 2}, {"skill": "beta", "runs": 1}])
            self.assertEqual(r["zero_runs"], ["gamma"])


class Snapshot(unittest.TestCase):
    def test_refuses_second_snapshot(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            s = make_skill(t, "s", "d")
            snapshot.snapshot(s, t / "work")
            self.assertTrue((t / "work/before/SKILL.md").is_file())
            self.assertEqual((t / "work/source.txt").read_text().strip(), str(s))
            with self.assertRaises(SystemExit):
                snapshot.snapshot(s, t / "work")


class Check(unittest.TestCase):
    def test_long_description_is_an_error(self):
        with tempfile.TemporaryDirectory() as t:
            s = make_skill(Path(t), "s", "x" * 300)
            r = check_skill.check(s, [], 250, 150)
            self.assertTrue(any("300 characters" in e for e in r["errors"]))

    def test_good_description_passes(self):
        with tempfile.TemporaryDirectory() as t:
            s = make_skill(Path(t), "s", 'Use when X. Phrases: "fix my hook". Do NOT use for posts.')
            self.assertEqual(check_skill.check(s, [], 250, 150)["errors"], [])

    def test_broken_link_and_counting_rule(self):
        with tempfile.TemporaryDirectory() as t:
            s = make_skill(Path(t), "s", '"a b c". Do not.', "See [guide](references/missing.md). Keep it under 200 words.\n")
            r = check_skill.check(s, [], 250, 150)
            self.assertTrue(any("broken link" in e for e in r["errors"]))
            self.assertTrue(any("under 200 words" in w for w in r["warnings"]))

    def test_pasted_shared_rule(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "shared").mkdir()
            (t / "shared/voice.md").write_text(SHARED_RULE + "\n")
            s = make_skill(t, "s", '"a b c". Do not.', "\n" + SHARED_RULE + "\n")
            r = check_skill.check(s, [t / "shared"], 250, 150)
            self.assertTrue(any("pasted copy" in w for w in r["warnings"]))


class Collide(unittest.TestCase):
    def test_exact_and_near(self):
        r = collide.collisions({
            "a": 'Phrases: "fix my hook", "write the post".',
            "b": 'Phrases: "fix my hook", "post the write".',
        })
        self.assertIn("fix my hook", r["exact"])
        self.assertEqual(len(r["near"]), 1)

    def test_no_collision(self):
        r = collide.collisions({"a": '"fix my hook"', "b": '"write a post"'})
        self.assertEqual((r["exact"], r["near"]), ({}, []))


class Trigger(unittest.TestCase):
    def test_detects_skill_call(self):
        ev = {"message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "plug:alpha"}}]}}
        self.assertTrue(trigger_test.triggered(json.dumps(ev) + "\nnot json\n", "alpha"))
        self.assertFalse(trigger_test.triggered(json.dumps(ev), "beta"))

    def test_checks(self):
        out = "Here is the draft, ten words or so in total here."
        self.assertTrue(trigger_test.apply_check({"type": "contains", "value": "DRAFT"}, out))
        self.assertTrue(trigger_test.apply_check({"type": "max_words", "value": 12}, out))
        self.assertFalse(trigger_test.apply_check({"type": "not_contains", "value": "draft"}, out))
        with self.assertRaises(ValueError):
            trigger_test.apply_check({"type": "nope"}, out)

    def test_score_and_verdict(self):
        phrases = [{"should_trigger": True}, {"should_trigger": False}]
        before = trigger_test.score([True, True], phrases, [[True, False]])
        after = trigger_test.score([True, False], phrases, [[True, True]])
        self.assertEqual(before["phrases_correct"], 1)
        self.assertEqual(trigger_test.verdict(before, after), "SHIP")
        self.assertEqual(trigger_test.verdict(after, before), "DO NOT SHIP")
        self.assertEqual(trigger_test.verdict(before, before), "SHIP")  # a tie ships

    def test_dry_run_counts_calls(self):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            s = make_skill(t, "s", "d")
            snapshot.snapshot(s, t / "w")
            (t / "w/tests.json").write_text(json.dumps({"skill": "s", "phrases": [{"text": "a"}] * 18, "tasks": [{"prompt": "p"}] * 3}))
            self.assertEqual(trigger_test.main([str(t / "w"), "--dry-run"]), 0)


if __name__ == "__main__":
    unittest.main()
