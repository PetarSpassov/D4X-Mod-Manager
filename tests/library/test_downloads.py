import os
import tempfile
import unittest

from d4xmm.library import downloads
from d4xmm.nexus import files as nexus_files

QQ = "QuinnQuest-5-v0-4-2-2-1780006924.zip"
CP = "community_patch-1-0-1-4-1760743071.7z"


def _found(name):
    return {"mod_name": name, "version": "1.0"}


class Offers(unittest.TestCase):
    def setUp(self):
        self.folder, self.state = tempfile.mkdtemp(), tempfile.mkdtemp()
        self.asked = []

    def _file(self, name, age):
        path = os.path.join(self.folder, name)
        open(path, "w").close()
        os.utime(path, (1_000_000 - age, 1_000_000 - age))

    def _lookup(self, answers):
        def lookup(name):
            self.asked.append(name)
            answer = answers[name]
            if isinstance(answer, Exception):
                raise answer
            return answer
        return lookup

    def test_offers_new_nexus_archives_of_this_game_oldest_first(self):
        for name, age in ((QQ, 1), (CP, 2), ("Other-9-1-1700000000.zip", 3),
                          ("notes.zip", 4), (QQ + ".crdownload", 5)):
            self._file(name, age)
        lookup = self._lookup({QQ: _found("QuinnQuest"), CP: _found("Community Patch"),
                               "Other-9-1-1700000000.zip": None})
        self.assertEqual([o["name"] for o in downloads.offers(self.folder, [], self.state, {},
                                                              lookup)],
                         ["Community Patch", "QuinnQuest"])

    def test_imported_and_dismissed_archives_are_not_offered_or_asked_about(self):
        self._file(QQ, 1)
        self._file(CP, 2)
        downloads.dismiss(self.state, CP)
        self.assertEqual(downloads.offers(self.folder, [QQ], self.state, {}, self._lookup({})), [])
        self.assertEqual(self.asked, [])

    def test_each_name_is_asked_once_but_offline_is_asked_again(self):
        self._file(QQ, 1)
        known = {}
        offline = self._lookup({QQ: nexus_files.Offline("x")})
        self.assertEqual(downloads.offers(self.folder, [], self.state, known, offline), [])
        found = self._lookup({QQ: _found("QuinnQuest")})
        for _ in range(2):
            self.assertEqual(len(downloads.offers(self.folder, [], self.state, known, found)), 1)
        self.assertEqual(self.asked, [QQ, QQ])

    def test_no_folder_offers_nothing(self):
        self.assertEqual(downloads.offers(None, [], self.state, {}), [])
        self.assertEqual(downloads.offers(os.path.join(self.folder, "gone"), [], self.state, {}),
                         [])


if __name__ == "__main__":
    unittest.main()
