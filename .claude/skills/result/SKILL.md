---
name: result
description: The user reported a test result (passed, failed, "I tested X", what they saw) - update the docs BEFORE replying. Run it every time; it is the step most often skipped.
---

## A reported result updates the docs first, in this same turn

The trigger is any of: "it worked", "it failed", "I tested", or a description of what happened.

1. **Re-read anything the user says changed.** State what you actually found, not what you expected.
2. **`► LAST KNOWN GOOD`** in `docs/HANDOFF.md` `## State`: update it only when the user's own words
   call this version good, and quote them. That line is the only record of it.
3. **`► WE ARE ON`**: if the work is finished, move it with `python .claude/tools/on.py "<next>"`, or
   `"nothing; awaiting direction"`. Never leave finished work as current.
4. **`## Untested`**: remove the cases this result covered, in their words, and add the ones it does not.
5. **A symptom, not a verdict.** Write what they saw. No "by design", "expected" or "not a fault" in the
   turn the report arrived.
6. **A new trap goes to `docs/GOTCHAS.md`** in the three-line format.
7. **Run `python .claude/tools/doccheck.py`** and fix what it names.

Then reply. Say which case passed and which did not. The user closes items, not you.

## When the news is a failure

Read the evidence yourself before theorising: the log, the error, the output. A crash says that
something failed, not why. Change one thing per experiment.
