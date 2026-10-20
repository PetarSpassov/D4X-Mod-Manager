import copy
import os
import tempfile
import unittest

from d4xmm.merge import cdb

COLS = [{"typeStr": "0", "name": "id"}, {"typeStr": "3", "name": "cost"},
        {"typeStr": "5:Bonus,Malus", "name": "type"}]


def _base():
    return {"sheets": [{"name": "trait", "columns": copy.deepcopy(COLS), "props": {},
                        "separators": [],
                        "lines": [{"id": "Fast", "cost": 1, "type": 0},
                                  {"id": "Slow", "cost": 2, "type": 1, "tags": ["x"]}]}],
            "customTypes": [], "compress": False}


def _mod(edit):
    mod = _base()
    edit(mod["sheets"][0])
    return mod


def _rows(cdb_):
    return {r["id"]: r for r in cdb_["sheets"][0]["lines"]}


class Merge(unittest.TestCase):
    def merge(self, *edits):
        base = _base()
        return cdb.apply(base, [cdb.diff(base, _mod(e)) for e in edits])

    def test_two_mods_changing_different_fields_of_one_row_both_count(self):
        merged = self.merge(lambda s: s["lines"][0].update(cost=5),
                            lambda s: s["lines"][0].update(type=1))
        self.assertEqual(_rows(merged)["Fast"], {"id": "Fast", "cost": 5, "type": 1})

    def test_on_the_same_field_the_later_mod_wins(self):
        merged = self.merge(lambda s: s["lines"][0].update(cost=5),
                            lambda s: s["lines"][0].update(cost=9))
        self.assertEqual(_rows(merged)["Fast"]["cost"], 9)

    def test_an_untouched_field_never_reverts_another_mods_change(self):
        merged = self.merge(lambda s: s["lines"][1].update(cost=7),
                            lambda s: s["lines"].append({"id": "New", "cost": 0}))
        self.assertEqual(_rows(merged)["Slow"]["cost"], 7)
        self.assertIn("New", _rows(merged))

    def test_a_new_row_lands_after_the_row_before_it_in_the_mod(self):
        merged = self.merge(lambda s: s["lines"].insert(1, {"id": "Mid", "cost": 3}))
        self.assertEqual([r["id"] for r in merged["sheets"][0]["lines"]], ["Fast", "Mid", "Slow"])

    def test_a_new_column_lands_after_the_column_before_it(self):
        merged = self.merge(lambda s: s["columns"].insert(1, {"typeStr": "1", "name": "note"}))
        self.assertEqual([c["name"] for c in merged["sheets"][0]["columns"]],
                         ["id", "note", "cost", "type"])

    def test_separators_are_taken_whole_from_the_later_mod(self):
        merged = self.merge(lambda s: s.update(separators=[{"title": "A", "id": "Fast"}]),
                            lambda s: s.update(separators=[{"title": "B", "id": "Slow"}]))
        self.assertEqual(merged["sheets"][0]["separators"], [{"title": "B", "id": "Slow"}])

    def test_a_removed_field_is_removed(self):
        merged = self.merge(lambda s: s["lines"][1].pop("tags"))
        self.assertNotIn("tags", _rows(merged)["Slow"])

    def test_the_same_new_row_from_two_mods_is_kept_once_later_wins(self):
        merged = self.merge(lambda s: s["lines"].append({"id": "New", "cost": 1}),
                            lambda s: s["lines"].append({"id": "New", "cost": 2}))
        self.assertEqual([r["id"] for r in merged["sheets"][0]["lines"]], ["Fast", "Slow", "New"])
        self.assertEqual(_rows(merged)["New"]["cost"], 2)

    def test_new_sheets_columns_and_enum_values_are_added(self):
        def edit(s):
            s["columns"][2]["typeStr"] = "5:Bonus,Malus,Neutral"
            s["columns"].append({"typeStr": "1", "name": "note"})
        mod = _mod(edit)
        mod["sheets"].append({"name": "extra", "columns": [], "lines": [], "props": {}})
        base = _base()
        merged = cdb.apply(base, [cdb.diff(base, mod)])
        cols = merged["sheets"][0]["columns"]
        self.assertEqual([c["name"] for c in cols], ["id", "cost", "type", "note"])
        self.assertEqual(cols[2]["typeStr"], "5:Bonus,Malus,Neutral")
        self.assertEqual([s["name"] for s in merged["sheets"]], ["trait", "extra"])

    def test_dropped_rows_are_reported_and_kept(self):
        base = _base()
        d = cdb.diff(base, _mod(lambda s: s["lines"].pop(0)))
        self.assertEqual(d["sheets"]["trait"]["dropped"], ["Fast"])
        self.assertIn("Fast", _rows(cdb.apply(base, [d])))

    def test_an_unchanged_mod_changes_nothing_and_base_is_untouched(self):
        base = _base()
        merged = cdb.apply(base, [cdb.diff(base, _base())])
        self.assertEqual(merged, _base())
        self.assertIsNot(merged, base)


class SaveLoad(unittest.TestCase):
    def test_round_trip_uses_tabs_and_lf(self):
        path = os.path.join(tempfile.mkdtemp(), "data.cdb")
        cdb.save(_base(), path)
        with open(path, "rb") as f:
            raw = f.read()
        self.assertTrue(raw.startswith(b'{\n\t"sheets"'))
        self.assertNotIn(b"\r", raw)
        self.assertEqual(cdb.load(path), _base())


if __name__ == "__main__":
    unittest.main()
