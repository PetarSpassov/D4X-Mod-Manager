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
from d4xmm.window import links, profiles, settings

LAST = "last_install.json"  # under state/: the folders installed and who overrode whom
NEXUS_PAGE = "https://www.nexusmods.com/dunespicewars/mods/%d"
NO_GAME = "Can't find the game in the Steam directory. Please adjust it in Settings."


def _sources(folders, records):
    """The archive each of these library folders was imported from."""
    return [records[f].get("source") for f in folders]


class Api:
    """pywebview hands the page every public attribute, so all but the calls start with _."""

    def __init__(self, home, pick_archives=None, pick_folder=None, pending_link=None):
        """pick_archives() returns the chosen paths, pick_folder(start) one folder or None;
        pending_link: the nxm:// link the app was started with."""
        self._home, self._pick_archives, self._pick_folder = home, pick_archives, pick_folder
        self._library = os.path.join(home, "library")
        self._state_dir = os.path.join(home, "state")
        for folder in (self._library, self._state_dir):
            os.makedirs(folder, exist_ok=True)
        self._known = {}  # Downloads archive name: Nexus's answer, so each is asked about once
        # whose key, and Premium; None: not asked yet this run
        self._account = None
        self._pending = pending_link
        self._progress = {}  # nexus id: what its download is doing, for the page to ask

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

    def _install_state(self, order, records):
        """{status: none, current, changed or unknown; clashes of the last install}.
        An update keeps its folder, so the archive each came from is compared too."""
        if not os.path.isfile(os.path.join(self._state_dir, deploy.RECORD)):
            return {"status": "none", "clashes": []}
        path = os.path.join(self._state_dir, LAST)
        if not os.path.isfile(path):
            return {"status": "unknown", "clashes": []}  # installed before this was recorded
        with open(path, encoding="utf-8") as f:
            last = json.load(f)
        ticked = [e["folder"] for e in order if e["enabled"]]
        same = ticked == last["folders"] and last.get("sources", _sources(ticked, records)) \
            == _sources(ticked, records)
        return {"status": "current" if same else "changed",
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
        return {"mods": listed, "install": self._install_state(order, records),
                "settings": dict(typed, game_ok=settings.game_ok(current["game_dir"])),
                "profiles": {"active": data["active"], "names": list(data["profiles"])},
                "account": self._account or {"key": "saved" if current["nexus_key"] else "none"},
                "links": links.status()}

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
        """Every mod's name, version and Nexus ids looked up again; the page calls it on start."""
        mods.refresh(self._library)
        return self.state()

    def check_key(self):
        """The page asks when Download is pressed and the key isn't checked yet."""
        self._check_key()
        return self.state()

    def _check_key(self):
        """Ask Nexus whose the key is; only on the player's action (typing it, Download), as
        Nexus's API policy asks. state() shows the answer until the key changes."""
        key = settings.load(self._home)["nexus_key"]
        if not key:
            self._account = {"key": "none"}
            return
        try:
            self._account = dict(account.check(key), key="ok")
        except account.InvalidKey:
            self._account = {"key": "invalid"}
        except (nexus_files.Offline, nexus_files.Refused):
            self._account = {"key": "unchecked"}  # no answer: the next Download asks again

    def open_key_page(self):
        webbrowser.open(account.KEY_PAGE)

    def download_mod(self, nexus_id):
        """Premium only: the mod's newest main file downloaded and imported."""
        if not (self._account or {}).get("premium"):
            raise RuntimeError("Downloading in the app needs a Premium Nexus account.")
        return self._download(int(nexus_id))

    def download_link(self, url):
        """A website "Mod Manager Download" link: its file downloaded and imported."""
        link = links.parse(url)
        if link["game"] != account.GAME:
            raise RuntimeError("That link is for another game's mod.")
        return self._download(link["mod_id"], link["file_id"], link["grant"])

    def pending_link(self):
        """The link the app was started with, once; the page asks when it is ready."""
        url, self._pending = self._pending, None
        return url

    def _download(self, mod_id, file_id=None, grant=None):
        """The file downloaded, imported, then put in Downloads as the browser would have,
        recorded so it isn't offered. file_id None: the newest main file."""
        current = settings.load(self._home)
        if not current["nexus_key"]:
            raise RuntimeError("Paste your Nexus API key in Settings first.")
        try:
            self._progress[mod_id] = "Asking Nexus for the file…"
            found = nexus_files.pick_file(mod_id, file_id)
            if not found or os.path.basename(found["uri"]) != found["uri"]:
                raise RuntimeError("Nexus lists no such file to download for this mod.")
            url = account.download_url(current["nexus_key"], mod_id, found["file_id"], grant)
            staged = os.path.join(self._state_dir, found["uri"])
            account.fetch(url, staged, lambda done, total: self._fetched(mod_id, done, total))
            self._progress[mod_id] = "Importing…"
            state = self.import_paths([staged])
        finally:
            self._progress.pop(mod_id, None)
        if current["downloads"] and os.path.isdir(current["downloads"]):
            shutil.move(staged, os.path.join(current["downloads"], found["uri"]))
        else:
            os.remove(staged)  # our own copy; the library has the mod's files
        return state

    def _fetched(self, mod_id, done, total):
        of = " of %.1f MB" % (total / 1e6) if total else ""
        self._progress[mod_id] = "Downloading: %.1f MB%s" % (done / 1e6, of)

    def download_progress(self, nexus_id):
        """What the download of this mod is doing now, or None when none runs."""
        return self._progress.get(int(nexus_id))

    def take_links(self):
        """Nexus's "Mod Manager Download" links come to this app from now on."""
        links.take(self._state_dir)
        return self.state()

    def release_links(self):
        links.release(self._state_dir)
        return self.state()

    def install(self):
        """Merge and install the ticked mods in load order; returns install_mods' report."""
        game = self._game()
        records = self._records()
        ticked = [e["folder"] for e in self._order(records) if e["enabled"]]
        if not ticked:
            raise RuntimeError("no mods are ticked")
        report = flow.install_mods(game, self._state_dir, self._library, ticked)
        if (report.get("merge") or {}).get("traits_over"):
            return report  # nothing was installed, so the last install still stands
        with open(os.path.join(self._state_dir, LAST), "w", encoding="utf-8") as f:
            json.dump({"folders": ticked, "sources": _sources(ticked, records),
                       "clashes": report.get("clashes", [])}, f, indent=1)
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
