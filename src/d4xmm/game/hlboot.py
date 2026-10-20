"""The game's code files, one per renderer. The manager never edits them, only backs them up."""
import os

FILES = ("hlboot.dat", "hlbootdx.dat")  # OpenGL, DirectX
# texts CodeCracker writes into the builds it makes; a backup carrying one isn't the stock game
MOD_MARKS = (b"spineTargets", b"SpiceWarsBuild: made by the app")


def modded(game_dir):
    """The hlboot files in the game folder that carry a known mod mark."""
    out = []
    for name in FILES:
        path = os.path.join(game_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        if any(mark in data for mark in MOD_MARKS):
            out.append(name)
    return out
