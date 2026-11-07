# Writing the description

The description is the only part of a skill the model reads before it decides whether to use
it. Every installed skill's description loads on every request, so it costs tokens even when
the skill never runs. Write it for the model that has to choose, not for a person browsing a list.

## The four parts

1. **When to use it.** Start with "Use when" and the situation, in the user's terms.
2. **The exact phrases.** Two to four things the user actually types, in quotes. Take them from
   real transcripts when you can. `collide.py` reads these quotes, so a phrase without quotes
   is invisible to the collision check.
3. **What it returns.** One short clause: "Drafts the SOW plus its cover email."
4. **When not to use it.** Name the neighbor skill that owns the near-miss case:
   "Do NOT use for hooks (linkedin-hooks)." This line settles most misroutes.

Keep the whole thing at 250 characters or fewer. Some tools cut long descriptions off, and the
cut usually lands on the "do not use" line, which is the part that prevents misroutes.

## Before and after

Before (long, no phrases, no boundary):

> A comprehensive skill for creating high-quality LinkedIn content including posts, carousels,
> and comments, following best practices for engagement and brand voice consistency across...

After (184 characters):

> Use when a LinkedIn post, comment, or carousel needs drafting. Phrases: "write a LinkedIn
> post", "rewrite this post". Drafts in your voice. Do NOT use for first lines (linkedin-hooks).

## Checks

- `check_skill.py` errors over the limit and warns on missing quotes or a missing boundary.
- `collide.py --focus <name>` lists phrases another skill already claims. Change one of the two
  phrases, or add a "do not use" line that sends the case to the other skill.
