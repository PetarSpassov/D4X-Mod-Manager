import os
import tempfile
import unittest

from d4xmm.game import hlboot


class Modded(unittest.TestCase):
    def test_reports_only_files_with_a_mark(self):
        game = tempfile.mkdtemp()
        with open(os.path.join(game, "hlboot.dat"), "wb") as f:
            f.write(b"code spineTargets code")
        with open(os.path.join(game, "hlbootdx.dat"), "wb") as f:
            f.write(b"stock code")
        self.assertEqual(hlboot.modded(game), ["hlboot.dat"])

    def test_missing_files_are_not_modded(self):
        self.assertEqual(hlboot.modded(tempfile.mkdtemp()), [])
