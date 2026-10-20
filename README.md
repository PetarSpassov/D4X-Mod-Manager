# D4X Mod Manager

A mod manager for **Dune: Spice Wars**. It imports mods from their zips, installs any chosen set
in load order, merges content mods so they work together, and puts the game back as it was.

Work in progress: import, merge, install and restore exist, with a first window that is not yet
tried on real mods. The design is in [docs/DESIGN.md](docs/DESIGN.md).

## Open the app

Double-click `!app.bat` in this folder. It needs Python 3 with `pywebview` installed.

## Run the tests

Windows, Python 3:

```
set PYTHONPATH=src
python -m unittest discover -s tests -t .
```

## Credits

D4X Mod Manager ships these third-party tools in `vendor/`, unchanged:

| Tool | By | Licence |
|---|---|---|
| QuickBMS 0.12.0 (`quickbms_4gb_files.exe`, `quickbms.txt`) | Luigi Auriemma, [aluigi.org](https://aluigi.org) | GPL 2.0: `LICENSE`, source in `quickbms-src-0.12.0.zip` |
| `d4x_res_pak.bms` | Sanctus-Susanin, from an original by Allen | not stated |
| `pakBuild.hl` | taken from D4XEditor | not stated |

Working with Claude Code on this repo: see [.claude/README.md](.claude/README.md).
