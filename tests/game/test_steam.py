import os
import tempfile
import unittest

from d4xmm.game import steam

MANIFEST = '"AppState"\n{\n\t"name"\t\t"%s"\n\t"installdir"\t\t"D4X"\n}\n'


class GameFolder(unittest.TestCase):
    def setUp(self):
        self.lib = tempfile.mkdtemp()
        self.apps = os.path.join(self.lib, "steamapps")
        os.makedirs(self.apps)

    def _manifest(self, name, game):
        with open(os.path.join(self.apps, name), "w", encoding="utf-8") as f:
            f.write(MANIFEST % game)

    def test_finds_the_game_by_name(self):
        self._manifest("appmanifest_1.acf", "Other Game")
        self._manifest("appmanifest_2.acf", steam.GAME_NAME)
        self.assertEqual(steam.game_folder(self.lib), os.path.join(self.apps, "common", "D4X"))

    def test_none_when_absent(self):
        self._manifest("appmanifest_1.acf", "Other Game")
        self.assertIsNone(steam.game_folder(self.lib))

    def test_libraries_lists_steam_first_without_repeats(self):
        vdf = os.path.join(self.apps, "libraryfolders.vdf")
        steam_path = self.lib.replace("\\", "\\\\")
        with open(vdf, "w", encoding="utf-8") as f:
            f.write('"0" { "path" "%s" }\n"1" { "path" "D:\\\\Games" }' % steam_path)
        self.assertEqual(steam.libraries(self.lib), [self.lib, os.path.normpath("D:\\Games")])
