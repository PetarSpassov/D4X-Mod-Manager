"""Unpacking a pak with the QuickBMS we ship in vendor/quickbms."""
import os
import subprocess

EXE = "quickbms_4gb_files.exe"
SCRIPT = "d4x_res_pak.bms"
TIMEOUT = 600
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                     "vendor", "quickbms"))


def unpack(pak, dest):
    """Unpack pak into dest, which must not exist yet; returns every file's path relative to dest.

    A fresh dest keeps QuickBMS from stopping to ask whether to overwrite.
    """
    if os.path.exists(dest):
        raise FileExistsError(dest)
    os.makedirs(dest)
    cmd = [os.path.join(TOOLS, EXE), os.path.join(TOOLS, SCRIPT), pak, dest]
    run = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                         stdin=subprocess.DEVNULL, timeout=TIMEOUT)
    files = sorted(os.path.relpath(os.path.join(root, f), dest).replace("\\", "/")
                   for root, _, names in os.walk(dest) for f in names)
    # QuickBMS exits 0 on a wrong signature, so an empty result counts as a failure too.
    if run.returncode != 0 or not files:
        raise RuntimeError("QuickBMS failed on %s: %s" % (pak, (run.stdout + run.stderr)[-500:]))
    return files
