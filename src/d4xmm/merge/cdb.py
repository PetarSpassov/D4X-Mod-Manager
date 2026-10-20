"""Merging data.cdb: each mod's changes against the base game, applied in load order.

Sheets match by name, rows by `id`, fields one by one; a list field counts as one field.
"""
import copy
import json

ID = "id"
MISSING = object()  # a field the mod removed from a row
META = ("props", "separators")  # a sheet's editor settings: taken whole, the later mod wins


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(cdb, path):
    """Write in CastleDB's own layout: tab indents, LF, no BOM."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(cdb, indent="\t", ensure_ascii=False))


def _by_name(items):
    return {i["name"]: i for i in items}


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


def _place(items, adds, key):
    """Each (previous key, item): replace the item with its key, else insert after previous."""
    for prev, item in adds:
        keys = [i.get(key) for i in items]
        if item[key] in keys:
            items[keys.index(item[key])] = copy.deepcopy(item)
        else:
            at = keys.index(prev) + 1 if prev in keys else len(items)
            items.insert(at, copy.deepcopy(item))


def _apply_sheet(sheet, change):
    _place(sheet["columns"], change["columns"], "name")
    sheet.update(copy.deepcopy(change["meta"]))
    rows = {r.get(ID): r for r in sheet["lines"]}
    for rid, fields in change["fields"].items():
        row = rows[rid]
        for k, v in fields.items():
            if v is MISSING:
                row.pop(k, None)
            else:
                row[k] = copy.deepcopy(v)
    _place(sheet["lines"], change["add"], ID)


def apply(base, diffs):
    """The base with each diff applied in load order; a later mod wins the same field."""
    merged = copy.deepcopy(base)
    for d in diffs:
        _place(merged["customTypes"], d["types"], "name")
        _place(merged["sheets"], d["new_sheets"], "name")
        sheets = _by_name(merged["sheets"])
        for name, change in d["sheets"].items():
            _apply_sheet(sheets[name], change)
    return merged
