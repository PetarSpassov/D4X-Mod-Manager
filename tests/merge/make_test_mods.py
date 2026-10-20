"""Build two test mods from the installed game's data.cdb, then merge them for real and check.

Run with PYTHONPATH=src; writes build/test_mods/D4XMM_Test1.zip and _Test2.zip for the app.
"""
import copy
import json
import os
import sys
import tempfile
import zipfile

from d4xmm import merge
from d4xmm.game import steam
from d4xmm.install import flow
from d4xmm.library import mods
from d4xmm.merge import cdb, pak, unpack

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "build", "test_mods"))
NAMES = ("D4XMM_Test1", "D4XMM_Test2")
NOTE = "d4xmmNote"


def _sheet(data, name):
    return [s for s in data["sheets"] if s["name"] == name][0]


def _new_row(rows, after, rid, **fields):
    """A copy of the row `after` under a new id, inserted right below it."""
    at = [r["id"] for r in rows].index(after)
    rows.insert(at + 1, dict(copy.deepcopy(rows[at]), id=rid, **fields))


def _picks(base):
    """The base rows each case works on, chosen from the data so a game update can't break it."""
    text = json.dumps(base)
    traits = _sheet(base, "trait")["lines"]
    named = [r["id"] for r in traits[1:] if r.get("name") and r.get("desc")]
    lonely = [r["id"] for r in traits[1:-1] if text.count('"%s"' % r["id"]) == 1]
    return {"first": traits[0]["id"], "fields": named[0], "same": named[1], "both": named[2],
            "end": traits[-2]["id"], "removed": lonely[0]}


def _edit_trait(t, p, n):
    """Cases 1-4 and 6-10 on the trait sheet for mod n (1 or 2)."""
    rows = t["lines"]
    _new_row(rows, p["first"], "D4XMM_T%d_Same" % n, name="D4XMM same spot %d" % n)
    row = {r["id"]: r for r in rows}
    row[p["fields"]]["name" if n == 1 else "desc"] = "D4XMM field from mod %d" % n
    row[p["same"]]["name"] = "D4XMM same field, mod %d" % n
    _new_row(rows, p["both"], "D4XMM_Both", name="D4XMM shared id, mod %d" % n)
    t["separators"].append({"title": "D4XMM Category %d" % n, "id": "D4XMM_T%d_Same" % n})
    if n == 1:
        _new_row(rows, p["end"], "D4XMM_T1_End", name="D4XMM near the end",
                 **{NOTE: "D4XMM new column"})
        t["separators"][1]["title"] = "D4XMM Renamed"
        rows[:] = [r for r in rows if r["id"] != p["removed"]]
        t["columns"].insert(2, {"name": NOTE, "typeStr": "1"})


def _edit_attribute(a, n):
    """Case 5: a custom attribute from each mod, mod 2's below `Invalid`, after `Count`."""
    ids = [r["id"] for r in a["lines"]]
    after = ids[ids.index("Count") - 1] if n == 1 else ids[-1]
    _new_row(a["lines"], after, "D4XMM_A%d" % n, desc="D4XMM custom attribute %d" % n)


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def build_mod(base, p, n, game, work):
    """One mod's zip: its pak (data.cdb plus test assets) and an audio bank. Returns its paths."""
    data = copy.deepcopy(base)
    _edit_trait(_sheet(data, "trait"), p, n)
    _edit_attribute(_sheet(data, "attribute"), n)
    res = os.path.join(work, "mod%d" % n, "res")
    os.makedirs(res)
    cdb.save(data, os.path.join(res, "data.cdb"))
    _write(os.path.join(res, "d4xmm", "both.txt"), b"from mod %d" % n)  # case 11
    if n == 1:
        _write(os.path.join(res, "d4xmm", "only1.txt"), b"only mod 1")  # case 12
    built = pak.build(res, game)
    zip_path = os.path.join(OUT, NAMES[n - 1] + ".zip")
    os.makedirs(OUT, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(built, "res.compressed1.pak")
        z.writestr("Audio/D4XMM_Test.bnk", b"bank from mod %d" % n)  # case 13
    return zip_path, built


def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _row_cases(data, p, first, last):
    """Cases 1-6 against the merged data.cdb, mod `first` loaded before mod `last`."""
    t, a = _sheet(data, "trait"), _sheet(data, "attribute")
    ids, aids = [r["id"] for r in t["lines"]], [r["id"] for r in a["lines"]]
    row = {r["id"]: r for r in t["lines"]}
    return {
        "1 same-spot rows, earlier mod first": ids[1:3] == ["D4XMM_T%d_Same" % first,
                                                           "D4XMM_T%d_Same" % last],
        "2 different fields both kept": (row[p["fields"]]["name"], row[p["fields"]]["desc"])
        == ("D4XMM field from mod 1", "D4XMM field from mod 2"),
        "3 same field, later mod wins": row[p["same"]]["name"] == "D4XMM same field, mod %d" % last,
        "4 near-end row above Count": ids[-2:] == ["D4XMM_T1_End", "Count"],
        "5 attributes in place, Count unmoved": aids[-3:] == ["Count", "Invalid", "D4XMM_A2"]
        and aids[aids.index("Count") - 1] == "D4XMM_A1",
        "6 shared id once, later wins": ids.count("D4XMM_Both") == 1
        and row["D4XMM_Both"]["name"] == "D4XMM shared id, mod %d" % last,
    }


def _sheet_cases(data, p, report):
    """Cases 7-10: categories, the removed row and the new column."""
    t = _sheet(data, "trait")
    ids = [r["id"] for r in t["lines"]]
    at = {rid: i for i, rid in enumerate(ids)}
    titles = [s.get("title") for s in t["separators"]]
    places = [at[s["id"]] for s in t["separators"]]
    both = {"D4XMM Category 1", "D4XMM Category 2"} <= set(titles)
    return {
        "7 both categories, row order": both and places == sorted(places),
        "8 renamed category": "D4XMM Renamed" in titles,
        "9 removed row kept, reported": p["removed"] in ids
        and report["cdb"]["D4XMM_Test1"]["trait"]["dropped"] == [p["removed"]],
        "10 new column": _column_case(t),
    }


def _column_case(t):
    end = [r for r in t["lines"] if r["id"] == "D4XMM_T1_End"][0]
    return NOTE in [c["name"] for c in t["columns"]] and end.get(NOTE) == "D4XMM new column"


def check(p, built, zips, game, order):
    """Merge in `order` (mod numbers) with the real merge; returns {case: passed}."""
    first, last = order
    work = tempfile.mkdtemp()
    report = merge.merge([(NAMES[n - 1], built[n - 1]) for n in order], game,
                         os.path.join(work, "merge"))
    back = os.path.join(work, "back")
    unpack.unpack(report["pak"], back)
    data = cdb.load(os.path.join(back, "data.cdb"))
    cases = dict(_row_cases(data, p, first, last), **_sheet_cases(data, p, report))
    cases["11 shared asset, later wins"] = (
        _read(os.path.join(back, "d4xmm", "both.txt")) == b"from mod %d" % last)
    cases["12 one mod's asset kept"] = (
        _read(os.path.join(back, "d4xmm", "only1.txt")) == b"only mod 1")
    lib = os.path.join(work, "library")
    for z in zips:
        mods.import_archive(z, lib)
    _, files, _ = flow._gather(lib, [NAMES[n - 1] for n in order])
    cases["13 audio bank, later wins"] = (
        _read(files["res/Audio/D4XMM_Test.bnk"]) == b"bank from mod %d" % last)
    return cases


def main():
    game = steam.find()
    if not game:
        sys.exit("the game was not found in Steam")
    work = tempfile.mkdtemp()
    unpack.unpack(os.path.join(game, merge.BASE_PAK), os.path.join(work, "base"), only="data.cdb")
    base = cdb.load(os.path.join(work, "base", "data.cdb"))
    p = _picks(base)
    zips, built = zip(*(build_mod(base, p, n, game, work) for n in (1, 2)))
    failed = 0
    for order in ((1, 2), (2, 1)):  # case 14: the swapped order flips the winners
        for case, ok in check(p, built, zips, game, order).items():
            failed += not ok
            print("%s  order %d,%d  %s" % ("pass" if ok else "FAIL", order[0], order[1], case))
    print("picked rows:", p)
    print("zips:", *zips, sep="\n  ")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
