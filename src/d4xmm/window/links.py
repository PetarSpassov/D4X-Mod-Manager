"""Nexus's "Mod Manager Download" links (nxm://): taking them over in Windows, letting them go,
and handing a link to the window that is already open instead of opening a second one."""
import json
import os
import re
import sys
import threading
import winreg
from multiprocessing.connection import AuthenticationError, Client, Listener
from urllib.parse import parse_qs

ROOT = r"Software\Classes\nxm"  # under HKEY_CURRENT_USER: this user's, no admin rights needed
PIPE = r"\\.\pipe\D4XModManager"
AUTH = b"D4XModManager"  # keeps stray programs' messages out; not a secret
PREVIOUS = "nxm_previous.json"  # under state/: the handler taken over, put back when let go
LINK = re.compile(r"nxm://([^/]+)/mods/(\d+)/files/(\d+)\?(.+)$", re.IGNORECASE)
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def parse(url):
    """{game, mod_id, file_id, grant: {key, expires}}; ValueError when url isn't such a link."""
    found = LINK.match(url.strip())
    query = parse_qs(found.group(4)) if found else {}
    if not found or "key" not in query or "expires" not in query:
        raise ValueError("not a Nexus mod manager link: %r" % url)
    return {"game": found.group(1).lower(), "mod_id": int(found.group(2)),
            "file_id": int(found.group(3)),
            "grant": {"key": query["key"][0], "expires": query["expires"][0]}}


def command():
    """What Windows runs for a link: this app, with the link as its one argument."""
    if getattr(sys, "frozen", False):
        return '"%s" "%%1"' % sys.executable
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    start = "import sys; sys.path.insert(0, r'%s'); from d4xmm.window.app import main; main()"
    return '"%s" -c "%s" "%%1"' % (pythonw, start % SRC)


def _read(root):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root + r"\shell\open\command") as k:
            return winreg.QueryValue(k, None)
    except FileNotFoundError:
        return None  # no handler of this user's


def _write(root, run):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, root) as k:
        winreg.SetValue(k, None, winreg.REG_SZ, "URL:NXM Protocol")
        winreg.SetValueEx(k, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, root + r"\shell\open\command") as k:
        winreg.SetValue(k, None, winreg.REG_SZ, run)


def _delete(root):
    """root and every key under it; winreg deletes only empty keys."""
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, root) as k:
        children = [winreg.EnumKey(k, i) for i in range(winreg.QueryInfoKey(k)[0])]
    for child in children:
        _delete(root + "\\" + child)
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, root)


def _program(run):
    """The file name of the program a command runs."""
    first = run[1:].split('"')[0] if run.startswith('"') else run.split()[0]
    return os.path.basename(first)


def status(root=ROOT):
    """{ours: links come here; other: the program they go to instead, or None}."""
    run = _read(root)
    ours = run == command()
    return {"ours": ours, "other": _program(run) if run and not ours else None}


def take(state_dir, root=ROOT):
    """Send links here; what had them before is kept to be put back."""
    run = _read(root)
    if run and run != command():
        with open(os.path.join(state_dir, PREVIOUS), "w", encoding="utf-8") as f:
            json.dump(run, f)
    _write(root, command())


def release(state_dir, root=ROOT):
    """Give links back to the program that had them, or to no one."""
    path = os.path.join(state_dir, PREVIOUS)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            _write(root, json.load(f))
        os.remove(path)
    elif _read(root) is not None:
        _delete(root)


def send(url, pipe=PIPE):
    """Give url to the window already open; False when none is."""
    try:
        with Client(pipe, "AF_PIPE", authkey=AUTH) as conn:
            conn.send(url)
        return True
    except OSError:
        return False  # no window is listening: this start opens one


def serve(handle, pipe=PIPE):
    """Call handle(url) for each link a later start of the app sends, on a background thread;
    False when a window opened earlier already listens, and gets the links."""
    try:
        listener = Listener(pipe, "AF_PIPE", authkey=AUTH)
    except PermissionError:
        return False  # the pipe's first instance belongs to that window

    def loop():
        while True:
            try:
                with listener.accept() as conn:
                    handle(conn.recv())
            except (OSError, EOFError, AuthenticationError) as e:
                print("A link handed over was lost:", e, file=sys.stderr)
    threading.Thread(target=loop, daemon=True).start()
    return True
