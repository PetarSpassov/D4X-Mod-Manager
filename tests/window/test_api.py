import os
import tempfile
import unittest
import zipfile
from unittest import mock

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
        with mock.patch("d4xmm.install.deploy.restore", return_value=[]):
            self.api.restore()
        os.remove(os.path.join(self.home, "state", "install.json"))
        self.assertEqual(self.api.state()["install"], {"status": "none", "clashes": []})

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
