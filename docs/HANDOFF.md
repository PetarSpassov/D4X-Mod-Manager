# Handoff

Only what is true now. History lives in git; traps go to `GOTCHAS.md`. A commit that changes the tools
or rules must change this file too (pre-commit).

## State

**► WE ARE ON:** design doc written (docs/DESIGN.md); next: window toolkit decision, then the install/restore core *(moved only by `python .claude/tools/on.py`)*

**► LAST KNOWN GOOD:** none yet *(only the user names this, in their own words; it lives here and nowhere else)*

**Open threads:** none.

## Standing decisions

- A change turn needs the user's message to start with "Go". Anything else is an answer turn: propose and stop.
- No hook sends a reply back after the user has seen it. Stop only records.
- No question boxes with buttons. The next step goes in the reply text. `noask.py` refuses
  `AskUserQuestion` and a wrap-up with a question or buttons, unless the user's message this turn says
  "questions are allowed". It fails closed.
- No mid-turn text: only the opening line and the final reply. postgate flags each one; it can't block.
- Replies: 700 prose characters, 1,800 when asked to explain. Code blocks and tables are free.
- The host's task list is kept on multi-step turns, nudged by a turn-start line on "Go" turns, not a CLAUDE.md rule.
- `CLAUDE.md` is capped at 7,000 characters (doccheck). Adding a rule means cutting or merging as much elsewhere, named in the commit message.
- The root `README.md` is the project's. The ClaudeStarter README lives at `.claude/README.md`.
- Code follows rule 12. A code file past 800 lines may only shrink.
- Pre-commit runs `codecheck.py`, which refuses only the violations a commit adds over HEAD. Function
  size, nesting, complexity, parameters and silent catches are checked in Python only.

## Untested

- `merge/pak.py` on a full-size merged folder: only a one-file pak has been built, and no game has
  loaded a pak we built.
- `merge.merge()` on real mods: only two tiny mods built in the tests have been merged.
- Row placement (each mod's rows where the mod had them, below earlier mods') in a game: tests only.
