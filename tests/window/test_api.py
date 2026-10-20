import os
import tempfile
import unittest
import zipfile
from unittest import mock

from d4xmm.window.api import Api


class WindowApi(unittest.TestCase):
    def setUp(self):
        self.home, self.zips = tempfile.mkdtemp(), tempfile.mkdtemp()
        self.picked = []
        self.api = Api(self.home, "C:/Game", lambda: self.picked)

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
        fresh = Api(self.home, "C:/Game")
        self.assertEqual(self._names(fresh.state()), [("B", True), ("A", False)])

    def test_install_passes_only_ticked_mods_in_load_order(self):
        self.picked = [self._zip("A"), self._zip("B"), self._zip("C")]
        self.api.import_mods()
        self.api.save_order([{"folder": "C", "enabled": True}, {"folder": "A", "enabled": False},
                             {"folder": "B", "enabled": True}])
        with mock.patch("d4xmm.install.flow.install_mods", return_value={}) as run:
            self.api.install()
        self.assertEqual(run.call_args.args[0], "C:/Game")
        self.assertEqual(run.call_args.args[3], ["C", "B"])

    def test_no_game_or_nothing_ticked_is_an_error_not_an_install(self):
        with self.assertRaises(RuntimeError):
            self.api.install()
        with self.assertRaises(RuntimeError):
            Api(self.home, None).restore()

    def test_the_page_sees_only_the_calls(self):
        public = sorted(n for n in vars(self.api) if not n.startswith("_"))
        self.assertEqual(public, [])


if __name__ == "__main__":
    unittest.main()
