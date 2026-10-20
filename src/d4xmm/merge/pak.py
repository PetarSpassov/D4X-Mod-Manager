"""Building the merged pak with pakBuild.hl, run by the player's own D4X.exe."""
import os
import subprocess

OUT = "res.compressed1"
TIMEOUT = 1800
PAKBUILD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                        "vendor", "pakbuild", "pakBuild.hl"))


def build(folder, game_dir):
    """Pack everything under folder into res.compressed1.pak beside it; returns the pak's path.

    pakBuild.hl writes the pak into its working folder, so that is folder's parent.
    """
    exe = os.path.join(game_dir, "D4X.exe")
    if not os.path.isfile(exe):
        raise FileNotFoundError(exe)
    work, name = os.path.split(os.path.abspath(folder))
    pak = os.path.join(work, OUT + ".pak")
    if os.path.exists(pak):
        raise FileExistsError(pak)
    cmd = [exe, PAKBUILD, "-res", name, "-out", OUT]
    run = subprocess.run(cmd, cwd=work, capture_output=True, text=True, errors="replace",
                         stdin=subprocess.DEVNULL, timeout=TIMEOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW)  # no console pops up
    if run.returncode != 0 or not os.path.isfile(pak):
        raise RuntimeError("pakBuild failed on %s: %s" % (folder, (run.stdout + run.stderr)[-500:]))
    return pak
