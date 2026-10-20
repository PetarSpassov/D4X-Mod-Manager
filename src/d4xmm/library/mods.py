"""Importing a mod's archive: one library folder per mod, its unpacked files plus a mod.json record.

The record maps each file the game loads to where it goes in the game folder.
"""
import json
import os
import re
import shutil
import subprocess

from d4xmm.game import hlboot

SEVEN_ZIP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                         "vendor", "7zip", "7z.exe"))
TIMEOUT = 600
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


def _extract(archive, dest):
    """Extract any archive 7-Zip reads into dest; return the files written, relative, with /."""
    os.makedirs(dest)
    run = subprocess.run([SEVEN_ZIP, "x", "-y", "-bso0", "-bsp0", "-o" + dest, archive],
                         capture_output=True, text=True, errors="replace",
                         stdin=subprocess.DEVNULL, timeout=TIMEOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW)  # no console from pythonw
    if run.returncode != 0:
        raise ModImportError("7-Zip could not unpack %s: %s"
                             % (os.path.basename(archive), run.stderr.strip()[-300:]))
    # 7-Zip drops "..", drive letters and leading slashes, so list what it really wrote
    return sorted(os.path.relpath(os.path.join(root, f), dest).replace(os.sep, "/")
                  for root, _, names in os.walk(dest) for f in names)


def _unpack(archive, dest):
    """Extract into dest; return {game path: path in the mod folder} and the other files."""
    files, other = {}, []
    for written in _extract(archive, dest):
        where = target(written)
        if where is None:
            other.append(written)
        elif where.lower() in (k.lower() for k in files):
            raise ModImportError("two files in the archive go to %s" % where)
        else:
            files[where] = written
    if not files:
        raise ModImportError("nothing in the archive is a file the game loads")
    return files, other


def import_archive(archive, library):
    """Unpack a mod's zip, 7z or rar into its library folder, replacing an earlier import of it.

    Returns the record written to mod.json.
    """
    info = describe(archive)
    folder = os.path.join(library, re.sub(r"[^\w.-]+", "_", info["name"]).strip("_.") or "mod")
    staging = folder + ".importing"
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    try:
        files, other = _unpack(archive, staging)
    except ModImportError:
        shutil.rmtree(staging, ignore_errors=True)  # best effort; the error below is what matters
        raise
    record = dict(info, source=os.path.basename(archive), files=files, other=other)
    with open(os.path.join(staging, RECORD), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.replace(staging, folder)
    return record
