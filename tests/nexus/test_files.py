import unittest

from d4xmm.nexus import files

QQ = "QuinnQuest-5-v0-4-2-2-1780006924.zip"


def _fake(listing):
    """A stand-in for the API: {mod id: [file records]}, and the ids it was asked for."""
    asked = []

    def mod_files(mod_id):
        asked.append(mod_id)
        return listing.get(mod_id, [])
    return mod_files, asked


class Lookup(unittest.TestCase):
    def test_matches_the_exact_download_name(self):
        mod_files, asked = _fake({"5": [
            {"fileId": 18, "name": "QuinnQuest", "version": "v0.2.2", "category": "OLD_VERSION",
             "uri": "QuinnQuest-5-v0-2-2-1756549824.zip"},
            {"fileId": 30, "name": "QuinnQuest", "version": "v0.4.2.2", "category": "MAIN",
             "uri": QQ}]})
        self.assertEqual(files.lookup(QQ, mod_files),
                         {"nexus_id": 5, "file_id": 30, "name": "QuinnQuest",
                          "version": "v0.4.2.2", "category": "MAIN"})
        self.assertEqual(asked, ["5"])

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
