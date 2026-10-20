"""Putting files into the game and taking them back out. The record keeps each path's hash before
and the hash we left, so restore undoes only what is still ours, never a later Steam update.
"""
import hashlib
import json
import os
import shutil

from d4xmm.game import hlboot

RECORD = "install.json"
BACKUP = "backup"


class InstallError(Exception):
    """An install that can't start because an earlier one is still in place."""


def sha256(path):
    """The file's SHA-256 as hex; None when there is no file."""
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _copy(src, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)


def install(game_dir, state_dir, files):
    """Copy files ({path inside the game: source file}) in, backing up what they replace.

    Both hlboot files are backed up even when no mod replaces them. Returns the record.
    """
    if os.path.exists(os.path.join(state_dir, RECORD)):
        raise InstallError("an install is already in place; restore it first")
    targets = dict.fromkeys(hlboot.FILES)
    targets.update(files)
    record = []
    for rel, src in targets.items():
        dest = os.path.join(game_dir, rel)
        before = sha256(dest)
        if before:
            _copy(dest, os.path.join(state_dir, BACKUP, rel))
        left = sha256(src) if src else before
        if left:
            record.append({"path": rel, "before": before, "left": left})
    # written before any copy, so an install cut short can still be restored
    with open(os.path.join(state_dir, RECORD), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)
    for rel, src in files.items():
        _copy(src, os.path.join(game_dir, rel))
    return record


def restore(game_dir, state_dir):
    """Undo the install in place. Returns the paths left alone because they changed since."""
    path = os.path.join(state_dir, RECORD)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        record = json.load(f)
    skipped = []
    for entry in record:
        dest = os.path.join(game_dir, entry["path"])
        now = sha256(dest)
        if now == entry["before"]:
            continue
        if now != entry["left"]:
            skipped.append(entry["path"])
        elif entry["before"]:
            _copy(os.path.join(state_dir, BACKUP, entry["path"]), dest)
        else:
            os.remove(dest)
    os.remove(path)
    if os.path.isdir(os.path.join(state_dir, BACKUP)):
        shutil.rmtree(os.path.join(state_dir, BACKUP))
    return skipped
