import os
import tempfile
import unittest

from d4xmm import merge
from d4xmm.game import steam
from d4xmm.merge import cdb, pak, unpack

GAME = steam.find()


def _sheet(name, rows):
    return {"name": name, "columns": [{"name": "id"}], "lines": [{"id": r} for r in rows]}


def _cdb(*sheets):
    return {"sheets": list(sheets), "customTypes": []}


def _write(folder, files):
    for rel, content in files.items():
        path = os.path.join(folder, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(content, dict):
            cdb.save(content, path)
        else:
            with open(path, "wb") as f:
                f.write(content)


class Merge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.base = os.path.join(self.tmp, "base.cdb")
        cdb.save(_cdb(_sheet("trait", ["a", "b"]), _sheet("unit", ["u", "v"])), self.base)

    def _mod_pak(self, name, files):
        """A mod's pak, built the way the game builds one."""
        folder = os.path.join(self.tmp, "src", name, "res")
        _write(folder, files)
        return name, pak.build(folder, GAME)

    def test_refuses_an_existing_work_folder(self):
        with self.assertRaises(FileExistsError):
            merge.merge([], self.base, self.tmp, self.tmp)

    @unittest.skipUnless(GAME, "needs the installed game's D4X.exe")
    def test_two_mods_merge_into_one_pak(self):
        one = self._mod_pak("one", {"ui/a.txt": b"one", "ui/b.txt": b"one",
                                    "data.cdb": _cdb(_sheet("trait", ["a", "b", "c"]),
                                                     _sheet("unit", ["u"]))})
        two = self._mod_pak("two", {"ui/a.txt": b"two"})
        out = merge.merge([one, two], self.base, GAME, os.path.join(self.tmp, "work"))
        self.assertEqual(out["owners"]["ui/a.txt"], ["one", "two"])
        self.assertEqual(out["cdb"], {"one": {"unit": {"dropped": ["v"], "no_id": 0}}})
        self.assertEqual((out["traits"], out["traits_over"]), (3, False))
        back = os.path.join(self.tmp, "back")
        self.assertEqual(unpack.unpack(out["pak"], back), ["data.cdb", "ui/a.txt", "ui/b.txt"])
        with open(os.path.join(back, "ui", "a.txt"), "rb") as f:
            self.assertEqual(f.read(), b"two")
        self.assertEqual([r["id"] for r in cdb.load(os.path.join(back, "data.cdb"))
                          ["sheets"][1]["lines"]], ["u", "v"])

    @unittest.skipUnless(GAME, "needs the installed game's D4X.exe")
    def test_no_mod_data_cdb_leaves_it_out(self):
        one = self._mod_pak("one", {"ui/a.txt": b"one"})
        out = merge.merge([one], self.base, GAME, os.path.join(self.tmp, "work"))
        self.assertEqual((out["cdb"], out["traits"]), ({}, None))
        self.assertEqual(unpack.unpack(out["pak"], os.path.join(self.tmp, "back")), ["ui/a.txt"])


if __name__ == "__main__":
    unittest.main()
