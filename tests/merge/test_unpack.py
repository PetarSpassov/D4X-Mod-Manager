import os
import struct
import tempfile
import unittest

from d4xmm.merge import unpack


def _entry(name, kind, body):
    raw = name.encode()
    return struct.pack("<B", len(raw)) + raw + struct.pack("<B", kind) + body


def _pak(path, files):
    """A pak in the layout d4x_res_pak.bms reads: one root folder holding the given files."""
    data, items = b"", b""
    for name, content in files.items():
        items += _entry(name, 0, struct.pack("<III", len(data), len(content), 0))
        data += content
    tree = _entry("ui", 1, struct.pack("<I", len(files)) + items)
    head_len = 4 + 4 + 4 + 2 + 4
    with open(path, "wb") as f:
        f.write(b"PAK\0" + struct.pack("<IIHI", head_len + len(tree), len(data), 256, 1))
        f.write(tree + data)


class Unpack(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_unpacks_files_under_their_folders(self):
        pak = os.path.join(self.tmp, "res.compressed1.pak")
        _pak(pak, {"a.txt": b"hello", "b.txt": b"world!"})
        dest = os.path.join(self.tmp, "out")
        self.assertEqual(unpack.unpack(pak, dest), ["ui/a.txt", "ui/b.txt"])
        with open(os.path.join(dest, "ui", "b.txt"), "rb") as f:
            self.assertEqual(f.read(), b"world!")

    def test_only_unpacks_the_matching_file(self):
        pak = os.path.join(self.tmp, "res.compressed1.pak")
        _pak(pak, {"a.txt": b"hello", "b.txt": b"world!"})
        self.assertEqual(unpack.unpack(pak, os.path.join(self.tmp, "out"), only="ui/b.txt"),
                         ["ui/b.txt"])

    def test_refuses_an_existing_dest(self):
        with self.assertRaises(FileExistsError):
            unpack.unpack("x.pak", self.tmp)

    def test_not_a_pak_raises(self):
        bad = os.path.join(self.tmp, "bad.pak")
        with open(bad, "wb") as f:
            f.write(b"nope")
        with self.assertRaises(RuntimeError):
            unpack.unpack(bad, os.path.join(self.tmp, "out"))


if __name__ == "__main__":
    unittest.main()
