import os
import tempfile
import unittest
import zipfile
from unittest import mock

from d4xmm.install import flow
from d4xmm.library import mods


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _read(path):
    with open(path, "rb") as f:
        return f.read()


class InstallMods(unittest.TestCase):
    def setUp(self):
        self.game, self.state, self.lib, self.zips = (tempfile.mkdtemp() for _ in range(4))
        _write(os.path.join(self.game, "hlboot.dat"), b"stock gl")
        _write(os.path.join(self.game, "hlbootdx.dat"), b"stock dx")
        self.merged = []

    def _import(self, name, files):
        path = os.path.join(self.zips, name + ".zip")
        with zipfile.ZipFile(path, "w") as z:
            for member, data in files.items():
                z.writestr(member, data)
        mods.import_archive(path, self.lib)
        return name  # the library folder, named after the zip

    def _fake_merge(self, paks, game_dir, work):
        """Stands in for merge.merge, which needs the real game: joins the paks' bytes."""
        self.merged.append([name for name, _ in paks])
        os.makedirs(work)
        out = os.path.join(work, "res.compressed1.pak")
        _write(out, b"+".join(_read(p) for _, p in paks))
        return {"pak": out}

    def _install(self, *folders):
        with mock.patch("d4xmm.merge.merge", self._fake_merge):
            return flow.install_mods(self.game, self.state, self.lib, list(folders))

    def test_paks_are_merged_in_load_order_and_other_files_later_mod_wins(self):
        a = self._import("A", {"res.compressed1.pak": b"pakA", "Audio/UI.bnk": b"uiA"})
        b = self._import("B", {"res.compressed1.pak": b"pakB", "Audio/UI.bnk": b"uiB"})
        out = self._install(b, a)
        self.assertEqual(self.merged, [["B", "A"]])
        self.assertEqual(_read(os.path.join(self.game, "res.compressed1.pak")), b"pakB+pakA")
        self.assertEqual(_read(os.path.join(self.game, "res", "Audio", "UI.bnk")), b"uiA")
        self.assertEqual(out["owners"], {"res/Audio/UI.bnk": ["B", "A"]})

    def test_a_second_install_replaces_the_first_and_restore_clears_it(self):
        a = self._import("A", {"res.compressed1.pak": b"pakA", "Audio/One.bnk": b"one"})
        b = self._import("B", {"Audio/Two.bnk": b"two"})
        self._install(a)
        out = self._install(b)
        self.assertEqual((out["merge"], out["skipped"]), (None, []))
        self.assertFalse(os.path.exists(os.path.join(self.game, "res.compressed1.pak")))
        self.assertFalse(os.path.exists(os.path.join(self.game, "res", "Audio", "One.bnk")))
        self.assertTrue(os.path.exists(os.path.join(self.game, "res", "Audio", "Two.bnk")))

    def test_a_failed_merge_leaves_the_earlier_install_in_place(self):
        a = self._import("A", {"res.compressed1.pak": b"pakA"})
        self._install(a)
        with mock.patch("d4xmm.merge.merge", side_effect=RuntimeError("pakBuild failed")):
            with self.assertRaises(RuntimeError):
                flow.install_mods(self.game, self.state, self.lib, [a])
        self.assertEqual(_read(os.path.join(self.game, "res.compressed1.pak")), b"pakA")


if __name__ == "__main__":
    unittest.main()
