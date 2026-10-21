import unittest

from d4xmm.nexus import catalog


def _node(mod_id):
    return {"modId": mod_id, "name": "Mod %d" % mod_id, "summary": "s", "pictureUrl": "p",
            "thumbnailUrl": "t", "downloads": 9, "endorsements": 2, "version": "1.0",
            "updatedAt": "2026-05-28T22:22:25Z", "uploader": {"name": "PeterQuinn98"}}


def _fake(total, nodes):
    """A stand-in for files.post serving nodes in pages, and the offsets it was asked for."""
    asked = []

    def post(_, variables):
        asked.append(variables["offset"])
        page = nodes[variables["offset"]:variables["offset"] + variables["count"]]
        return {"mods": {"totalCount": total, "nodes": page}}
    return post, asked


class Browse(unittest.TestCase):
    def test_gives_each_mod_in_the_library_names(self):
        post, _ = _fake(1, [_node(5)])
        self.assertEqual(catalog.browse(post), [{
            "nexus_id": 5, "name": "Mod 5", "version": "1.0", "creator": "PeterQuinn98",
            "summary": "s", "picture": "p", "thumbnail": "t", "downloads": 9, "endorsements": 2,
            "updated": "2026-05-28T22:22:25Z"}])

    def test_asks_page_after_page_until_it_has_them_all(self):
        post, asked = _fake(catalog.PAGE + 1, [_node(i) for i in range(catalog.PAGE + 1)])
        self.assertEqual(len(catalog.browse(post)), catalog.PAGE + 1)
        self.assertEqual(asked, [0, catalog.PAGE])

    def test_stops_on_an_empty_page_even_if_the_total_says_more(self):
        post, asked = _fake(10, [])
        self.assertEqual(catalog.browse(post), [])
        self.assertEqual(asked, [0])

    def test_a_mod_without_an_uploader_has_no_creator(self):
        post, _ = _fake(1, [dict(_node(1), uploader=None)])
        self.assertIsNone(catalog.browse(post)[0]["creator"])


if __name__ == "__main__":
    unittest.main()
