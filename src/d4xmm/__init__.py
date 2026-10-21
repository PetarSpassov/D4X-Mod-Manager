"""D4X Mod Manager: installs, merges and removes Dune: Spice Wars mods."""
import os

NAME = "D4X Mod Manager"
__version__ = "0.1.0"
COMPILED = "__compiled__" in globals()  # Nuitka sets it in every module it compiles
# built by Nuitka, vendor/ sits beside this package; run from source, beside src/
VENDOR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      *([".."] if COMPILED else ["..", ".."]), "vendor"))
