"""Merging chosen mods into one pak: unpack each, combine assets and data.cdb, rebuild."""
import os

from d4xmm.merge import assets, cdb, pak, unpack

BASE_PAK = "res.compressed.pak"
TRAIT_LIMIT = 2048  # the game crashes past this many rows in `trait`


def _cdb_report(name, d):
    """What one mod's data.cdb diff could not carry over: {sheet: {dropped, no_id}}."""
    out = {}
    for sheet, change in d["sheets"].items():
        if change["dropped"] or change["no_id"]:
            out[sheet] = {"dropped": change["dropped"], "no_id": change["no_id"]}
    return {name: out} if out else {}


def clashes(*owner_maps):
    """What several mods ship, grouped as [{winner, over, items}]; the mod loaded last wins.

    Each map is {item: [mod names in load order]}: asset paths, game files or 'sheet id' rows.
    """
    groups = {}
    for owners in owner_maps:
        for item, names in owners.items():
            over = tuple(n for n in dict.fromkeys(names[:-1]) if n != names[-1])
            if over:
                groups.setdefault((names[-1], over), []).append(item)
    return [{"winner": w, "over": list(o), "items": sorted(i)} for (w, o), i in groups.items()]


def _merge_cdb(unpacked, base_cdb, dest):
    """Apply each mod's data.cdb diff in load order into dest.

    Returns (report, trait rows, {'sheet id': [mods that change or add that row]}).
    """
    base, diffs, report, rows = cdb.load(base_cdb), [], {}, {}
    for name, folder in unpacked:
        path = os.path.join(folder, assets.CDB)
        if os.path.isfile(path):
            diffs.append(cdb.diff(base, cdb.load(path)))
            report.update(_cdb_report(name, diffs[-1]))
            for row in cdb.touched(diffs[-1]):
                rows.setdefault(row, []).append(name)
    if not diffs:
        return report, None, rows
    merged = cdb.apply(base, diffs)
    cdb.save(merged, os.path.join(dest, assets.CDB))
    traits = [s for s in merged["sheets"] if s["name"] == "trait"]
    return report, len(traits[0]["lines"]) if traits else None, rows


def _base_cdb(game_dir, work):
    """The base game's data.cdb, pulled fresh from its pak so a game update is never missed."""
    dest = os.path.join(work, "base")
    unpack.unpack(os.path.join(game_dir, BASE_PAK), dest, only=assets.CDB)
    return os.path.join(dest, assets.CDB)


def merge(mods, game_dir, work):
    """Merge each (name, pak path) in load order into one pak under work, which must not exist.

    Returns the pak, asset and row owners, what data.cdb couldn't carry over, the trait count.
    """
    if os.path.exists(work):
        raise FileExistsError(work)
    unpacked = []
    for i, (name, mod_pak) in enumerate(mods):
        folder = os.path.join(work, "unpacked", str(i))
        unpack.unpack(mod_pak, folder)
        unpacked.append((name, folder))
    merged = os.path.join(work, "merged")
    owners = assets.combine(unpacked, merged)
    os.makedirs(merged, exist_ok=True)
    report, traits, rows = _merge_cdb(unpacked, _base_cdb(game_dir, work), merged)
    return {"pak": pak.build(merged, game_dir), "owners": owners, "rows": rows, "cdb": report,
            "traits": traits, "traits_over": traits is not None and traits > TRAIT_LIMIT}
