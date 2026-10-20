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
  and has the contents of both. The other load order also works: shared files and rows "got
  flipped to the other one".
- Import looks each archive up on Nexus by exact download name (`nexus/files.py`). Seen live:
  `QuinnQuest.zip` is "not_found". A mod imported offline keeps "?" until re-imported.

- Owed, asked for, not built: mod profiles (save/load order and ticks); one ticked mod deployed
  as-is, unmerged; the Browse tab's Nexus catalog (the tab is empty).

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
  otherwise "some twisted amalgamation of the two"). After Install the window lists who overrides
  whom: rows, pak assets and loose game files, 8 items shown per pair.
- Code follows rule 12. A code file past 800 lines may only shrink.
- Pre-commit runs `codecheck.py`, which refuses only the violations a commit adds over HEAD. Function
  size, nesting, complexity, parameters and silent catches are checked in Python only.

## Untested

- Merging more than two real mods (only Community Patch + QuinnQuest, both orders, has been seen
  in the game).
- A row two mods change is the later mod's whole row. After `141b72e` the user re-merged and says
  "the merge still seems to work without issue"; whether each shared row is exactly the later mod's
  was not reported. Inference: a mod whose editor wrote a column into every row wins every row.
- After `4ce7bf7` the user says "the overrides show correctly" in the window after Install.
- A mod is named by its Nexus mod name (e.g. "Dune Spice Wars Community Patch"); offline or not on
  Nexus, by the archive name. The library folder still comes from the Nexus file name, else the
  archive name. Seen live: both `examples/` archives describe with their mod names. Not seen in the
  window. The user's library holds QuinnQuest as `QuinnQuest-5-v0-4-2-2-1780006924` (imported
  offline): an online re-import goes to `QuinnQuest`, a second entry, and no window delete exists.
- On start the window looks every mod up on Nexus again in the background (`mods.refresh`) and
  re-renders; a found mod's record takes the new name, version and ids, in its own folder. Seen
  live on a copy of the user's records: QuinnQuest and community_patch took their Nexus names and
  versions. Not seen in the window; an import or reorder while it runs is untested.
- New window layout (`window/index.html`, `style.css`, `page.js`): install status pill, Import plus
  drop archives anywhere (`app.py` hands dropped paths to `Api.import_paths`), search, drag to
  reorder, per-mod menu (Open folder, Open on Nexus, Delete with a second click), "update: X" from
  Nexus's newest main file, a "Last install" overrides panel. Api parts tested; seen live: the real
  window loads it with 4 rows and the pill "Installed" (installed before `last_install.json`
  existed). Drag and the menu seen only in a browser preview with a fake Api. File drop, delete,
  open folder/Nexus and the update note: not seen in the window.
- Tabs Installed / Browse / Settings replace the header. Settings holds the game folder and the
  Downloads folder (typed or Choose…; empty means found from Steam / Windows' Shell Folders), kept
  in `settings.json`. No `D4X.exe` there: Settings shows an error and Install and Remove all refuse
  with "Can't find the game in the Steam directory. Please adjust it in Settings." Rows read
  "Name v1.2 by Uploader" (Nexus uploader name, as the user's example "PeterQuinn98"); a click opens
  the Nexus picture and summary. Api parts tested; tabs, settings error and the open row seen only in
  a browser preview with a fake Api. Not seen in the window: Choose…, typed folders, pictures.
  After `32ddf18` the user reports: a second click on an open mod doesn't close it; moving an open
  mod collapses everything; dragging past the first/last mod stops it being put down; the install
  log never disappears and is bulky; "Last install" looks out of place; the scrollbar is white.
- Changed for that: mods are separate cards; a second click closes a row and an open row stays open
  when moved; a drag anywhere above the first or below the last row drops there; the open row adds
  downloads, endorsements and last updated (seen live from Nexus for QuinnQuest: 1226, 29,
  2026-05-28). Install shows one line ("Installed." fades; with notes or an error it stays, with ×)
  and "Last install: N notes, N overrides" in the footer opens a panel. Themed scrollbar. Seen only
  in a browser preview with a fake Api; real mouse drags and the scrollbar not seen at all.
  After `3790943` the user reports: dragging a mod far down works, far up still does not; "Click
  again to delete" stays after the menu is closed and reopened; the tabs jitter when clicked.
  Changed for that: a dragged row's drop and edge scroll now work over the whole page (the toolbar
  above the list included); closing the menu disarms Delete; all tabs share one weight. Settings
  has a Nexus API key field (kept as typed in `settings.json`, unused by any lookup so far) and no
  folder hint. Seen in a browser preview with a fake Api with synthetic drag events; not by mouse.
- A trial the user may drop: the ⋯ menu is replaced by three icons per row (folder, open on Nexus,
  bin). The bin turns red on the first click and deletes on the second; any other click disarms
  it. Seen only in a browser preview with a fake Api.
- The window reopens where it closed, maximised if it was. Seen live: closed maximised, settings.json
  kept `"width": 860, "height": 640, "maximized": true`; reopened, closed untouched, the same again.
  Un-maximising after a restart, and a second monitor, not seen.
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
