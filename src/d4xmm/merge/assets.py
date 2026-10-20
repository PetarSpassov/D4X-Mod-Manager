"""Combining the unpacked assets of several mods: the mod loaded later wins a shared path."""
import os
import shutil

CDB = "data.cdb"  # merged row by row instead, so never copied whole


def _files(folder):
    """Every file under folder, as a forward-slash path relative to it."""
    return sorted(os.path.relpath(os.path.join(root, f), folder).replace("\\", "/")
                  for root, _, names in os.walk(folder) for f in names)


def combine(mods, dest):
    """Copy each (name, unpacked folder) into dest in load order; dest must not exist yet.

    Returns {path: [names of the mods that ship it]}; the last name is the one kept.
    """
    if os.path.exists(dest):
        raise FileExistsError(dest)
    owners = {}
    for name, folder in mods:
        for path in _files(folder):
            if path == CDB:
                continue
            target = os.path.join(dest, *path.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(os.path.join(folder, *path.split("/")), target)
            owners.setdefault(path, []).append(name)
    return owners
