# Testing old against new

A rewrite that reads better can still trigger worse. The only way to know is to run both
versions on the same inputs and count.

## tests.json

```json
{
  "skill": "linkedin-hooks",
  "phrases": [
    {"text": "give me 10 openers for this post", "should_trigger": true},
    {"text": "write a LinkedIn post about pricing", "should_trigger": false}
  ],
  "tasks": [
    {
      "prompt": "Write 5 hooks for a post about cutting our tool stack from 14 to 6.",
      "checks": [
        {"type": "regex", "value": "^\\s*1[.)]"},
        {"type": "not_contains", "value": "unlock"},
        {"type": "max_words", "value": 200}
      ]
    }
  ]
}
```

`after` is optional. Without it, the test uses the folder that `snapshot.py` copied, which is
where you made your edits.

## Writing the 18 phrases

- 9 should trigger: the quoted phrases from the description, plus paraphrases a real user would
  type, including a sloppy one with a typo.
- 9 should not trigger: near-misses that belong to a neighbor skill (take them from the
  `collide.py` output and the "do not use" line), plus a couple of unrelated requests.
- Write them before you rewrite the description, so the test is not shaped to the answer.

## Writing the 3 tasks

Pick three real jobs the skill did in the last month. Give each one a few checks a script can
decide: required text, banned words, a word limit, a format pattern. Leave out checks that need
taste. Judge those by reading the saved outputs in `<run-dir>/run-*/task-*.txt`.

## Reading the result

`results.json` holds both scores and a verdict. A tie ships. If the new version loses on either
half, go back to the description or the instructions, not to the tests.
