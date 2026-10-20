"""Unpacking a pak with the QuickBMS we ship in vendor/quickbms."""
import os
import subprocess

EXE = "quickbms_4gb_files.exe"
SCRIPT = "d4x_res_pak.bms"
TIMEOUT = 600
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                     "vendor", "quickbms"))


def unpack(pak, dest, only=None):
    """Unpack pak, or only the files matching `only`, into dest, which must not exist yet.

    Returns every file's path relative to dest. A fresh dest keeps QuickBMS from asking.
    """
    if os.path.exists(dest):
        raise FileExistsError(dest)
    os.makedirs(dest)
    pick = ["-f", only] if only else []
    cmd = [os.path.join(TOOLS, EXE)] + pick + [os.path.join(TOOLS, SCRIPT), pak, dest]
    # given a console of its own, QuickBMS turns to GUI mode and waits for ENTER until it crashes
    run = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                         stdin=subprocess.DEVNULL, timeout=TIMEOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    files = sorted(os.path.relpath(os.path.join(root, f), dest).replace("\\", "/")
                   for root, _, names in os.walk(dest) for f in names)
    # QuickBMS exits 0 on a wrong signature, so an empty result counts as a failure too.
    if run.returncode != 0 or not files:
        raise RuntimeError("QuickBMS failed on %s: %s" % (pak, (run.stdout + run.stderr)[-500:]))
    return files
