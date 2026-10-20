import os
import tempfile
import unittest

from d4xmm.merge import assets


def _mod(root, name, files):
    folder = os.path.join(root, name)
    for path, data in files.items():
        full = os.path.join(folder, *path.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
    return name, folder


def _read(dest, path):
    with open(os.path.join(dest, *path.split("/")), "rb") as f:
        return f.read()


class Combine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dest = os.path.join(self.tmp, "merged")

    def test_later_mod_wins_a_shared_path_and_both_are_named(self):
        a = _mod(self.tmp, "A", {"ui/icon.png": b"a", "ui/a.png": b"only a"})
        b = _mod(self.tmp, "B", {"ui/icon.png": b"b"})
        owners = assets.combine([a, b], self.dest)
        self.assertEqual(_read(self.dest, "ui/icon.png"), b"b")
        self.assertEqual(_read(self.dest, "ui/a.png"), b"only a")
        self.assertEqual(owners, {"ui/icon.png": ["A", "B"], "ui/a.png": ["A"]})

    def test_load_order_decides_not_name(self):
        a = _mod(self.tmp, "A", {"x.png": b"a"})
        b = _mod(self.tmp, "B", {"x.png": b"b"})
        assets.combine([b, a], self.dest)
        self.assertEqual(_read(self.dest, "x.png"), b"a")

    def test_data_cdb_is_left_for_the_row_merge(self):
        a = _mod(self.tmp, "A", {"data.cdb": b"{}", "ui/x.png": b"x"})
        self.assertEqual(assets.combine([a], self.dest), {"ui/x.png": ["A"]})
        self.assertFalse(os.path.exists(os.path.join(self.dest, "data.cdb")))

    def test_refuses_an_existing_dest(self):
        os.makedirs(self.dest)
        with self.assertRaises(FileExistsError):
            assets.combine([], self.dest)


if __name__ == "__main__":
    unittest.main()
