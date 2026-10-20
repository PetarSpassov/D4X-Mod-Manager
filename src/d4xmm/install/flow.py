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

    Returns ([(mod name, pak path)], {game path: source}, {game path: [mod names]}).
    """
    paks, files, owners = [], {}, {}
    for folder in folders:
        root = os.path.join(library_dir, folder)
        with open(os.path.join(root, library.RECORD), encoding="utf-8") as f:
            record = json.load(f)
        for where, rel in record["files"].items():
            src = os.path.join(root, *rel.split("/"))
            if library.PAK.match(where):
                paks.append((record["name"], src))
            else:
                files[where] = src  # a later mod replaces the same path
                owners.setdefault(where, []).append(record["name"])
    return paks, files, owners


def install_mods(game_dir, state_dir, library_dir, folders):
    """Merge and install the library mods in folders, in load order, replacing any earlier install.

    Returns what the merge reported, which mods ship each other file, and what restore left alone.
    """
    paks, files, owners = _gather(library_dir, folders)
    work = tempfile.mkdtemp()
    try:
        report = {"merge": None, "owners": owners, "hlboot_modded": [], "skipped": []}
        if paks:
            report["merge"] = merge.merge(paks, game_dir, os.path.join(work, "merge"))
            files[os.path.basename(report["merge"]["pak"])] = report["merge"]["pak"]
        # merged first, so a merge that fails leaves the earlier install in place
        report["skipped"] = deploy.restore(game_dir, state_dir)
        report["hlboot_modded"] = hlboot.modded(game_dir)
        deploy.install(game_dir, state_dir, files)
        return report
    finally:
        shutil.rmtree(work, ignore_errors=True)  # temp files only; a leftover costs disk, not data
