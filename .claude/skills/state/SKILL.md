---
name: state
description: Orient at the start of a session or after a /clear or compaction - print where the project is, then read only the one thing we are on.
---

## Orient, cheaply, in this order

1. The session briefing (`=== PROJECT STATE ===`) is already in context when the session started
   normally. If it is not, run `python .claude/tools/briefing.py`. Don't go looking for those facts by hand.
2. If the user refers to anything said before a /clear ("as we discussed", "pick up from there", a
   pronoun with nothing to point at), run `python .claude/tools/prevconvo.py`.
3. Read only what the WE ARE ON line names. Then run `python .claude/tools/rules.py <thing>` for each
   thing you are about to touch.

## Do not

* Do not read `docs/GOTCHAS.md` or the HANDOFF log whole. Search the log with `grep -n`.
* Do not restate the state back to the user; they can see it. Say what you will do next, and do it.
* Do not open by asking what to do. Ask only if the WE ARE ON line and the journal disagree, and say how.
