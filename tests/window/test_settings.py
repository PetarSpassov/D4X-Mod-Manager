import os
import tempfile
import unittest
from unittest import mock

from d4xmm.window import settings


class Settings(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()
        for name, value in (("find", "C:\\Steam\\D4X"), ("downloads_dir", "C:\\dl")):
            target = settings.steam if name == "find" else settings
            patch = mock.patch.object(target, name, return_value=value)
            patch.start()
            self.addCleanup(patch.stop)

    def test_unsaved_folders_are_found_and_saved_ones_win(self):
        self.assertEqual(settings.load(self.home),
                         {"game_dir": "C:\\Steam\\D4X", "downloads": "C:\\dl", "nexus_key": None,
                          "window": None})
        settings.save(self.home, game_dir="D:\\D4X")
        settings.save(self.home, window={"width": 900, "maximized": True})
        loaded = settings.load(self.home)
        self.assertEqual((loaded["game_dir"], loaded["window"]["width"]), ("D:\\D4X", 900))
        settings.save(self.home, game_dir=None)
        self.assertEqual(settings.load(self.home)["game_dir"], "C:\\Steam\\D4X")

    def test_the_game_is_there_only_with_its_exe(self):
        self.assertFalse(settings.game_ok(self.home))
        self.assertFalse(settings.game_ok(None))
        open(os.path.join(self.home, settings.GAME_EXE), "w").close()
        self.assertTrue(settings.game_ok(self.home))

    def test_the_window_opens_where_it_closed_unless_that_screen_is_gone(self):
        screen = mock.Mock(x=0, y=0, width=1920, height=1080)
        saved = {"x": 100, "y": 50, "width": 900, "height": 700, "maximized": True}
        self.assertEqual(settings.window_args(saved, [screen]), saved)
        gone = dict(saved, x=2500)
        self.assertEqual(settings.window_args(gone, [screen]),
                         {"width": 900, "height": 700, "maximized": True})
        self.assertEqual(settings.window_args(None, [screen]),
                         {"width": 860, "height": 640, "maximized": False})

    def test_downloads_comes_from_windows(self):
        mock.patch.stopall()
        self.assertTrue(os.path.isabs(settings.downloads_dir()))


if __name__ == "__main__":
    unittest.main()
