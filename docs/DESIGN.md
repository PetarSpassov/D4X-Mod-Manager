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

One folder chosen by the user. Each mod gets a subfolder: the unpacked zip, plus `mod.json` with its
Nexus id and version (read from a Nexus file name, `<name>-<id>-<version>-<time>.zip`) and where
each file goes. Installing never moves anything out of the library. Import sorts files by name:

| In the zip | Goes to |
|---|---|
| `res.compressed<N>.pak`, `hlboot.dat`, `hlbootdx.dat`, in any folder | game root |
| `.wem`, `.bnk` | `res/Audio/`, keeping the layout under the zip's own `Audio` folder if it has one |
| anything else | kept, listed as "other", not installed |

A zip with nothing the game loads, or two files for one place, is refused. Re-importing a mod
replaces its old copy. Zip, 7z and rar are all unpacked by the 7-Zip in `vendor/7zip`.

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

Installing over an earlier install restores that one first, after the merge, so a failed merge
leaves the earlier install in place. For files other than paks, the later mod wins.

**Removing all mods** goes through the record: a file we added is deleted, a file we overwrote gets
its backup back, and both hlboot files are restored. The game is back to its base state. A file whose
hash is no longer the one we left (for example after a Steam update) is left alone and reported.

## Merging (splicing)

For each mod, in load order:

1. Unpack its pak with QuickBMS (`d4x_res_pak.bms`) into a temp folder.
2. **Assets:** copy into one merged folder; a later mod overwrites the same path.
3. **data.cdb:** diff it against the base game's `data.cdb` (pulled fresh from
   `res.compressed.pak` on every merge, about a second), then apply the diff to the merged
   result. Sheets match by name, rows by their `id` column, and fields one by one. So two mods that
   change different fields of the same row both keep their changes, and on the same field the later
   mod wins. New rows, columns and sheets go after the item that precedes them in the mod, below
   any other mod's additions already there, never at the end by default: the game needs lines in
   place. `trait`'s `Count` row is put back last; `attribute`'s is not.
   A sheet's `props` are taken whole, the later mod winning. Its `separators` (categories) merge
   by row id: each mod's new ones are kept, ones it removed or renamed go, and all are sorted into
   row order. For now, rows a mod
   deletes are kept and reported, rows with no `id` are counted and skipped, and a mod's reordering
   of existing rows or sheets is not carried over.

Then build the pak with the game's own `pakBuild.hl`, run by the player's `D4X.exe`, as
`!repackage.ps1` in D4XEditor does. We pass `-res <merged folder> -out res.compressed1`, but not the
`-diff` that script passes: in a folder with no pak it built the same pak without it.

**Trait limit:** the game crashes with more than 2,048 rows in `trait`. The base game has 1,562. The
merge counts them and shows a warning before installing, with an info note that this is a limit of
the game, not the manager.

## Shipping

One zip of a Nuitka `--standalone` folder, as CodeCracker builds but not `--onefile`: Nuitka
compiles our code to C, and a folder keeps the licences beside the exe.

```
D4XModManager/
  D4XModManager.exe   + the runtime files Nuitka puts beside it
  vendor/             QuickBMS, d4x_res_pak.bms, pakBuild.hl
  licences/           QuickBMS's GPL text and source, the README credits
```

It does not bundle the game's runtime: it uses the player's `D4X.exe`.

The window is **pywebview**: HTML pages in a native window, as in CodeCracker's app.

## Not decided yet

- **Rows deleted by a mod:** whether to delete them (kept and reported for now). The base game has
  no rows without an `id`.
- **Licensing:** whether `pakBuild.hl` and `d4x_res_pak.bms` may be bundled. QuickBMS may: GPL 2.0,
  shipped with its licence text and source.
- **The first tests** use small controlled mods built for the purpose, before any real Nexus mod.
