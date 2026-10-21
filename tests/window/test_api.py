import os
import tempfile
import unittest
import zipfile
from unittest import mock

from d4xmm.nexus import account
from d4xmm.nexus import files as nexus_files
from d4xmm.window import settings
from d4xmm.window.api import NO_GAME, Api


class WindowApi(unittest.TestCase):
    def setUp(self):
        self.home, self.zips, self.game = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        open(os.path.join(self.game, "D4X.exe"), "w").close()
        settings.save(self.home, game_dir=self.game)
        self.picked, self.folder = [], None
        self.api = Api(self.home, lambda: self.picked, lambda start: self.folder)

    def _zip(self, name):
        path = os.path.join(self.zips, name + ".zip")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("Audio/%s.bnk" % name, b"x")
        return path

    def _names(self, state):
        return [(m["name"], m["enabled"]) for m in state["mods"]]

    def test_imported_mods_join_the_end_of_the_list_ticked(self):
        self.picked = [self._zip("A"), self._zip("B")]
        self.assertEqual(self._names(self.api.import_mods()), [("A", True), ("B", True)])

    def test_a_saved_order_and_ticks_come_back(self):
        self.picked = [self._zip("A"), self._zip("B")]
        self.api.import_mods()
        self.api.save_order([{"folder": "B", "enabled": True}, {"folder": "A", "enabled": False}])
        fresh = Api(self.home)
        self.assertEqual(self._names(fresh.state()), [("B", True), ("A", False)])

    def test_each_profile_keeps_its_own_order_and_an_import_ticks_only_in_the_active_one(self):
        self.picked = [self._zip("A"), self._zip("B")]
        self.api.import_mods()
        state = self.api.new_profile("Solo")
        self.assertEqual(state["profiles"], {"active": "Solo", "names": ["Default", "Solo"]})
        self.assertEqual(self._names(state), [("A", True), ("B", True)])
        self.api.save_order([{"folder": "B", "enabled": True}, {"folder": "A", "enabled": False}])
        self.api.import_paths([self._zip("C")])
        state = self.api.switch_profile("Default")
        self.assertEqual(self._names(state), [("A", True), ("B", True), ("C", False)])
        state = self.api.delete_profile("Default")
        self.assertEqual(self._names(state), [("B", True), ("A", False), ("C", True)])

    def test_install_passes_only_ticked_mods_in_load_order(self):
        self.picked = [self._zip("A"), self._zip("B"), self._zip("C")]
        self.api.import_mods()
        self.api.save_order([{"folder": "C", "enabled": True}, {"folder": "A", "enabled": False},
                             {"folder": "B", "enabled": True}])
        with mock.patch("d4xmm.install.flow.install_mods", return_value={}) as run:
            self.api.install()
        self.assertEqual(run.call_args.args[0], self.game)
        self.assertEqual(run.call_args.args[3], ["C", "B"])

    def test_refresh_returns_the_list_with_what_nexus_says(self):
        self.picked = [self._zip("A")]
        self.api.import_mods()
        found = {"nexus_id": 1, "file_id": 2, "name": "A", "mod_name": "Mod A", "version": "1.0",
                 "category": "MAIN", "latest": "1.1", "creator": "Ann", "summary": None,
                 "picture": None, "downloads": 7, "endorsements": 2, "updated": None}
        with mock.patch("d4xmm.nexus.files.lookup", return_value=found):
            state = self.api.refresh()
        self.assertEqual([(m["folder"], m["name"], m["version"], m["creator"], m["downloads"])
                          for m in state["mods"]], [("A", "Mod A", "1.0", "Ann", 7)])

    def test_dropped_paths_import_and_delete_takes_a_mod_out(self):
        self.api.import_paths([self._zip("A"), self._zip("B")])
        self.assertEqual(self._names(self.api.delete("A")), [("B", True)])

    def _fake_install(self, game_dir, state_dir, library, folders):
        with open(os.path.join(state_dir, "install.json"), "w") as f:
            f.write("[]")
        return {"clashes": [{"winner": folders[-1], "over": folders[:-1], "items": ["x"]}]}

    def test_install_status_follows_the_ticked_list_until_restore(self):
        self.picked = [self._zip("A"), self._zip("B")]
        self.assertEqual(self.api.import_mods()["install"]["status"], "none")
        with mock.patch("d4xmm.install.flow.install_mods", self._fake_install):
            self.api.install()
        install = self.api.state()["install"]
        self.assertEqual((install["status"], install["clashes"][0]["winner"]), ("current", "B"))
        state = self.api.save_order([{"folder": "B", "enabled": True},
                                     {"folder": "A", "enabled": True}])
        self.assertEqual(state["install"]["status"], "changed")
        self.api.save_order([{"folder": "A", "enabled": True}, {"folder": "B", "enabled": True}])
        self.assertEqual(self.api.state()["install"]["status"], "current")
        found = {"nexus_id": 1, "file_id": 3, "name": "B", "mod_name": "B", "version": "2.0",
                 "category": "MAIN", "latest": "2.0", "creator": None, "summary": None,
                 "picture": None, "downloads": 0, "endorsements": 0, "updated": None}
        with mock.patch("d4xmm.nexus.files.lookup", return_value=found):
            state = self.api.import_paths([self._zip("B-1-2-0-1790000000")])
        self.assertEqual(self._names(state), [("A", True), ("B", True)])  # updated in its place
        self.assertEqual(state["install"]["status"], "changed")
        with mock.patch("d4xmm.install.deploy.restore", return_value=[]):
            self.api.restore()
        os.remove(os.path.join(self.home, "state", "install.json"))
        self.assertEqual(self.api.state()["install"], {"status": "none", "clashes": []})

    def test_an_install_refused_over_the_trait_cap_is_not_recorded(self):
        self.picked = [self._zip("A")]
        self.api.import_mods()
        with mock.patch("d4xmm.install.flow.install_mods", self._fake_install):
            self.api.install()
        self.api.import_paths([self._zip("B")])
        with mock.patch("d4xmm.install.flow.install_mods",
                        return_value={"merge": {"traits_over": True}, "clashes": []}):
            self.api.install()
        self.assertEqual(self.api.state()["install"]["status"], "changed")  # A alone is in

    def test_open_on_nexus_opens_the_mods_page_only_when_it_has_one(self):
        self.picked = [self._zip("A")]
        self.api.import_mods()
        with mock.patch("webbrowser.open") as opened:
            self.api.open_nexus("A")
        opened.assert_not_called()

    def test_browse_gives_the_catalog(self):
        listing = [{"nexus_id": 5, "name": "Mod A"}]
        with mock.patch("d4xmm.nexus.catalog.browse", return_value=listing):
            self.assertEqual(self.api.browse(), {"mods": listing, "error": None})

    def test_browse_says_offline_or_refused_instead_of_failing(self):
        for error, word in ((nexus_files.Offline, "offline"), (nexus_files.Refused, "refused")):
            with mock.patch("d4xmm.nexus.catalog.browse", side_effect=error("x")):
                self.assertEqual(self.api.browse(), {"mods": [], "error": word})

    def test_download_opens_the_mods_files_tab(self):
        with mock.patch("webbrowser.open") as opened:
            self.api.open_nexus_files(5)
        opened.assert_called_once_with("https://www.nexusmods.com/dunespicewars/mods/5?tab=files")

    def test_a_description_link_opens_only_when_it_is_a_web_address(self):
        with mock.patch("webbrowser.open") as opened:
            self.api.open_link("https://discord.gg/x")
            with self.assertRaises(ValueError):
                self.api.open_link("file:///C:/Windows/notepad.exe")
        opened.assert_called_once_with("https://discord.gg/x")

    def test_a_download_offered_is_imported_by_name_or_dismissed(self):
        settings.save(self.home, downloads=self.zips)
        os.rename(self._zip("A"), os.path.join(self.zips, "A-7-1-0-1752884636.zip"))
        open(os.path.join(self.zips, "B-8-1-1752884636.zip"), "w").close()
        found = {"nexus_id": 7, "file_id": 2, "name": "A", "mod_name": "Mod A", "version": "1",
                 "category": "MAIN", "latest": "1", **dict.fromkeys(nexus_files.ABOUT)}
        with mock.patch("d4xmm.nexus.files.lookup", return_value=found):
            self.assertEqual(len(self.api.downloads()), 2)
            self.api.dismiss_download("B-8-1-1752884636.zip")
            state = self.api.import_download("A-7-1-0-1752884636.zip")
            self.assertEqual([m["enabled"] for m in state["mods"]], [True])
            self.assertEqual(self.api.downloads(), [])
            self.api.delete(state["mods"][0]["folder"])
            self.assertEqual(self.api.downloads(), [])  # still there, but imported once already
        self.assertTrue(os.path.isfile(os.path.join(self.zips, "A-7-1-0-1752884636.zip")))
        for bad in ("..\\A-7-1-0-1752884636.zip", "notes.zip"):
            with self.assertRaises(ValueError):
                self.api.import_download(bad)

    def test_the_key_is_checked_when_typed_and_its_account_shown(self):
        self.assertEqual(self.api.state()["account"], {"key": "none"})
        settings.save(self.home, nexus_key="k")
        with mock.patch("d4xmm.nexus.account.check") as check, \
                mock.patch("d4xmm.library.mods.refresh"):
            self.assertEqual(Api(self.home).refresh()["account"], {"key": "saved"})
        check.assert_not_called()  # only the player's action asks Nexus about the key
        with mock.patch("d4xmm.nexus.account.check",
                        return_value={"name": "Ann", "premium": True}):
            self.assertEqual(self.api.check_key()["account"]["premium"], True)
        with mock.patch("d4xmm.nexus.account.check",
                        return_value={"name": "Ann", "premium": False}):
            self.assertEqual(self.api.set_setting("nexus_key", "k")["account"],
                             {"key": "ok", "name": "Ann", "premium": False})
        with mock.patch("d4xmm.nexus.account.check", side_effect=account.InvalidKey("401")):
            self.assertEqual(self.api.set_setting("nexus_key", "bad")["account"],
                             {"key": "invalid"})
        self.assertEqual(self.api.set_setting("nexus_key", "")["account"], {"key": "none"})

    def _premium(self):
        with mock.patch("d4xmm.nexus.account.check", return_value={"name": "A", "premium": True}):
            self.api.set_setting("nexus_key", "k")

    def _download(self, start):
        """start() with Nexus faked: file 3 of mod 7 downloads as A's zip; returns the state
        and how the file and its address were asked for."""
        settings.save(self.home, downloads=self.zips)
        name, source, asked = "A-7-1-0-1752884636.zip", self._zip("A"), {}

        def pick(mod_id, file_id=None):
            asked["pick"] = (mod_id, file_id)
            return {"file_id": 3, "download": name, "version": "1.0"}

        def url(key, mod_id, file_id, grant=None):
            asked["url"] = (key, mod_id, file_id, grant)
            return "https://cdn/a"

        def fetch(url, dest, progress):
            progress(2_500_000, 10_000_000)
            asked["progress"] = self.api.download_progress(asked["url"][1])
            os.rename(source, dest)
        with mock.patch("d4xmm.nexus.files.pick_file", pick), \
                mock.patch("d4xmm.nexus.account.download_url", url), \
                mock.patch("d4xmm.nexus.account.fetch", fetch), \
                mock.patch("d4xmm.nexus.files.lookup", return_value=None):
            state = start()
        self.assertEqual([m["enabled"] for m in state["mods"]], [True])
        self.assertTrue(os.path.isfile(os.path.join(self.zips, name)))
        self.assertEqual(self.api.downloads(), [])
        return asked

    def test_premium_download_imports_the_newest_main_file_and_keeps_it_in_downloads(self):
        self._premium()
        asked = self._download(lambda: self.api.download_mod(7))
        self.assertEqual((asked["pick"], asked["url"]), ((7, None), ("k", 7, 3, None)))
        self.assertEqual(asked["progress"], "Downloading: 2.5 MB of 10.0 MB")
        self.assertIsNone(self.api.download_progress(7))

    def test_a_website_link_downloads_its_own_file_with_its_grant(self):
        settings.save(self.home, nexus_key="k")
        link = "nxm://dunespicewars/mods/7/files/3?key=abc&expires=17&user_id=1"
        asked = self._download(lambda: self.api.download_link(link))
        self.assertEqual(asked["url"], ("k", 7, 3, {"key": "abc", "expires": "17"}))
        with self.assertRaisesRegex(RuntimeError, "another game"):
            self.api.download_link("nxm://skyrim/mods/7/files/3?key=abc&expires=17")

    def test_without_premium_a_key_or_a_file_nothing_downloads(self):
        with self.assertRaisesRegex(RuntimeError, "Premium"):
            self.api.download_mod(7)
        with self.assertRaisesRegex(RuntimeError, "API key"):
            self.api.download_link("nxm://dunespicewars/mods/7/files/3?key=a&expires=1")
        self._premium()
        with mock.patch("d4xmm.nexus.files.pick_file", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "no such file"):
                self.api.download_mod(7)

    def test_the_start_link_is_given_once(self):
        api = Api(self.home, pending_link="nxm://x")
        self.assertEqual((api.pending_link(), api.pending_link()), ("nxm://x", None))

    def test_no_game_or_nothing_ticked_is_an_error_not_an_install(self):
        with self.assertRaises(RuntimeError):
            self.api.install()
        self.picked = [self._zip("A")]
        self.api.import_mods()
        os.remove(os.path.join(self.game, "D4X.exe"))
        self.assertFalse(self.api.state()["settings"]["game_ok"])
        with mock.patch("d4xmm.install.flow.install_mods") as run:
            with self.assertRaisesRegex(RuntimeError, NO_GAME):
                self.api.install()
        run.assert_not_called()
        with self.assertRaisesRegex(RuntimeError, NO_GAME):
            self.api.restore()

    def test_a_chosen_or_typed_folder_is_kept_and_an_empty_one_is_found_again(self):
        self.folder = self.zips
        self.assertEqual(self.api.choose_folder("downloads")["settings"]["downloads"], self.zips)
        self.folder = None
        self.assertEqual(self.api.choose_folder("downloads")["settings"]["downloads"], self.zips)
        with mock.patch.object(settings, "downloads_dir", return_value="C:\\dl"):
            state = Api(self.home).set_setting("downloads", " ")
        self.assertEqual(state["settings"]["downloads"], "C:\\dl")
        with self.assertRaises(ValueError):
            self.api.set_setting("window", "x")

    def test_the_nexus_key_is_kept_as_typed_and_cleared_when_empty(self):
        self.assertIsNone(self.api.state()["settings"]["nexus_key"])
        self.assertEqual(self.api.set_setting("nexus_key", " abc/def= ")["settings"]["nexus_key"],
                         "abc/def=")
        self.assertIsNone(self.api.set_setting("nexus_key", "")["settings"]["nexus_key"])

    def test_the_page_sees_only_the_calls(self):
        public = sorted(n for n in vars(self.api) if not n.startswith("_"))
        self.assertEqual(public, [])


if __name__ == "__main__":
    unittest.main()
