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


def _add_sep(title, rid):
    return lambda s: s["separators"].append({"title": title, "id": rid})


def _rows(cdb_):
    return {r["id"]: r for r in cdb_["sheets"][0]["lines"]}


class Merge(unittest.TestCase):
    def merge(self, *edits):
        base = _base()
        return cdb.apply(base, [cdb.diff(base, _mod(e)) for e in edits])

    def test_a_row_two_mods_change_is_the_later_mods_whole_row(self):
        merged = self.merge(lambda s: s["lines"][0].update(cost=5),
                            lambda s: s["lines"][0].update(type=1))
        self.assertEqual(_rows(merged)["Fast"], {"id": "Fast", "cost": 1, "type": 1})

    def test_a_field_the_mod_removed_stays_removed(self):
        merged = self.merge(lambda s: s["lines"][1].pop("tags"))
        self.assertNotIn("tags", _rows(merged)["Slow"])

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

    def test_a_later_mods_row_sits_under_an_earlier_mods_row_in_the_same_spot(self):
        merged = self.merge(lambda s: s["lines"].insert(1, {"id": "A1"}),
                            lambda s: s["lines"].insert(1, {"id": "B1"}))
        self.assertEqual([r["id"] for r in merged["sheets"][0]["lines"]],
                         ["Fast", "A1", "B1", "Slow"])

    def test_a_new_first_row_stays_first_not_appended(self):
        merged = self.merge(lambda s: s["lines"].insert(0, {"id": "Top"}))
        self.assertEqual([r["id"] for r in merged["sheets"][0]["lines"]], ["Top", "Fast", "Slow"])

    def _after_count(self, sheet_name):
        base = _base()
        base["sheets"][0].update(name=sheet_name)
        base["sheets"][0]["lines"].append({"id": "Count"})
        mod = copy.deepcopy(base)
        mod["sheets"][0]["lines"].append({"id": "Late"})
        return [r["id"] for r in cdb.apply(base, [cdb.diff(base, mod)])["sheets"][0]["lines"]]

    def test_traits_count_row_stays_last(self):
        self.assertEqual(self._after_count("trait"), ["Fast", "Slow", "Late", "Count"])

    def test_attributes_count_row_may_move(self):
        self.assertEqual(self._after_count("attribute"), ["Fast", "Slow", "Count", "Late"])

    def test_a_new_column_lands_after_the_column_before_it(self):
        merged = self.merge(lambda s: s["columns"].insert(1, {"typeStr": "1", "name": "note"}))
        self.assertEqual([c["name"] for c in merged["sheets"][0]["columns"]],
                         ["id", "note", "cost", "type"])

    def _seps(self, base_seps, *edits):
        base = _base()
        base["sheets"][0]["separators"] = base_seps
        mods = []
        for edit in edits:
            mods.append(copy.deepcopy(base))
            edit(mods[-1]["sheets"][0])
        merged = cdb.apply(base, [cdb.diff(base, m) for m in mods])
        return [(s.get("title"), s["id"]) for s in merged["sheets"][0]["separators"]]

    def test_every_mods_separators_are_kept_in_row_order(self):
        self.assertEqual(self._seps([], _add_sep("A", "Slow"), _add_sep("B", "Fast")),
                         [("B", "Fast"), ("A", "Slow")])

    def test_a_renamed_separator_replaces_the_old_one(self):
        self.assertEqual(self._seps([{"title": "Old", "id": "Fast"}],
                                    lambda s: s["separators"][0].update(title="New")),
                         [("New", "Fast")])

    def test_separators_on_one_row_keep_their_order_later_mod_below(self):
        self.assertEqual(self._seps([{"title": "P", "id": "Fast"}],
                                    _add_sep("C1", "Fast"), _add_sep("C2", "Fast")),
                         [("P", "Fast"), ("C1", "Fast"), ("C2", "Fast")])

    def test_a_separator_on_a_mods_new_row_sits_at_that_row(self):
        def edit(s):
            s["lines"].insert(1, {"id": "Mid"})
            s["separators"].append({"title": "M", "id": "Mid"})
        self.assertEqual(self._seps([{"title": "S", "id": "Slow"}], edit),
                         [("M", "Mid"), ("S", "Slow")])

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
