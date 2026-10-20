# Design

A mod manager for Dune: Spice Wars. It finds mods on Nexus, keeps them in a library folder the user
picks, installs any chosen set into the game, and merges content mods so they work together.

## The game folder

Found from Steam's library list (the `common\D4X` folder), and the user can change it. A mod changes
the game by adding these files:

| File | Where | Notes |
|---|---|---|
| `res.compressed1.pak` (2, 3, …) | game root | Loaded after `res.compressed.pak` in number order. A later pak overwrites any asset an earlier one also has. Holds `data.cdb` |
| `hlboot.dat`, `hlbootdx.dat` | game root | Game code: OpenGL and DirectX. The manager never edits them; it only backs them up and restores them |
| `.wem`, `.bnk` | `res/Audio` | WWise audio, copied in as-is |

`data.cdb` is a CastleDB file: JSON, `sheets` → `columns` + `lines`. The base game has 909 sheets
and 1,562 rows in `trait`.

## Library

One folder chosen by the user. Each mod gets a subfolder: the unpacked zip, plus a small record of
its Nexus id, version and file list. Installing never moves anything out of the library.

## Getting mods

1. **Browse** in the app through Nexus's public API, with no key needed (checked live: it lists the
   game's mods with name, summary, picture and download count).
2. **Download** opens the mod's Files page in the user's browser.
3. Then one of two ways in:
   - **Watched folder:** the manager watches the Downloads folder (filled in from Windows, user can
     change it) and offers to import a new zip that matches a mod. A zip can also be imported by hand.
   - **"Download with mod manager" button** (optional): the manager registers as the handler for
     Nexus's `nxm://` links. It needs the user's personal API key, pasted once from their Nexus account
     page. There is no login screen. Windows allows one handler at a time, so this can take over from
     Vortex. Registering is an opt-in button.

Before a public release, the app is registered with Nexus (support@nexusmods.com), as their API
policy asks.

## Installing

The user ticks mods and orders them. **Lower in the list = loaded later = wins.**

1. **Merge** (see below) into one `res.compressed1.pak`. One mod with no `data.cdb` clash still goes
   through the same path, so there is only one way in.
2. **Back up** `hlboot.dat`, `hlbootdx.dat` and every game file the install would overwrite, byte for
   byte. Warn if an hlboot file carries a known mod mark (`spineTargets`, the mark CodeCracker uses),
   because then the backup isn't the stock game.
3. **Write the install record**, then copy the files in (pak to the root, audio to `res/Audio`). The
   record holds each file's path, its hash before, and the hash we left there.

**Removing all mods** goes through the record: a file we added is deleted, a file we overwrote gets
its backup back, and both hlboot files are restored. The game is back to its base state. A file whose
hash is no longer the one we left (for example after a Steam update) is left alone and reported.

## Merging (splicing)

For each mod, in load order:

1. Unpack its pak with QuickBMS (`d4x_res_pak.bms`) into a temp folder.
2. **Assets:** copy into one merged folder; a later mod overwrites the same path.
3. **data.cdb:** diff it against the base game's `data.cdb`, then apply the diff to the merged
   result. Sheets match by name, rows by their `id` column, and fields one by one. So two mods that
   change different fields of the same row both keep their changes, and on the same field the later
   mod wins. New rows and new sheets are added.

Then build the pak with the game's own `pakBuild.hl`, run by the player's `D4X.exe`, as
`!repackage.ps1` in D4XEditor does. The `-diff` flag it passes is not understood yet.

**Trait limit:** the game crashes with more than 2,048 rows in `trait`. The base game has 1,562. The
merge counts them and shows a warning before installing, with an info note that this is a limit of
the game, not the manager.

## Shipping

One Windows `.exe` built with PyInstaller. It bundles QuickBMS and `pakBuild.hl`, but not the game's
runtime: it uses the player's `D4X.exe`.

The window is **pywebview**: HTML pages in a native window, as in CodeCracker's app.

## Not decided yet

- **Rows with no `id`**, and rows deleted by a mod: how the merge treats them.
- **Licensing:** whether QuickBMS and `pakBuild.hl` may be bundled.
- **The first tests** use small controlled mods built for the purpose, before any real Nexus mod.
