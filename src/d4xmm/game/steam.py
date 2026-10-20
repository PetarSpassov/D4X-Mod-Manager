"""Where Steam installed Dune: Spice Wars, read from Steam's own files."""
import os
import re
import winreg

GAME_NAME = "Dune: Spice Wars"
PAIR = re.compile(r'"([^"]+)"\s+"([^"]*)"')


def _pairs(path):
    """Every quoted key and value in a Steam text file, in file order."""
    with open(path, encoding="utf-8", errors="replace") as f:
        return [(k, v.replace("\\\\", "\\")) for k, v in PAIR.findall(f.read())]


def steam_dir():
    """Steam's own folder, from the registry; None when Steam is not installed."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            return os.path.normpath(winreg.QueryValueEx(k, "SteamPath")[0])
    except OSError:
        return None


def libraries(steam):
    """Every Steam library folder, Steam's own first."""
    out = [steam]
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    if os.path.isfile(vdf):
        out += [os.path.normpath(v) for k, v in _pairs(vdf) if k == "path"]
    return list(dict.fromkeys(out))


def game_folder(library):
    """The game's folder in one library, from its manifest; None when it is not there."""
    apps = os.path.join(library, "steamapps")
    if not os.path.isdir(apps):
        return None
    for name in os.listdir(apps):
        if name.startswith("appmanifest_") and name.endswith(".acf"):
            fields = dict(_pairs(os.path.join(apps, name)))
            if fields.get("name") == GAME_NAME:
                return os.path.join(apps, "common", fields.get("installdir", ""))
    return None


def find():
    """The game's folder as Steam knows it; None when Steam or the game is not found."""
    steam = steam_dir()
    if not steam:
        return None
    for lib in libraries(steam):
        folder = game_folder(lib)
        if folder and os.path.isdir(folder):
            return folder
    return None
