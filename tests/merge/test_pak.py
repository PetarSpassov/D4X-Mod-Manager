import os
import tempfile
import unittest

from d4xmm.game import steam
from d4xmm.merge import pak, unpack

GAME = steam.find()


class Build(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.merged = os.path.join(self.tmp, "merged")
        os.makedirs(os.path.join(self.merged, "ui"))
        with open(os.path.join(self.merged, "ui", "a.txt"), "wb") as f:
            f.write(b"hello")

    def test_no_game_exe_raises(self):
        with self.assertRaises(FileNotFoundError):
            pak.build(self.merged, self.tmp)

    @unittest.skipUnless(GAME, "needs the installed game's D4X.exe")
    def test_built_pak_unpacks_to_the_same_files(self):
        out = pak.build(self.merged, GAME)
        self.assertEqual(out, os.path.join(self.tmp, "res.compressed1.pak"))
        self.assertEqual(unpack.unpack(out, os.path.join(self.tmp, "u")), ["ui/a.txt"])

    @unittest.skipUnless(GAME, "needs the installed game's D4X.exe")
    def test_refuses_to_overwrite_a_pak(self):
        open(os.path.join(self.tmp, "res.compressed1.pak"), "wb").close()
        with self.assertRaises(FileExistsError):
            pak.build(self.merged, GAME)


if __name__ == "__main__":
    unittest.main()
