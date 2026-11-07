# Running the steps by hand

For when Python or the `claude` CLI is unavailable. Same seven steps, same order.

1. **Rank.** Search your chat history or tool logs for each skill name and write the counts down.
   Without logs, list the ten skills you remember using most.
2. **Snapshot.** Copy the skill folder to `<work>/before/` before you change anything.
3. **Check.** Count the description's characters. Look for quoted phrases and a "do not use"
   line. Open every link in the skill and confirm the file exists. Read the descriptions of
   neighboring skills for the same phrases.
4. **Rewrite the description** with [the description guide](description-guide.md).
5. **One home per rule set.** Search the skill for text you recognize from your voice guide or
   brand rules. Replace each copy with a link to the original file.
6. **Scripts and gotchas.** List every counting rule. Write down each real failure as a gotcha.
7. **Test.** Open two fresh chats, one with each version installed. Paste the same 18 phrases
   and 3 tasks into both and tally which version picked the skill correctly and which passed
   more checks. If the new one loses, it does not ship.

Tell the user that the run was manual, so the counts are less reliable than a scripted run.
