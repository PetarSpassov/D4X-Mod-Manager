"""What the window's page can ask for: the mod list and its order, import, install and settings.

Under one home: library/ (mods), state/ (install record, backups), order.json, settings.json.
"""
import json
import os
import webbrowser

from d4xmm.install import deploy, flow
from d4xmm.library import mods
from d4xmm.nexus import files as nexus_files
from d4xmm.window import settings

ORDER = "order.json"
LAST = "last_install.json"  # under state/: the folders installed and who overrode whom
NEXUS_PAGE = "https://www.nexusmods.com/dunespicewars/mods/%d"
NO_GAME = "Can't find the game in the Steam directory. Please adjust it in Settings."


class Api:
    """pywebview hands the page every public attribute, so all but the calls start with _."""

    def __init__(self, home, pick_archives=None, pick_folder=None):
        """pick_archives() returns the chosen paths, pick_folder(start) one folder or None."""
        self._home, self._pick_archives, self._pick_folder = home, pick_archives, pick_folder
        self._library = os.path.join(home, "library")
        self._state_dir = os.path.join(home, "state")
        for folder in (self._library, self._state_dir):
            os.makedirs(folder, exist_ok=True)

    def _records(self):
        """{library folder: its mod.json record} for every imported mod."""
        out = {}
        for folder in sorted(os.listdir(self._library)):
            path = os.path.join(self._library, folder, mods.RECORD)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    out[folder] = json.load(f)
        return out

    def _order(self, records):
        """The saved order, minus mods gone from the library, plus new ones at the end, ticked."""
        path = os.path.join(self._home, ORDER)
        saved = []
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                saved = [e for e in json.load(f) if e["folder"] in records]
        known = {e["folder"] for e in saved}
        return saved + [{"folder": f, "enabled": True} for f in records if f not in known]

    def _install_state(self, order):
        """{status: none, current, changed or unknown; clashes of the last install}."""
        if not os.path.isfile(os.path.join(self._state_dir, deploy.RECORD)):
            return {"status": "none", "clashes": []}
        path = os.path.join(self._state_dir, LAST)
        if not os.path.isfile(path):
            return {"status": "unknown", "clashes": []}  # installed before this was recorded
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        ticked = [e["folder"] for e in order if e["enabled"]]
        return {"status": "current" if ticked == last["folders"] else "changed",
                "clashes": last["clashes"]}

    def state(self):
        """What the page shows: mods in load order, the install's status, the settings."""
        records = self._records()
        keys = ("name", "version", "latest", "nexus", "nexus_id") + nexus_files.ABOUT
        order = self._order(records)
        listed = [dict(e, **{k: records[e["folder"]].get(k) for k in keys}) for e in order]
        current = settings.load(self._home)
        folders = {k: current[k] for k in settings.FOLDERS}
        return {"mods": listed, "install": self._install_state(order),
                "settings": dict(folders, game_ok=settings.game_ok(current["game_dir"]))}

    def set_folder(self, key, path):
        """Keep one of settings.FOLDERS; an empty path goes back to the one Steam or Windows has."""
        if key not in settings.FOLDERS:
            raise ValueError("no setting %r" % key)
        settings.save(self._home, **{key: os.path.normpath(path) if path.strip() else None})
        return self.state()

    def choose_folder(self, key):
        """Let the user pick the folder for key, starting from the current one."""
        path = self._pick_folder(settings.load(self._home)[key])
        return self.set_folder(key, path) if path else self.state()

    def save_order(self, entries):
        """Keep the page's order and ticks: a list of {folder, enabled}, first loaded first."""
        with open(os.path.join(self._home, ORDER), "w", encoding="utf-8") as f:
            json.dump([{"folder": e["folder"], "enabled": bool(e["enabled"])} for e in entries],
                      f, indent=1)
        return self.state()

    def import_mods(self):
        return self.import_paths(self._pick_archives() or [])

    def import_paths(self, paths):
        """Import each archive; the window calls it with the files dropped on it."""
        for path in paths:
            mods.import_archive(path, self._library)
        return self.state()

    def delete(self, folder):
        mods.delete(self._library, folder)
        return self.state()

    def open_folder(self, folder):
        if folder not in self._records():
            raise ValueError("no mod %r in the library" % folder)
        os.startfile(os.path.join(self._library, folder))

    def open_nexus(self, folder):
        nexus_id = self._records()[folder].get("nexus_id")
        if nexus_id:
            webbrowser.open(NEXUS_PAGE % nexus_id)

    def refresh(self):
        """Every mod's name, version and Nexus ids looked up again; the page calls it on start."""
        mods.refresh(self._library)
        return self.state()

    def install(self):
        """Merge and install the ticked mods in load order; returns install_mods' report."""
        game = self._game()
        ticked = [e["folder"] for e in self._order(self._records()) if e["enabled"]]
        if not ticked:
            raise RuntimeError("no mods are ticked")
        report = flow.install_mods(game, self._state_dir, self._library, ticked)
        with open(os.path.join(self._state_dir, LAST), "w", encoding="utf-8") as f:
            json.dump({"folders": ticked, "clashes": report.get("clashes", [])}, f, indent=1)
        return report

    def restore(self):
        """Take every installed mod out; returns the paths left alone because they changed since."""
        skipped = deploy.restore(self._game(), self._state_dir)
        if os.path.isfile(os.path.join(self._state_dir, LAST)):
            os.remove(os.path.join(self._state_dir, LAST))
        return skipped

    def _game(self):
        game_dir = settings.load(self._home)["game_dir"]
        if not settings.game_ok(game_dir):
            raise RuntimeError(NO_GAME)
        return game_dir
