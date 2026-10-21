# Handoff

Only what is true now. History lives in git; traps go to `GOTCHAS.md`. A commit that changes the tools
or rules must change this file too (pre-commit).

## State

**► WE ARE ON:** exe packaged (Nuitka/Zig, build/ zips) and the Nexus email drafted; next: the user tests the exe, then sends the email *(moved only by `python .claude/tools/on.py`)*

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

- The exe from `!build.bat` (Nuitka with Zig, standalone folder `build/D4XModManager`, 81 MB).
  Seen live: it builds, starts, and opens a window titled "D4X Mod Manager". Untested in it: the
  page itself, `vendor/` found (`d4xmm.VENDOR`, `COMPILED`), import, merge, and the nxm handler.
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
  Asked: the update badge should get the update. Changed: it is a button; Premium downloads the
  newest main file with progress in the status line, Free opens the Files page. Any version of
  the same Nexus mod imports into the folder already holding it (`_same_mod`), keeping its place
  and tick; the pill compares each ticked mod's archive too, so an update reads "changed". An
  install refused over the trait cap no longer records itself as the last install. Tested with
  fakes; the badge not seen.
  The user reports: "Nexus lists no such file to download for this mod" is long enough to push
  Install down to the left. Changed: the footer no longer wraps; the status wraps inside its own
  box. Seen in a browser preview at 900px: one row, Install at the right. Not seen in the window.
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
- After `29ad90e` the user reports: dragging a mod up moves it, but no drop bar shows, unlike
  dragging down. The bar above the first row sat in the list's clipped top edge; the list now has
  6px above it. Not seen since.
- The window reopens where it closed, maximised if it was. Seen live: closed maximised, settings.json
  kept `"width": 860, "height": 640, "maximized": true`; reopened, closed untouched, the same again.
  Un-maximising after a restart, and a second monitor, not seen.
- Mod profiles (`window/profiles.py`, `profiles.json`): each its own order and ticks; every change
  goes to the active one. Toolbar: picker, + (a copy of the current one, named inline), bin (two
  clicks; not on the last). A new import is ticked in the active profile, unticked in others. The
  old `order.json` is read once as "Default"; seen live: the user's reads as QuinnQuest ticked,
  community_patch not. Switching doesn't install. UI seen only in a browser preview, fake Api.
  After `c93029c` the user reports: the dropdown's arrow sits too far right; the dropdown is sharp
  and blocky against the rounded style; the selected profile shows in all white; Import jumps when
  a new profile is being named; the mod tickboxes are small, hard to hit between the handle and
  the row's click-to-open, and blue. After `2ca5a1c`: the field's border doesn't match the
  other shapes; the list it opens is square, and its hover is white, not a soft highlight.
  Now our own picker (`window/profiles.js`): a button styled like the others and a rounded list,
  row hover, the active profile in beige. Seen only in a browser preview with a fake Api.
  After `8ac1665` the user reports: the bins' red is too aggressive; mod rows use another bin
  icon than profiles; the folder icon feels flat; the profile bin stays red after a delete; the
  picker changes width with the name; the focused "New profile name" border isn't the app's colour.
  Changed: a darker rust red, one bin icon, a folder drawn open, bins disarm when they delete, a
  170px picker, accent focus borders on every text field. Preview only.
  After `26a463f` the user reports: shrinking the window narrows the cards but not the search
  box, which reaches the window's edge; truncated grey row text ends in a white "…"; the New
  profile name field still gets no accent border when focused. Changed: search shrinks (seen in
  preview at 560px: its right edge matches the cards'), name and meta cut with their own "…",
  the profile field's focus rule outranks its own border rule, rows unfold and fold (~0.15s).
  After `0fba8c1` the user reports: shrinking the window turns mod names into "…" though they
  lose no room. Changed: the name never shrinks; it is cut only once the grey details are gone
  (seen in a scratch page with the real stylesheet: at 250px the name keeps 170.344 of 170.344px).
  After `1cb9fd8` the user says "Looks good now".
- Browse lists Nexus's mods for the game, most downloaded first (`nexus/catalog.py`, `browse.js`):
  picture, name, version, creator, stats, two lines of summary, Download (opens the Files tab) or
  "in library" with Files. Search and Reload. Seen live from Nexus: 7 mods, paging works at 3 a
  page. Seen in a browser preview with a fake Api: the cards, search, Download's call. Not seen in
  the window: the tab, the browser opening, offline and refused messages.
  After `75003af` the user says "Looks good", and reports: Files plus "in library" make widths
  uneven; summaries are cut off. Asked: open a card for more (tags, full text), a reload icon, a
  tag filter that includes and excludes. Changed: one 96px Download on every card, "✓ In library"
  on the picture; a click opens the card: tags (a click filters), dates, the full description as
  text (`catalog.plain`); reload and funnel icons; the menu cycles a tag: only, hidden, off.
  Seen in a browser preview with a fake Api and live Nexus data: equal buttons, the filter counts
  (Gameplay: 2 of 7, hidden 5 of 7), the menu staying open. Not seen in the window.
  After `b1fa41f` the user says "This is looking great". Asked: a sort (downloads, endorsements,
  last updated, A to Z) behind an up/down arrows icon; the open card's text formatted as on Nexus.
  Changed: sort menu; `nexus/bbcode.py` turns the BBCode into escaped HTML (bold, italic, sizes,
  colours, lists, links, images, spoilers); links open in the browser (`open_link`, web only).
  Seen in the preview: each sort's order, the markup made, a link click calling open_link and the
  page staying put. Not seen: how it looks next to Nexus's page, light theme with authors' colours.
  After `8e4fa83` the user reports: many spaces and newlines don't show; on QuinnQuest no line
  break between "COMPATIBILITY" and "NOTE:". Found: each "\n<br />" was dropped whole, the "\n"
  with it. Changed: only the "<br />" goes. Seen in a test only, not in the window.
- The window and taskbar icon is `window/logo.ico` (the user's, moved from the root; one 256px
  image), set through `webview.start(icon=)` with our own taskbar id. Not seen in the window.
  Owed: the same icon on the exe, when there is one.
- The Downloads folder is watched (`library/downloads.py`, `offers.js`): every 5s the page asks
  for archives named as Nexus names downloads, not imported or dismissed, that Nexus confirms are
  this game's (asked once per name; offline asks again). A bar under the tabs offers each:
  Import (ticked at the end, as any import) or × (never again, `state/dismissed_downloads.json`).
  Tested with fakes; seen in a browser preview: offers, ×, Import. Not seen: a real download.
  Not built: the optional nxm:// "Download with mod manager" handler (needs the API key).
  After `c74c467` the user says "Looks great". Asked: look every 1s; an imported archive must not
  be offered again once its mod is deleted. Changed: a look starts 1s after the last one ends;
  every import (offered, picked or dropped) records the archive's name as handled. The archive
  stays in Downloads, untouched. Tested; not seen in the window.
  Asked: a deleted archive downloaded again must be offered again. Changed: each look forgets
  the recorded names no longer in the folder (imported and ×'d alike). A mod still in the
  library is not offered again under the same archive name. Tested; not seen in the window.
- The Nexus key (`nexus/account.py`, v1 REST API): checked when typed and at start; Settings says
  "Signed in as X · Premium/Free", or that it isn't accepted, or that Nexus couldn't be reached.
  "Get my key" opens nexusmods.com/settings/api-keys (where the old account-page address now
  redirects; the page itself not seen). Premium: Download fetches the newest main file (`.part`,
  renamed whole), imports it, then puts the zip in Downloads, recorded so it isn't offered. Free
  or no key: Download opens the Files page as before. Seen live: a wrong key gets 401 from both
  key check and download link. Tested with fakes; seen in a browser preview with a fake Premium
  Api: the account line, "Downloading…", the error in the Browse toolbar. Not seen: a real key,
  a real download, a free account's answer (403 assumed). No progress bar: one "Downloading…".
  Asked: "Get my key" should land at the "Personal API Key" heading. Changed: the address ends
  in a text fragment (`#:~:text=Personal%20API%20Key`). Signed out, the page has no such heading
  or id to read (seen in the preview browser); whether the browser scrolls there is not seen.
  The user, with a real Premium key, says "The app doesn't work with Premium yet": the
  "Downloading…" text leaves its box; nothing says what the download is doing; Dyaus Anchor's
  Download shows "Dyaus Anchor: URL can't contain control characters. '/cdn/7811/2/dsw Dyaus
  Anchor v1.22-2…" (the address has spaces). Changed in `a6f423d`: the address is escaped
  before fetching; the button says "Wait…" and the card's summary line shows "Asking Nexus…",
  "Downloading: X MB of Y MB", "Importing…" (asked every 0.5 s). After `a6f423d` the user says
  "It downloads now, the progress text shows". Asked: a green "Installed!" for 5 s on success.
  Changed: the card's summary line shows it for OK_SECONDS. Asked then: "Added to library." in
  its place (a download doesn't install) and "Working…" for "Wait…". Changed; not seen.
- Nexus's "Mod Manager Download" links (`window/links.py`): Settings → "Use this app" writes
  this user's nxm handler (HKCU\Software\Classes\nxm) to start the app with the link, keeping
  the old command in `state/nxm_previous.json`; "Give back" restores it (or removes ours). Seen
  live: this machine's handler before is `nxmhandler.exe` (Mod Organizer's). A start with a link
  hands it to the open window over a named pipe and exits; with none open, the window opens and
  downloads it. The link's key and expires go with the download-link request (needs the API key).
  Tested: parsing, registry take/give back on a throwaway key, the pipe handover, the download
  with fakes; the handler's command line run with a sample link. Not seen: a real click on Nexus,
  the Settings line. A second window opened normally doesn't get links; the first keeps them.
  Found after: every Dune mod and the game say `supportsVortex: false`, and the user sees no
  "Mod Manager Download" on its pages, so no link reaches the handler for now.
- Nexus API policy (help.nexusmods.com/article/114): every request now carries Application-Name
  "D4X Mod Manager" and Application-Version (`d4xmm.__version__`, 0.1.0), seen accepted live.
  The key is checked only when typed or when Download is pressed, never at start. A personal key
  is allowed only while testing: a public release needs registration, then Nexus's SSO slug.
  Repo is private on GitHub (404 signed out). Licence: MIT, the user's choice (`LICENSE`, in the
  root where GitHub looks). `pakBuild.hl` holds `hxd.fmt.pak.Build` (Heaps, MIT, by its class
  names), shipped with Heaps' notice in `vendor/pakbuild/LICENSE`. Copyright "Petar Spassov".
  `d4x_res_pak.bms` is from github.com/Sviat/qbms_shirogames (`northgard_res_pak.bms`, same
  header): use is free if all authors' names stay and the repo is linked; the link is now added
  to the script's header; `test_unpacks_files_under_their_folders` still passes with it.
  After `cbb1f29` the user reports: the icon at the top of the window "seems quite mangled".
  Changed: `logo.ico` now holds 16, 20, 24, 32, 40, 48, 64 and 256px, each shrunk from the 256px
  one (Pillow, Lanczos, a one-off run, not a project dependency); the 256-only file is in
  `todelete/`. The 16 and 32px frames look clean as images; not seen in the window.
- One ticked mod is installed as shipped: its paks and files copied, no merge (`install/flow.py`).
  Tested with a fake library only; not seen in the game.
- Row placement and merged separators as seen in the CastleDB editor after a real merge.
- What the window reports when data.cdb couldn't carry rows over, or `trait` passes 16384 rows
  (the cap after the game's patch, per the user): a red error naming each mod's added traits;
  any other note stays green. Over the cap nothing is installed; the earlier install stays.
- The test mods from `tests/merge/make_test_mods.py` (`build/test_mods/`) in the game, alone or
  merged. Their paks hold only data.cdb and two test files; whether the game takes a pak that small,
  and a trait column it doesn't know (`d4xmmNote`), is unknown.
- 7z and rar import from the window's file dialog: tested through `import_archive` only (a 7z
  built by 7-Zip, a rar built by WinRAR). Seen live: both `examples/` mods import into a temp library.
- The "?" version and its tooltip in the window, and a real offline import: unit tests only.
- The window (`!app.bat`, or `python -m d4xmm.window.app`; home `%LOCALAPPDATA%\D4XModManager`): how it looks and
  every button. Only its Api is tested; seen live, it stays open 8 s with no error.
