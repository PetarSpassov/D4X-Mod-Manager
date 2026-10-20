"""Merging data.cdb: each mod's changes against the base game, applied in load order.

Sheets match by name, rows by `id`, fields one by one; a list field counts as one field.
"""
import copy
import json

ID = "id"
MISSING = object()  # a field the mod removed from a row
META = ("props",)  # a sheet's editor settings: taken whole, the later mod wins
LAST_ROW = {"trait": "Count"}  # the game needs this row last; attribute's Count may move


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(cdb, path):
    """Write in CastleDB's own layout: tab indents, LF, no BOM."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(cdb, indent="\t", ensure_ascii=False))


def _by_name(items):
    return {i["name"]: i for i in items}


def _field(name):
    return lambda item: item.get(name)


def _sep_key(sep):
    """A separator as a whole: several can start at the same row, told apart by title or level."""
    return tuple(sorted(sep.items()))


def _seps_diff(old, new):
    """Separators a mod added, each with the one before it, and the ones it removed."""
    before = {_sep_key(s) for s in old}
    after = {_sep_key(s) for s in new}
    add, prev = [], None
    for sep in new:
        if _sep_key(sep) not in before:
            add.append((prev, sep))
        prev = _sep_key(sep)
    return {"seps": add, "seps_gone": [s for s in old if _sep_key(s) not in after]}


def _changed(old, new):
    """(previous name, item) for each item of new that old lacks or holds differently."""
    before, out, prev = _by_name(old), [], None
    for item in new:
        if before.get(item["name"]) != item:
            out.append((prev, item))
        prev = item["name"]
    return out


def _fields(old, new):
    keys = list(old) + [k for k in new if k not in old]
    return {k: new.get(k, MISSING) for k in keys if old.get(k, MISSING) != new.get(k, MISSING)}


def _sheet_diff(old, new):
    """What a mod changed in one sheet; dropped rows and rows with no id are reported only."""
    change = {"columns": _changed(old["columns"], new["columns"]),
              "meta": {k: new[k] for k in META if k in new and new[k] != old.get(k)}}
    change.update(_row_changes(old["lines"], new["lines"]),
                  dropped=_dropped(old["lines"], new["lines"]))
    change.update(_seps_diff(old.get("separators", []), new.get("separators", [])))
    return change if any(change.values()) else None


def _row_changes(old, new):
    base_rows = {r[ID]: r for r in old if r.get(ID)}
    out = {"add": [], "fields": {}, "no_id": 0}
    prev = None
    for row in new:
        rid = row.get(ID)
        if not rid:
            out["no_id"] += 1
        elif rid not in base_rows:
            out["add"].append((prev, row))
        elif row != base_rows[rid]:
            out["fields"][rid] = _fields(base_rows[rid], row)
        prev = rid or prev
    return out


def _dropped(old, new):
    kept = {r.get(ID) for r in new}
    return [r[ID] for r in old if r.get(ID) and r[ID] not in kept]


def diff(base, mod):
    """One mod's changes against the base game's data.cdb."""
    sheets = _by_name(base["sheets"])
    out = {"types": _changed(base["customTypes"], mod["customTypes"]),
           "new_sheets": [], "sheets": {}}
    prev = None
    for sheet in mod["sheets"]:
        if sheet["name"] not in sheets:
            out["new_sheets"].append((prev, sheet))
        else:
            change = _sheet_diff(sheets[sheet["name"]], sheet)
            if change:
                out["sheets"][sheet["name"]] = change
        prev = sheet["name"]
    return out


def _place(items, adds, key, base):
    """Each (previous key, item): replace the item with its key, else insert after previous.

    Past previous, other mods' additions (keys not in base) are stepped over, so they stay above.
    """
    base_keys = {key(i) for i in base}
    for prev, item in adds:
        keys = [key(i) for i in items]
        if key(item) in keys:
            items[keys.index(key(item))] = copy.deepcopy(item)
            continue
        at = keys.index(prev) + 1 if prev in keys else 0
        while at < len(keys) and keys[at] not in base_keys:
            at += 1
        items.insert(at, copy.deepcopy(item))


def _keep_last(sheet):
    """Move the row the game needs at the very end back there, if the sheet has one."""
    rows = sheet["lines"]
    ids = [r.get(ID) for r in rows]
    last = LAST_ROW.get(sheet["name"])
    if last in ids:
        rows.append(rows.pop(ids.index(last)))


def _apply_seps(sheet, change, base):
    """Drop the separators the mod removed, place its new ones, then sort them into row order."""
    seps = [s for s in sheet.get("separators", []) if s not in change["seps_gone"]]
    _place(seps, change["seps"], _sep_key, base.get("separators", []))
    at = {r.get(ID): i for i, r in enumerate(sheet["lines"])}
    seps.sort(key=lambda s: at.get(s.get(ID), len(at)))
    if seps or "separators" in sheet:
        sheet["separators"] = seps


def _apply_sheet(sheet, change, base):
    _place(sheet["columns"], change["columns"], _field("name"), base["columns"])
    sheet.update(copy.deepcopy(change["meta"]))
    rows = {r.get(ID): r for r in sheet["lines"]}
    for rid, fields in change["fields"].items():
        row = rows[rid]
        for k, v in fields.items():
            if v is MISSING:
                row.pop(k, None)
            else:
                row[k] = copy.deepcopy(v)
    _place(sheet["lines"], change["add"], _field(ID), base["lines"])
    _keep_last(sheet)
    _apply_seps(sheet, change, base)


def apply(base, diffs):
    """The base with each diff applied in load order; a later mod wins the same field."""
    merged, base_sheets = copy.deepcopy(base), _by_name(base["sheets"])
    for d in diffs:
        _place(merged["customTypes"], d["types"], _field("name"), base["customTypes"])
        _place(merged["sheets"], d["new_sheets"], _field("name"), base["sheets"])
        sheets = _by_name(merged["sheets"])
        for name, change in d["sheets"].items():
            _apply_sheet(sheets[name], change, base_sheets[name])
    return merged
