import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from unittest import mock

from d4xmm.library import mods

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _zip(folder, name, members):
    path = os.path.join(folder, name)
    with zipfile.ZipFile(path, "w") as z:
        for member, data in members.items():
            z.writestr(member, data)
    return path


class Target(unittest.TestCase):
    def test_paks_and_hlboot_go_to_the_root_wherever_they_sit(self):
        self.assertEqual(mods.target("MyMod/res.compressed1.pak"), "res.compressed1.pak")
        self.assertEqual(mods.target("MyMod/bin/hlbootdx.dat"), "hlbootdx.dat")

    def test_audio_keeps_its_layout_under_audio(self):
        self.assertEqual(mods.target("MyMod/res/Audio/Media/1.wem"), "res/Audio/Media/1.wem")
        self.assertEqual(mods.target("MyMod/sounds/UI.bnk"), "res/Audio/UI.bnk")

    def test_other_files_are_not_loaded(self):
        self.assertIsNone(mods.target("MyMod/readme.txt"))
        self.assertIsNone(mods.target("res.pak"))


class Describe(unittest.TestCase):
    def _describe(self, path, **lookup):
        with mock.patch.object(mods.nexus_files, "lookup", **lookup) as asked:
            info = mods.describe(path)
        asked.assert_called_once_with(os.path.basename(path))
        return info

    def test_a_file_nexus_knows_takes_its_record(self):
        found = {"nexus_id": 5, "file_id": 30, "name": "QuinnQuest", "version": "v0.4.2.2",
                 "mod_name": "QuinnQuest - Conquest", "category": "MAIN"}
        self.assertEqual(self._describe("C:/dl/QuinnQuest-5-v0-4-2-2-1780006924.zip",
                                        return_value=found),
                         {"name": "QuinnQuest - Conquest", "file": "QuinnQuest", "nexus_id": 5,
                          "file_id": 30, "version": "v0.4.2.2", "nexus": "found"})

    def test_a_file_nexus_doesnt_know_keeps_its_name_and_no_version(self):
        self.assertEqual(self._describe("C:/dl/my mod.zip", return_value=None),
                         {"name": "my mod", "file": "my mod", "nexus_id": None, "file_id": None,
                          "version": None, "nexus": "not_found"})

    def test_offline_guesses_nothing(self):
        info = self._describe("QuinnQuest-5-v0-4-2-2-1780006924.zip",
                              side_effect=mods.nexus_files.Offline("no network"))
        self.assertEqual((info["name"], info["version"], info["nexus"]),
                         ("QuinnQuest-5-v0-4-2-2-1780006924", None, "offline"))

    def test_an_error_from_nexus_is_not_called_offline(self):
        info = self._describe("QuinnQuest-5-v0-4-2-2-1780006924.zip",
                              side_effect=mods.nexus_files.Refused("HTTP Error 403"))
        self.assertEqual((info["version"], info["nexus"]), (None, "refused"))


class ImportZip(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(mods.nexus_files, "lookup", return_value=None)
        patch.start()
        self.addCleanup(patch.stop)
        self.downloads, self.library = tempfile.mkdtemp(), tempfile.mkdtemp()

    def _imports_cool_mod(self, archive):
        record = mods.import_archive(archive, self.library)
        folder = os.path.join(self.library, "Cool_Mod-7-2-0-1752884636")  # not on Nexus: whole name
        with open(os.path.join(folder, mods.RECORD), encoding="utf-8") as f:
            self.assertEqual(json.load(f), record)
        self.assertEqual(record["files"], {"res.compressed1.pak": "Cool/res.compressed1.pak"})
        self.assertEqual(record["other"], ["Cool/readme.txt"])
        self.assertTrue(os.path.isfile(os.path.join(folder, "Cool", "res.compressed1.pak")))

    def test_unpacks_and_records_a_zip(self):
        self._imports_cool_mod(_zip(self.downloads, "Cool Mod-7-2-0-1752884636.zip",
                                    {"Cool/res.compressed1.pak": b"pak", "Cool/readme.txt": b"hi"}))

    def test_unpacks_a_7z(self):
        src = os.path.join(tempfile.mkdtemp(), "Cool")
        os.makedirs(src)
        for name, data in (("res.compressed1.pak", b"pak"), ("readme.txt", b"hi")):
            with open(os.path.join(src, name), "wb") as f:
                f.write(data)
        archive = os.path.join(self.downloads, "Cool Mod-7-2-0-1752884636.7z")
        subprocess.run([mods.SEVEN_ZIP, "a", archive, src], check=True, capture_output=True)
        self._imports_cool_mod(archive)

    def test_unpacks_a_rar(self):
        self._imports_cool_mod(os.path.join(FIXTURES, "Cool Mod-7-2-0-1752884636.rar"))

    def test_an_unreadable_archive_is_refused_and_leaves_nothing(self):
        path = os.path.join(self.downloads, "Broken.7z")
        with open(path, "wb") as f:
            f.write(b"not an archive")
        with self.assertRaises(mods.ModImportError):
            mods.import_archive(path, self.library)
        self.assertEqual(os.listdir(self.library), [])

    def test_reimport_replaces_the_old_copy(self):
        mods.import_archive(_zip(self.downloads, "M.zip", {"old/res.compressed1.pak": b"1"}),
                        self.library)
        mods.import_archive(_zip(self.downloads, "M.zip", {"new/res.compressed1.pak": b"2"}),
                        self.library)
        self.assertEqual(sorted(os.listdir(os.path.join(self.library, "M"))),
                         ["mod.json", "new"])

    def test_a_zip_with_nothing_to_load_is_refused_and_leaves_nothing(self):
        z = _zip(self.downloads, "Notes.zip", {"readme.txt": b"hi"})
        with self.assertRaises(mods.ModImportError):
            mods.import_archive(z, self.library)
        self.assertEqual(os.listdir(self.library), [])

    def test_two_files_for_one_place_are_refused(self):
        z = _zip(self.downloads, "Twice.zip",
                 {"a/res.compressed1.pak": b"1", "b/res.compressed1.pak": b"2"})
        with self.assertRaises(mods.ModImportError):
            mods.import_archive(z, self.library)

    def test_paths_escaping_the_folder_stay_inside(self):
        z = _zip(self.downloads, "Evil.zip", {"../../res.compressed1.pak": b"x"})
        record = mods.import_archive(z, self.library)
        self.assertEqual(sorted(os.listdir(self.library)), ["Evil"])
        self.assertEqual(record["files"], {"res.compressed1.pak": "res.compressed1.pak"})
