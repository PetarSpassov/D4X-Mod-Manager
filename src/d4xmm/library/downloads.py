"""Archives in the Downloads folder that are Dune: Spice Wars mods from Nexus, not yet imported.

A browser gives a download Nexus's name (<name>-<mod id>-<version>-<time>) only once complete.
"""
import json
import os
import re

from d4xmm.nexus import files as nexus_files

NEXUS_NAME = re.compile(r"-\d+(-.+)?-\d{9,}\.(zip|7z|rar)$", re.IGNORECASE)
DISMISSED = "dismissed_downloads.json"  # under state/: archives imported or turned down


def dismissed(state_dir):
    path = os.path.join(state_dir, DISMISSED)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(state_dir, names):
    with open(os.path.join(state_dir, DISMISSED), "w", encoding="utf-8") as f:
        json.dump(names, f, indent=1)


def dismiss(state_dir, name):
    names = dismissed(state_dir)
    if name not in names:
        _save(state_dir, names + [name])


def _forget_missing(state_dir, present):
    """Drop the names no longer in the folder, so the same archive downloaded again is offered."""
    names = dismissed(state_dir)
    kept = [n for n in names if n in present]
    if kept != names:
        _save(state_dir, kept)
    return kept


def _answer(name, known, lookup):
    """Nexus's record of name, None when it isn't this game's; known keeps the answers."""
    if name not in known:
        try:
            known[name] = lookup(name)
        except (nexus_files.Offline, nexus_files.Refused):
            return None  # no answer is not a no: not kept, so the next look asks again
    return known[name]


def offers(folder, imported, state_dir, known, lookup=None):
    """[{file, name, version}] for each new Dune mod archive in folder, oldest first; imported
    and dismissed names are skipped. known: {name: Nexus's answer}, kept by the caller."""
    if not folder or not os.path.isdir(folder):
        return []
    lookup = lookup or nexus_files.lookup  # looked up at call time, so a test can patch it
    present = os.listdir(folder)
    skip = set(imported) | set(_forget_missing(state_dir, set(present)))
    names = [n for n in present if NEXUS_NAME.search(n) and n not in skip]
    out = []
    for name in sorted(names, key=lambda n: os.path.getmtime(os.path.join(folder, n))):
        found = _answer(name, known, lookup)
        if found:
            out.append({"file": name, "name": found["mod_name"], "version": found["version"]})
    return out
