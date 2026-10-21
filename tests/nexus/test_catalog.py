import unittest

from d4xmm.nexus import catalog


def _node(mod_id):
    return {"modId": mod_id, "name": "Mod %d" % mod_id, "summary": "s", "pictureUrl": "p",
            "thumbnailUrl": "t", "downloads": 9, "endorsements": 2, "version": "1.0",
            "createdAt": "2025-07-19T00:46:49Z", "updatedAt": "2026-05-28T22:22:25Z",
            "uploader": {"name": "PeterQuinn98"}, "description": "[b]Hi[/b]",
            "tags": [{"name": "Gameplay"}, {"name": "Overhaul"}]}


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
            "summary": "s", "description": "Hi", "picture": "p", "thumbnail": "t",
            "downloads": 9, "endorsements": 2, "created": "2025-07-19T00:46:49Z",
            "updated": "2026-05-28T22:22:25Z", "tags": ["Gameplay", "Overhaul"]}])

    def test_asks_page_after_page_until_it_has_them_all(self):
        post, asked = _fake(catalog.PAGE + 1, [_node(i) for i in range(catalog.PAGE + 1)])
        self.assertEqual(len(catalog.browse(post)), catalog.PAGE + 1)
        self.assertEqual(asked, [0, catalog.PAGE])

    def test_stops_on_an_empty_page_even_if_the_total_says_more(self):
        post, asked = _fake(10, [])
        self.assertEqual(catalog.browse(post), [])
        self.assertEqual(asked, [0])

    def test_a_mod_without_an_uploader_tags_or_description_has_none(self):
        post, _ = _fake(1, [dict(_node(1), uploader=None, tags=[], description=None)])
        found = catalog.browse(post)[0]
        self.assertEqual((found["creator"], found["tags"], found["description"]), (None, [], ""))


class Plain(unittest.TestCase):
    def test_a_nexus_description_reads_as_text(self):
        bbcode = ("[size=5][b]Title[/b][/size]\n<br />\n<br />\n<br />\n<br />Join the "
                  "[url=https://discord.gg/x]Discord[/url]!\n<br />[list]\n<br />[*]One &amp; "
                  "two\n<br />[*]Three�\xa0four\n<br />[/list]\n<br />"
                  "[img]https://x/1.jpg[/img]")
        self.assertEqual(catalog.plain(bbcode),
                         "Title\n\nJoin the Discord!\n\n• One & two\n• Three four")


if __name__ == "__main__":
    unittest.main()
