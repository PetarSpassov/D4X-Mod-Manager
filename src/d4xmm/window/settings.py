"""The user's settings, kept in settings.json under the home folder: folders and window placement.

A folder not set yet is filled in from Steam or Windows each time, and saved only once changed.
"""
import json
import os
import winreg

from d4xmm.game import steam

FILE = "settings.json"
GAME_EXE = "D4X.exe"
FOLDERS = ("game_dir", "downloads")
SHELL_FOLDERS = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
DOWNLOADS_ID = "{374DE290-123F-4565-9164-39C4925E467B}"  # Windows's id for the Downloads folder


def downloads_dir():
    """The user's Downloads folder as Windows has it, even when moved to another drive."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, SHELL_FOLDERS) as k:
            return os.path.normpath(winreg.QueryValueEx(k, DOWNLOADS_ID)[0])
    except OSError:  # no entry: the folder sits where Windows puts it by default
        return os.path.join(os.path.expanduser("~"), "Downloads")


def game_ok(folder):
    """True when folder holds the game's executable."""
    return bool(folder) and os.path.isfile(os.path.join(folder, GAME_EXE))


def window_args(saved, screens):
    """create_window's width, height, x, y and maximized from a saved placement.

    A place whose title bar is on no screen now (a monitor unplugged) is dropped: it opens centred.
    """
    saved = saved or {}
    out = {"width": saved.get("width", 860), "height": saved.get("height", 640),
           "maximized": bool(saved.get("maximized"))}
    x, y = saved.get("x"), saved.get("y")
    if x is not None and y is not None:
        bar_x, bar_y = x + out["width"] // 2, y + 10
        if any(s.x <= bar_x < s.x + s.width and s.y <= bar_y < s.y + s.height for s in screens):
            out.update(x=x, y=y)
    return out


def _saved(home):
    path = os.path.join(home, FILE)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(home):
    """{game_dir, downloads, window}: saved values, the two folders found when not saved."""
    saved = _saved(home)
    return {"game_dir": saved.get("game_dir") or steam.find(),
            "downloads": saved.get("downloads") or downloads_dir(),
            "window": saved.get("window")}


def save(home, **changes):
    """Keep changes on top of what is saved; an empty folder goes back to being found."""
    saved = dict(_saved(home), **changes)
    with open(os.path.join(home, FILE), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in saved.items() if v}, f, indent=1)
