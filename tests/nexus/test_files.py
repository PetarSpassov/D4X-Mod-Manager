import unittest

from d4xmm.nexus import files

QQ = "QuinnQuest-5-v0-4-2-2-1780006924.zip"


def _fake(listing, name=None):
    """A stand-in for the API: {mod id: [file records]}, and the ids it was asked for."""
    asked = []

    def mod(mod_id):
        asked.append(mod_id)
        return {"name": name, "files": listing.get(mod_id, [])}
    return mod, asked


class Lookup(unittest.TestCase):
    def test_matches_the_exact_download_name(self):
        mod_files, asked = _fake({"5": [
            {"fileId": 18, "name": "QuinnQuest", "version": "v0.2.2", "category": "OLD_VERSION",
             "uri": "QuinnQuest-5-v0-2-2-1756549824.zip"},
            {"fileId": 30, "name": "QuinnQuest", "version": "v0.4.2.2", "category": "MAIN",
             "uri": QQ}]}, name="QuinnQuest - Conquest Additions and Overhauls")
        self.assertEqual(files.lookup(QQ, mod_files),
                         {"nexus_id": 5, "file_id": 30, "name": "QuinnQuest",
                          "mod_name": "QuinnQuest - Conquest Additions and Overhauls",
                          "version": "v0.4.2.2", "category": "MAIN", "latest": "v0.4.2.2"})
        self.assertEqual(asked, ["5"])

    def test_latest_is_the_newest_main_file_even_when_this_one_is_older(self):
        mod_files, _ = _fake({"5": [
            {"fileId": 30, "name": "Q", "version": "v0.4.2.2", "category": "OLD_VERSION",
             "uri": QQ},
            {"fileId": 50, "name": "Q", "version": "v0.5", "category": "MAIN", "uri": "b.zip"},
            {"fileId": 40, "name": "Q", "version": "v0.4.3", "category": "MAIN", "uri": "a.zip"},
            {"fileId": 60, "name": "Q", "version": "patch", "category": "OPTIONAL", "uri": "c"}]})
        self.assertEqual(files.lookup(QQ, mod_files)["latest"], "v0.5")

    def test_a_mod_with_no_name_falls_back_to_the_file_name(self):
        mod_files, _ = _fake({"5": [{"fileId": 1, "name": "QuinnQuest", "version": "1",
                                     "uri": QQ, "category": "MAIN"}]})
        self.assertEqual(files.lookup(QQ, mod_files)["mod_name"], "QuinnQuest")

    def test_tries_each_number_in_the_name_once(self):
        mod_files, asked = _fake({"4": [{"fileId": 1, "name": "X", "version": "1", "uri": QQ,
                                         "category": "MAIN"}]})
        self.assertEqual(files.lookup(QQ, mod_files)["nexus_id"], 4)
        self.assertEqual(asked, ["5", "4"])

    def test_no_match_is_none(self):
        mod_files, asked = _fake({})
        self.assertIsNone(files.lookup(QQ, mod_files))
        self.assertEqual(asked, ["5", "4", "2"])

    def test_a_name_without_numbers_asks_nothing(self):
        mod_files, asked = _fake({})
        self.assertIsNone(files.lookup("QuinnQuest.zip", mod_files))
        self.assertEqual(asked, [])
