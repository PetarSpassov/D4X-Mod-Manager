"""What the window's page can ask for: the mod list and its order, import, install and restore.

Under one home folder: library/ (mods), state/ (install record, backups), order.json (load order).
"""
import json
import os

from d4xmm.install import deploy, flow
from d4xmm.library import mods

ORDER = "order.json"


class Api:
    """pywebview hands the page every public attribute, so all but the calls start with _."""

    def __init__(self, home, game_dir, pick_archives=None):
        """pick_archives() returns the paths the user chose; the window supplies a file dialog."""
        self._home, self._game_dir, self._pick_archives = home, game_dir, pick_archives
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

    def state(self):
        """What the page shows: the game folder, mods in load order, whether an install is in."""
        records = self._records()
        listed = [dict(e, name=records[e["folder"]]["name"],
                       version=records[e["folder"]]["version"],
                       nexus=records[e["folder"]].get("nexus")) for e in self._order(records)]
        installed = os.path.isfile(os.path.join(self._state_dir, deploy.RECORD))
        return {"game_dir": self._game_dir, "mods": listed, "installed": installed}

    def save_order(self, entries):
        """Keep the page's order and ticks: a list of {folder, enabled}, first loaded first."""
        with open(os.path.join(self._home, ORDER), "w", encoding="utf-8") as f:
            json.dump([{"folder": e["folder"], "enabled": bool(e["enabled"])} for e in entries],
                      f, indent=1)
        return self.state()

    def import_mods(self):
        for path in (self._pick_archives() or []):
            mods.import_archive(path, self._library)
        return self.state()

    def refresh(self):
        """Every mod's name, version and Nexus ids looked up again; the page calls it on start."""
        mods.refresh(self._library)
        return self.state()

    def install(self):
        """Merge and install the ticked mods in load order; returns install_mods' report."""
        ticked = [e["folder"] for e in self._order(self._records()) if e["enabled"]]
        if not ticked:
            raise RuntimeError("no mods are ticked")
        return flow.install_mods(self._game(), self._state_dir, self._library, ticked)

    def restore(self):
        """Take every installed mod out; returns the paths left alone because they changed since."""
        return deploy.restore(self._game(), self._state_dir)

    def _game(self):
        if not self._game_dir:
            raise RuntimeError("Dune: Spice Wars was not found in Steam")
        return self._game_dir
