# D4X Mod Manager

A mod manager for **Dune: Spice Wars**. It imports mods from their zip, 7z or rar, installs any chosen set
in load order, merges content mods so they work together, and puts the game back as it was.

Work in progress: import, merge, install and restore work from the window, and merges of real mods
(Community Patch with QuinnQuest) boot the game. The design is in [docs/DESIGN.md](docs/DESIGN.md).

This project is written with an AI coding assistant (Claude Code); its working rules are in
`CLAUDE.md` and [.claude/README.md](.claude/README.md).

## Open the app

Double-click `!app.bat` in this folder. It needs Python 3 with `pywebview` installed.

## Run the tests

Windows, Python 3:

```
set PYTHONPATH=src
python -m unittest discover -s tests -t .
```

## What it touches

For anyone reviewing the code: everything the app reads, writes, runs or sends, and where.

| What | Where | Code |
|---|---|---|
| Network | Only `api.nexusmods.com` (mod lookups, key check, download links) and the download address Nexus returns. Images in mod descriptions load from where the author hosts them. | `src/d4xmm/nexus/` |
| Nexus API key | Typed by the player, sent only to Nexus in the `apikey` header, saved as plain text in the settings file below | `nexus/account.py`, `window/settings.py` |
| Its own files | `%LOCALAPPDATA%\D4XModManager`: settings, the mod library, backups of replaced game files | `window/app.py` |
| Game folder | Writes the installed files; restore puts back each backup and removes only files it installed, leaving any changed since | `install/deploy.py` |
| Registry, read | Steam's install path and the Downloads folder, under the current user | `game/steam.py`, `window/settings.py` |
| Registry, written | The `nxm` link handler, under the current user, only when the player turns on Nexus links; the handler it replaced is kept and put back when turned off | `window/links.py` |
| Programs run | `7z.exe` to unpack archives; `quickbms_4gb_files.exe` to unpack paks; the game's own `D4X.exe` (a HashLink runtime) running `pakBuild.hl` to build the merged pak. No console, no shell. | `library/mods.py`, `merge/unpack.py`, `merge/pak.py` |

## Credits

D4X Mod Manager ships these third-party tools in `vendor/`. Check the binaries against your own
copy from the official source with `certutil -hashfile <file> SHA256`.

| Tool | By | Licence | SHA-256 |
|---|---|---|---|
| QuickBMS 0.12.0 (`quickbms_4gb_files.exe`, `quickbms.txt`), from [aluigi.org](https://aluigi.org/quickbms.htm) | Luigi Auriemma | GPL 2.0: `LICENSE`, source in `quickbms-src-0.12.0.zip` | exe `3a248ab5f9f1dae7b999b4098cb623372ae29ebaefbb72f8c359cf3b72d2b5a7`<br>source zip `e96794af8369fdcb6dd4744e126cc82bda22329153359c756a4c70b44fd6b328` |
| `d4x_res_pak.bms`, from `northgard_res_pak.bms` in [Sviat/qbms_shirogames](https://github.com/Sviat/qbms_shirogames) | Sanctus-Susanin, from an original by Allen | any use keeping the authors' names and a link to that repository; credited in the script's header | `315e93521a61112c445d7081b15f94c4461544371ba6f58f9c43332813d517f9` |
| `pakBuild.hl`, taken from D4XEditor: HashLink bytecode of `hxd.fmt.pak.Build`, the pak builder of [Heaps](https://github.com/HeapsIO/heaps) | Nicolas Cannasse and Heaps' contributors | MIT: `vendor/pakbuild/LICENSE` | `538ca99de22135f4e7521bd083cb26dc3b1fdf3e25ce1ad753b0defa771e2b0d` |
| 7-Zip 26.04 (`7z.exe`, `7z.dll`), from the official x64 installer at [7-zip.org](https://www.7-zip.org) | Igor Pavlov | GNU LGPL with the unRAR restriction: `License.txt` | exe `95fff19b73eff77c87c0d7bd32822e43fb90dd2932459f962eb532d8dfb6ba53`<br>dll `899cd73d7fc60e1c1c35c7de0f5bed3dc69bfe2cecbd48014d868a347970a0b1` |

D4X Mod Manager itself is MIT: see `LICENSE`.
