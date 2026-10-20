import json
import os
import tempfile
import unittest

from d4xmm.window import profiles

ORDER = [{"folder": "A", "enabled": True}]


class Profiles(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp()

    def test_the_order_kept_before_profiles_becomes_default(self):
        self.assertEqual(profiles.load(self.home),
                         {"active": "Default", "profiles": {"Default": []}})
        with open(os.path.join(self.home, profiles.OLD_ORDER), "w") as f:
            json.dump(ORDER, f)
        self.assertEqual(profiles.load(self.home)["profiles"]["Default"], ORDER)

    def test_create_switch_and_delete(self):
        data = profiles.load(self.home)
        profiles.create(data, " Big run ", [{"folder": "A", "enabled": 1, "name": "x"}])
        self.assertEqual(data, {"active": "Big run", "profiles": {"Default": [], "Big run": ORDER}})
        for bad in ("Default", " "):
            with self.assertRaises(ValueError):
                profiles.create(data, bad, [])
        profiles.switch(data, "Default")
        profiles.delete(data, "Default")
        self.assertEqual(data["active"], "Big run")
        with self.assertRaises(ValueError):
            profiles.delete(data, "Big run")
        with self.assertRaises(ValueError):
            profiles.switch(data, "missing")


if __name__ == "__main__":
    unittest.main()
