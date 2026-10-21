import os
import queue
import tempfile
import unittest
import uuid
import winreg

from d4xmm.window import links

URL = "nxm://dunespicewars/mods/5/files/30?key=abc&expires=1700000000&user_id=9"


class Parse(unittest.TestCase):
    def test_reads_the_mod_file_and_grant(self):
        self.assertEqual(links.parse(URL), {"game": "dunespicewars", "mod_id": 5, "file_id": 30,
                                            "grant": {"key": "abc", "expires": "1700000000"}})

    def test_anything_else_is_refused(self):
        for bad in ("https://x", "nxm://dunespicewars/mods/5/files/30",
                    "nxm://dunespicewars/mods/5/files/30?key=abc"):
            with self.assertRaises(ValueError):
                links.parse(bad)


class Registry(unittest.TestCase):
    """On a throwaway key of this user's, never the real nxm one."""

    def setUp(self):
        self.root = r"Software\D4XModManagerTest-%s\nxm" % uuid.uuid4().hex
        self.state = tempfile.mkdtemp()

    def tearDown(self):
        parent = self.root.rsplit("\\", 1)[0]
        try:
            links._delete(parent)
        except FileNotFoundError:
            pass  # the test removed it already

    def test_taking_over_from_another_program_and_giving_it_back(self):
        links._write(self.root, '"C:\\Vortex\\Vortex.exe" -d "%1"')
        self.assertEqual(links.status(self.root), {"ours": False, "other": "Vortex.exe"})
        links.take(self.state, self.root)
        self.assertEqual(links.status(self.root), {"ours": True, "other": None})
        links.release(self.state, self.root)
        self.assertEqual(links._read(self.root), '"C:\\Vortex\\Vortex.exe" -d "%1"')
        self.assertEqual(os.listdir(self.state), [])

    def test_with_no_program_before_letting_go_leaves_none(self):
        self.assertEqual(links.status(self.root), {"ours": False, "other": None})
        links.take(self.state, self.root)
        links.release(self.state, self.root)
        self.assertIsNone(links._read(self.root))
        with self.assertRaises(FileNotFoundError):
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.root)


class Handover(unittest.TestCase):
    def test_a_link_reaches_the_open_window(self):
        pipe = r"\\.\pipe\D4XModManagerTest-" + uuid.uuid4().hex
        self.assertFalse(links.send(URL, pipe))
        got = queue.Queue()
        self.assertTrue(links.serve(got.put, pipe))
        self.assertFalse(links.serve(got.put, pipe))  # a second window: the first keeps them
        self.assertTrue(links.send(URL, pipe))
        self.assertEqual(got.get(timeout=5), URL)


if __name__ == "__main__":
    unittest.main()
