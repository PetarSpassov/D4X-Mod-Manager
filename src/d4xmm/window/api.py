"""What the window's page can ask for: the mods and their order, import, install, settings, Browse.

Under one home: library/ (mods), state/ (install record, backups), profiles.json, settings.json.
"""
import json
import os
import shutil
import webbrowser

from d4xmm.install import deploy, flow
from d4xmm.library import downloads as watched
from d4xmm.library import mods
from d4xmm.nexus import account, catalog
from d4xmm.nexus import files as nexus_files
from d4xmm.window import profiles, settings

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
        self._known = {}  # Downloads archive name: Nexus's answer, so each is asked about once
        self._account = {"key": "checking"}  # whose key, and Premium; refresh() asks Nexus

    def _records(self):
        """{library folder: its mod.json record} for every imported mod."""
        out = {}
        for folder in sorted(os.listdir(self._library)):
            path = os.path.join(self._library, folder, mods.RECORD)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    out[folder] = json.load(f)
        return out

    def _order(self, records, data=None):
        """The active profile's order, minus mods gone from the library, plus others unticked."""
        data = data or profiles.load(self._home)
        saved = [e for e in data["profiles"][data["active"]] if e["folder"] in records]
        known = {e["folder"] for e in saved}
        return saved + [{"folder": f, "enabled": False} for f in records if f not in known]

    def _change_profiles(self, change):
        """Apply change(data, the active order) to the saved profiles; returns the new state."""
        data = profiles.load(self._home)
        data["profiles"][data["active"]] = self._order(self._records(), data)
        change(data, data["profiles"][data["active"]])
        profiles.save(self._home, data)
        return self.state()

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
        typed = {k: current[k] for k in settings.TYPED}
        data = profiles.load(self._home)
        return {"mods": listed, "install": self._install_state(order),
                "settings": dict(typed, game_ok=settings.game_ok(current["game_dir"])),
                "profiles": {"active": data["active"], "names": list(data["profiles"])},
                "account": self._account}

    def set_setting(self, key, value):
        """Keep one of settings.TYPED; an empty folder goes back to the one Steam or Windows has."""
        if key not in settings.TYPED:
            raise ValueError("no setting %r" % key)
        value = value.strip() or None
        if value and key in settings.FOLDERS:
            value = os.path.normpath(value)
        settings.save(self._home, **{key: value})
        if key == "nexus_key":
            self._check_key()
        return self.state()

    def choose_folder(self, key):
        """Let the user pick the folder for key, starting from the current one."""
        path = self._pick_folder(settings.load(self._home)[key])
        return self.set_setting(key, path) if path else self.state()

    def save_order(self, entries):
        """Keep the page's order and ticks in the active profile: [{folder, enabled}]."""
        def keep(data, _):
            data["profiles"][data["active"]] = profiles.clean(entries)
        return self._change_profiles(keep)

    def new_profile(self, name):
        """A profile called name, a copy of the active one's order, made active."""
        return self._change_profiles(lambda data, order: profiles.create(data, name, order))

    def switch_profile(self, name):
        return self._change_profiles(lambda data, _: profiles.switch(data, name))

    def delete_profile(self, name):
        return self._change_profiles(lambda data, _: profiles.delete(data, name))

    def import_mods(self):
        return self.import_paths(self._pick_archives() or [])

    def import_paths(self, paths):
        """Import each archive, ticked at the end of the active profile; also for dropped files."""
        before = set(self._records())
        for path in paths:
            mods.import_archive(path, self._library)
            # deleting the mod later mustn't bring its archive back as a new download
            watched.dismiss(self._state_dir, os.path.basename(path))

        def tick_new(_, order):
            for e in order:
                e["enabled"] = e["enabled"] or e["folder"] not in before
        return self._change_profiles(tick_new)

    def downloads(self):
        """New Dune mod archives in the Downloads folder: [{file, name, version}]."""
        imported = [r.get("source") for r in self._records().values()]
        return watched.offers(settings.load(self._home)["downloads"], imported, self._state_dir,
                              self._known)

    def import_download(self, name):
        """Import one archive the Downloads folder offered, by its name there."""
        if os.path.basename(name) != name or not watched.NEXUS_NAME.search(name):
            raise ValueError("not a download: %r" % name)
        return self.import_paths([os.path.join(settings.load(self._home)["downloads"], name)])

    def dismiss_download(self, name):
        """Never offer this archive again."""
        watched.dismiss(self._state_dir, name)

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

    def browse(self):
        """{mods: Nexus's catalog for the game; error: None, "offline" or "refused"}."""
        try:
            return {"mods": catalog.browse(), "error": None}
        except nexus_files.Offline:
            return {"mods": [], "error": "offline"}
        except nexus_files.Refused:
            return {"mods": [], "error": "refused"}

    def open_nexus_files(self, nexus_id):
        """The mod's Files tab in the user's browser, where its Download buttons are."""
        webbrowser.open(NEXUS_PAGE % int(nexus_id) + "?tab=files")

    def open_link(self, url):
        """A link in a mod's description, in the user's browser; only web addresses."""
        if not url.lower().startswith(("https://", "http://")):
            raise ValueError("not a web address: %r" % url)
        webbrowser.open(url)

    def refresh(self):
        """The key checked, and every mod's name, version and Nexus ids looked up again; the page
        calls it on start."""
        self._check_key()
        mods.refresh(self._library)
        return self.state()

    def _check_key(self):
        """Ask Nexus whose the key is; state() shows the answer until the key changes."""
        key = settings.load(self._home)["nexus_key"]
        if not key:
            self._account = {"key": "none"}
            return
        try:
            self._account = dict(account.check(key), key="ok")
        except account.InvalidKey:
            self._account = {"key": "invalid"}
        except (nexus_files.Offline, nexus_files.Refused):
            self._account = {"key": "unchecked"}  # no answer: the next start asks again

    def open_key_page(self):
        webbrowser.open(account.KEY_PAGE)

    def download_mod(self, nexus_id):
        """Premium only: the mod's newest main file, downloaded, imported, then put in Downloads
        as the browser would have, recorded so it isn't offered."""
        if not self._account.get("premium"):
            raise RuntimeError("Downloading in the app needs a Premium Nexus account.")
        newest = nexus_files.newest_main(str(int(nexus_id)))
        if not newest or os.path.basename(newest["uri"]) != newest["uri"]:
            raise RuntimeError("Nexus lists no main file to download for this mod.")
        current = settings.load(self._home)
        url = account.download_url(current["nexus_key"], int(nexus_id), newest["file_id"])
        staged = os.path.join(self._state_dir, newest["uri"])
        account.fetch(url, staged)
        state = self.import_paths([staged])
        if current["downloads"] and os.path.isdir(current["downloads"]):
            shutil.move(staged, os.path.join(current["downloads"], newest["uri"]))
        else:
            os.remove(staged)  # our own copy; the library has the mod's files
        return state

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
