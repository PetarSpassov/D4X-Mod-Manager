import copy
import os
import tempfile
import unittest

from d4xmm import merge
from d4xmm.game import steam
from d4xmm.merge import cdb, pak, unpack

GAME = steam.find()


def _write(folder, files):
    for rel, content in files.items():
        path = os.path.join(folder, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(content, dict):
            cdb.save(content, path)
        else:
            with open(path, "wb") as f:
                f.write(content)


def _traits(data):
    return [s for s in data["sheets"] if s["name"] == "trait"][0]["lines"]


class Clashes(unittest.TestCase):
    def test_items_group_by_the_mod_that_wins_and_the_mods_it_overrides(self):
        out = merge.clashes({"ui/a.png": ["A", "B"], "ui/solo.png": ["A"]},
                            {"trait X": ["A", "B"], "trait Y": ["A", "C", "B"]})
        self.assertEqual(out, [{"winner": "B", "over": ["A"], "items": ["trait X", "ui/a.png"]},
                               {"winner": "B", "over": ["A", "C"], "items": ["trait Y"]}])


@unittest.skipUnless(GAME, "needs the installed game")
class Merge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = os.path.join(tempfile.mkdtemp(), "base")
        unpack.unpack(os.path.join(GAME, merge.BASE_PAK), tmp, only="data.cdb")
        cls.base = cdb.load(os.path.join(tmp, "data.cdb"))

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _mod_pak(self, name, files):
        """A mod's pak, built the way the game builds one."""
        folder = os.path.join(self.tmp, "src", name, "res")
        _write(folder, files)
        return name, pak.build(folder, GAME)

    def test_refuses_an_existing_work_folder(self):
        with self.assertRaises(FileExistsError):
            merge.merge([], GAME, self.tmp)

    def test_two_mods_merge_into_one_pak_against_the_games_own_data_cdb(self):
        mod = copy.deepcopy(self.base)
        rows = _traits(mod)
        dropped = rows.pop()["id"]
        rows.append(dict(rows[0], id="TestNewTrait"))
        one = self._mod_pak("one", {"ui/a.txt": b"one", "ui/b.txt": b"one", "data.cdb": mod})
        two = self._mod_pak("two", {"ui/a.txt": b"two"})
        out = merge.merge([one, two], GAME, os.path.join(self.tmp, "work"))
        self.assertEqual(out["owners"]["ui/a.txt"], ["one", "two"])
        self.assertEqual(out["rows"], {"trait TestNewTrait": ["one"]})
        self.assertEqual(out["cdb"], {"one": {"trait": {"dropped": [dropped], "no_id": 0}}})
        self.assertEqual((out["traits"], out["traits_over"]), (len(_traits(self.base)) + 1, False))
        self.assertEqual((out["traits_added"], out["trait_limit"]), ({"one": 1}, 16384))
        back = os.path.join(self.tmp, "back")
        self.assertEqual(unpack.unpack(out["pak"], back), ["data.cdb", "ui/a.txt", "ui/b.txt"])
        with open(os.path.join(back, "ui", "a.txt"), "rb") as f:
            self.assertEqual(f.read(), b"two")
        ids = [r["id"] for r in _traits(cdb.load(os.path.join(back, "data.cdb")))]
        # the new row follows the row before it in the mod, so it lands before the kept one
        self.assertEqual(ids[-2:], ["TestNewTrait", dropped])

    def test_no_mod_data_cdb_leaves_it_out(self):
        one = self._mod_pak("one", {"ui/a.txt": b"one"})
        out = merge.merge([one], GAME, os.path.join(self.tmp, "work"))
        self.assertEqual((out["cdb"], out["traits"]), ({}, None))
        self.assertEqual(unpack.unpack(out["pak"], os.path.join(self.tmp, "back")), ["ui/a.txt"])


if __name__ == "__main__":
    unittest.main()
