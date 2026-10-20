"""Importing a mod's zip: one library folder per mod, its unpacked files plus a mod.json record.

The record maps each file the game loads to where it goes in the game folder.
"""
import json
import os
import re
import shutil
import zipfile

from d4xmm.game import hlboot

RECORD = "mod.json"
AUDIO_DIR = "res/Audio"
AUDIO_EXT = (".wem", ".bnk")
PAK = re.compile(r"res\.compressed\d+\.pak$", re.IGNORECASE)
# Nexus names a download "<file name>-<mod id>-<version, dots as dashes>-<upload time>"
NEXUS_NAME = re.compile(r"^(?P<name>.+?)-(?P<id>\d+)-(?P<version>\d+(?:-\d+)*)-\d{9,}$")


class ModImportError(Exception):
    """A zip that can't become a mod: nothing in it the game loads, or two files for one place."""


def target(member):
    """Where a file from the zip goes in the game folder; None for files the game doesn't load."""
    parts = member.split("/")
    name = parts[-1]
    if PAK.match(name) or name.lower() in hlboot.FILES:
        return name
    if name.lower().endswith(AUDIO_EXT):
        folders = [p.lower() for p in parts[:-1]]
        # keep the layout under the mod's own Audio folder (Media/, English(US)/), if it has one
        start = folders.index("audio") + 1 if "audio" in folders else len(parts) - 1
        return "/".join([AUDIO_DIR] + parts[start:])
    return None


def describe(zip_path):
    """Name, Nexus mod id and version, read from the zip's file name when Nexus named it."""
    stem = os.path.splitext(os.path.basename(zip_path))[0]
    m = NEXUS_NAME.match(stem)
    if not m:
        return {"name": stem, "nexus_id": None, "version": None}
    return {"name": m["name"], "nexus_id": int(m["id"]),
            "version": m["version"].replace("-", ".")}


def _unpack(zip_path, dest):
    """Extract the zip into dest; return {game path: path in the mod folder} and the other files."""
    files, other = {}, []
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("/"):
                continue
            # zipfile drops "..", drive letters and leading slashes, so record where it really went
            written = os.path.relpath(z.extract(member, dest), dest).replace(os.sep, "/")
            where = target(written)
            if where is None:
                other.append(written)
            elif where.lower() in (k.lower() for k in files):
                raise ModImportError("two files in the zip go to %s" % where)
            else:
                files[where] = written
    if not files:
        raise ModImportError("nothing in the zip is a file the game loads")
    return files, other


def import_zip(zip_path, library):
    """Unpack a mod's zip into its library folder, replacing an earlier import of the same mod.

    Returns the record written to mod.json.
    """
    info = describe(zip_path)
    folder = os.path.join(library, re.sub(r"[^\w.-]+", "_", info["name"]).strip("_.") or "mod")
    staging = folder + ".importing"
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    try:
        files, other = _unpack(zip_path, staging)
    except (ModImportError, zipfile.BadZipFile):
        shutil.rmtree(staging, ignore_errors=True)  # best effort; the error below is what matters
        raise
    record = dict(info, source=os.path.basename(zip_path), files=files, other=other)
    with open(os.path.join(staging, RECORD), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.replace(staging, folder)
    return record
