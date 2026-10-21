"""Installing the chosen library mods: merge their paks into one, then put every file in place."""
import json
import os
import shutil
import tempfile

from d4xmm import merge
from d4xmm.game import hlboot
from d4xmm.install import deploy
from d4xmm.library import mods as library


def _gather(library_dir, folders):
    """Split the chosen mods' files into paks to merge and the rest, in load order.

    Returns ([(mod name, game path, pak path)], {game path: source}, {game path: [mod names]}).
    """
    paks, files, owners = [], {}, {}
    for folder in folders:
        root = os.path.join(library_dir, folder)
        with open(os.path.join(root, library.RECORD), encoding="utf-8") as f:
            record = json.load(f)
        for where, rel in record["files"].items():
            src = os.path.join(root, *rel.split("/"))
            if library.PAK.match(where):
                paks.append((record["name"], where, src))
            else:
                files[where] = src  # a later mod replaces the same path
                owners.setdefault(where, []).append(record["name"])
    return paks, files, owners


def install_mods(game_dir, state_dir, library_dir, folders):
    """Merge and install the mods in folders, in load order; one alone goes in as shipped.
    Returns the merge's report (None unmerged), who ships each file, clashes, what restore skipped.
    A merge over the trait cap installs nothing.
    """
    paks, files, owners = _gather(library_dir, folders)
    if len(folders) == 1:
        files.update({where: src for _, where, src in paks})
        paks = []
    work = tempfile.mkdtemp()
    try:
        report = {"merge": None, "owners": owners, "hlboot_modded": [], "skipped": [],
                  "clashes": merge.clashes(owners)}
        if paks:
            m = report["merge"] = merge.merge([(name, src) for name, _, src in paks], game_dir,
                                              os.path.join(work, "merge"))
            files[os.path.basename(m["pak"])] = m["pak"]
            report["clashes"] = merge.clashes(owners, m["owners"], m["rows"])
            if m.get("traits_over"):
                return report  # the game crashes on startup with it, so the game is left untouched
        # merged first, so a merge that fails leaves the earlier install in place
        report["skipped"] = deploy.restore(game_dir, state_dir)
        report["hlboot_modded"] = hlboot.modded(game_dir)
        deploy.install(game_dir, state_dir, files)
        return report
    finally:
        shutil.rmtree(work, ignore_errors=True)  # temp files only; a leftover costs disk, not data
