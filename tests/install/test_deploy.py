import os
import tempfile
import unittest

from d4xmm.install import deploy


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _read(path):
    with open(path, "rb") as f:
        return f.read()


class InstallRestore(unittest.TestCase):
    def setUp(self):
        self.game, self.state, self.mods = (tempfile.mkdtemp() for _ in range(3))
        _write(os.path.join(self.game, "hlboot.dat"), b"stock gl")
        _write(os.path.join(self.game, "hlbootdx.dat"), b"stock dx")
        _write(os.path.join(self.game, "res", "Audio", "UI.bnk"), b"stock ui")

    def _mod(self, name, data):
        path = os.path.join(self.mods, name)
        _write(path, data)
        return path

    def _install(self, files):
        return deploy.install(self.game, self.state, {k: self._mod(k, v) for k, v in files.items()})

    def test_restore_puts_the_game_back(self):
        self._install({"res.compressed1.pak": b"mod pak", "res/Audio/UI.bnk": b"mod ui"})
        self.assertEqual(_read(os.path.join(self.game, "res/Audio/UI.bnk")), b"mod ui")
        self.assertEqual(deploy.restore(self.game, self.state), [])
        self.assertFalse(os.path.exists(os.path.join(self.game, "res.compressed1.pak")))
        self.assertEqual(_read(os.path.join(self.game, "res/Audio/UI.bnk")), b"stock ui")
        self.assertEqual(os.listdir(self.state), [])

    def test_a_mod_that_replaces_hlboot_is_undone(self):
        self._install({"hlboot.dat": b"mod gl"})
        deploy.restore(self.game, self.state)
        self.assertEqual(_read(os.path.join(self.game, "hlboot.dat")), b"stock gl")

    def test_hlboot_is_backed_up_even_when_no_mod_replaces_it(self):
        record = self._install({"res.compressed1.pak": b"mod pak"})
        self.assertIn("hlbootdx.dat", [e["path"] for e in record])
        self.assertEqual(_read(os.path.join(self.state, "backup", "hlbootdx.dat")), b"stock dx")

    def test_a_file_changed_since_is_left_alone(self):
        self._install({"hlboot.dat": b"mod gl"})
        _write(os.path.join(self.game, "hlboot.dat"), b"steam update")
        self.assertEqual(deploy.restore(self.game, self.state), ["hlboot.dat"])
        self.assertEqual(_read(os.path.join(self.game, "hlboot.dat")), b"steam update")

    def test_second_install_refused_until_restored(self):
        self._install({"res.compressed1.pak": b"mod pak"})
        with self.assertRaises(deploy.InstallError):
            self._install({"res.compressed1.pak": b"other pak"})
        deploy.restore(self.game, self.state)
        self._install({"res.compressed1.pak": b"other pak"})

    def test_restore_with_nothing_installed_does_nothing(self):
        self.assertEqual(deploy.restore(self.game, self.state), [])
