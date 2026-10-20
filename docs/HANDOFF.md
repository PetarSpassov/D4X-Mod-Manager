# Handoff

Only what is true now. History lives in git; traps go to `GOTCHAS.md`. A commit that changes the tools
or rules must change this file too (pre-commit).

## State

**► WE ARE ON:** backend joined: install_mods() merges and installs library mods (install/flow.py); next: the pywebview window *(moved only by `python .claude/tools/on.py`)*

**► LAST KNOWN GOOD:** `42ea256`: "Both show the right version, merging them boots the game correctly
and has the contents of both. This is a great success, it seems the merge is working for now."
(Community Patch + QuinnQuest) *(only the user names this, in their own words; it lives here and nowhere else)*

**Open threads:**
- After `0122881` the user reports "the installation works now" (Install of D4XMM_Test1 and _Test2
  from the window). In the editor they saw the test mods' custom attribute row above `Invalid`
  "so the attributes broke"; custom attributes go below `Invalid`. Test mods not yet changed.
- The user says `constant` and `attribute` have baked row indices and crash the game if shuffled;
  `trait` and `quest` do not (keep trait rows above `Count`). 45 sheets carry `hasIndex`, 31
  `hasGroup` (separator ordinals compiled in); which of them bake literal indices is not yet read.
- At `42ea256` the user merged Community Patch (`examples/community_patch-1-0-1-4-1760743071.7z`)
  and QuinnQuest (`examples/QuinnQuest-5-v0-4-2-2-1780006924.zip`) from the window: the game boots
  and has the contents of both. After re-import both show the right version (v0.4.2.2, 0.1.4).
  In the other load order it also works: the user checked the rows and files the two mods share,
  and both the overlapping files and the descriptions/values "got flipped to the other one".
- Import looks each archive up on Nexus by exact download name (`nexus/files.py`). Seen live:
  `QuinnQuest.zip` is "not_found". A mod imported offline keeps "?" until re-imported.

Debt: the no-console `subprocess.run` is now written three times (unpack, pak, mods).

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
- data.cdb rows two mods change: the later mod's whole row wins, never a mix of values (the user:
  otherwise "some twisted amalgamation of the two"). A clash list in the window is proposed, not built.
- Code follows rule 12. A code file past 800 lines may only shrink.
- Pre-commit runs `codecheck.py`, which refuses only the violations a commit adds over HEAD. Function
  size, nesting, complexity, parameters and silent catches are checked in Python only.

## Untested

- Merging more than two real mods (only Community Patch + QuinnQuest, both orders, has been seen
  in the game).
- A row two mods change is the later mod's whole row: unit tests only, not yet merged in the game.
  Inference: a mod whose editor wrote a new column into every row would win every row it touched.
- Row placement and merged separators as seen in the CastleDB editor after a real merge.
- What the window reports when data.cdb couldn't carry rows over, or `trait` passes 2048 rows.
- The test mods from `tests/merge/make_test_mods.py` (`build/test_mods/`) in the game, alone or
  merged. Their paks hold only data.cdb and two test files; whether the game takes a pak that small,
  and a trait column it doesn't know (`d4xmmNote`), is unknown.
- 7z and rar import from the window's file dialog: tested through `import_archive` only (a 7z
  built by 7-Zip, a rar built by WinRAR). Seen live: both `examples/` mods import into a temp library.
- The "?" version and its tooltip in the window, and a real offline import: unit tests only.
- The window (`!app.bat`, or `python -m d4xmm.window.app`; home `%LOCALAPPDATA%\D4XModManager`): how it looks and
  every button. Only its Api is tested; seen live, it stays open 8 s with no error.
