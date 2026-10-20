"""Merging chosen mods into one pak: unpack each, combine assets and data.cdb, rebuild."""
import os

from d4xmm.merge import assets, cdb, pak, unpack

TRAIT_LIMIT = 2048  # the game crashes past this many rows in `trait`


def _cdb_report(name, d):
    """What one mod's data.cdb diff could not carry over: {sheet: {dropped, no_id}}."""
    out = {}
    for sheet, change in d["sheets"].items():
        if change["dropped"] or change["no_id"]:
            out[sheet] = {"dropped": change["dropped"], "no_id": change["no_id"]}
    return {name: out} if out else {}


def _merge_cdb(unpacked, base_cdb, dest):
    """Apply each mod's data.cdb diff in load order into dest; returns (report, trait rows)."""
    base, diffs, report = cdb.load(base_cdb), [], {}
    for name, folder in unpacked:
        path = os.path.join(folder, assets.CDB)
        if os.path.isfile(path):
            diffs.append(cdb.diff(base, cdb.load(path)))
            report.update(_cdb_report(name, diffs[-1]))
    if not diffs:
        return report, None
    merged = cdb.apply(base, diffs)
    cdb.save(merged, os.path.join(dest, assets.CDB))
    traits = [s for s in merged["sheets"] if s["name"] == "trait"]
    return report, len(traits[0]["lines"]) if traits else None


def merge(mods, base_cdb, game_dir, work):
    """Merge each (name, pak path) in load order into one pak under work, which must not exist.

    Returns the pak, asset owners, what data.cdb couldn't carry over, and the trait count.
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
    report, traits = _merge_cdb(unpacked, base_cdb, merged)
    return {"pak": pak.build(merged, game_dir), "owners": owners, "cdb": report,
            "traits": traits, "traits_over": traits is not None and traits > TRAIT_LIMIT}
