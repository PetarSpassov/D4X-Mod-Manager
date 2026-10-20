"""Unpacking a pak with the QuickBMS that ships in the game's QuickBMS folder."""
import os
import subprocess

EXE = "quickbms_4gb_files.exe"
SCRIPT = "d4x_res_pak.bms"
TIMEOUT = 600


def tool_dir(game):
    """The game's QuickBMS folder; None when the exe or the script is missing."""
    folder = os.path.join(game, "QuickBMS")
    ok = all(os.path.isfile(os.path.join(folder, n)) for n in (EXE, SCRIPT))
    return folder if ok else None


def unpack(pak, dest, tools):
    """Unpack pak into dest, which must not exist yet; returns every file's path relative to dest.

    A fresh dest keeps QuickBMS from stopping to ask whether to overwrite.
    """
    if os.path.exists(dest):
        raise FileExistsError(dest)
    os.makedirs(dest)
    cmd = [os.path.join(tools, EXE), os.path.join(tools, SCRIPT), pak, dest]
    run = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                         stdin=subprocess.DEVNULL, timeout=TIMEOUT)
    files = sorted(os.path.relpath(os.path.join(root, f), dest).replace("\\", "/")
                   for root, _, names in os.walk(dest) for f in names)
    # QuickBMS exits 0 on a wrong signature, so an empty result counts as a failure too.
    if run.returncode != 0 or not files:
        raise RuntimeError("QuickBMS failed on %s: %s" % (pak, (run.stdout + run.stderr)[-500:]))
    return files
