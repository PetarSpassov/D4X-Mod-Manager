"""What is proven, not what feels finished: an item's cases are the cross of its axes.

    coverage.py [<item>] [--axes k=a,b ...] [--prove | --fail k=v ... --note "<seen>"]
"""
import itertools
import os
import sys

from _common import ROOT, config, load, now, save, utf8

DATA = os.path.join(ROOT, config().get("coverage") or "docs/coverage.json")


def cells(item):
    axes = item.get("axes") or {}
    names = sorted(axes)
    return [dict(zip(names, combo)) for combo in itertools.product(*(axes[n] for n in names))]


def key(cell):
    return ";".join("%s=%s" % (k, cell[k]) for k in sorted(cell))


def parse_cell(args):
    return dict(a.split("=", 1) for a in args if "=" in a)


def summary():
    items = load(DATA).get("items") or {}
    out = []
    for name, item in sorted(items.items()):
        all_ = cells(item)
        proven = sum(1 for c in all_
                     if (item.get("results") or {}).get(key(c), {}).get("status") == "PROVEN")
        if all_ and proven < len(all_):
            out.append("  %-20s %d of %d cases proven -- the rest have never been shown to work"
                       % (name, proven, len(all_)))
    return out


def show(name, item):
    res = item.get("results") or {}
    axes_text = "; ".join("%s=%s" % (k, ",".join(v)) for k, v in sorted(item["axes"].items()))
    lines = ["%s -- axes: %s" % (name, axes_text)]
    for c in cells(item):
        r = res.get(key(c)) or {}
        lines.append("  %-8s %-40s %s" % (r.get("status", "UNPROVEN"), key(c), r.get("note", "")))
    return "\n".join(lines)


def _declare(items, name, rest):
    kept = (items.get(name) or {}).get("results") or {}
    items[name] = {"axes": {k: v.split(",") for k, v in parse_cell(rest[1:]).items()},
                   "results": kept}


def _record(items, name, rest):
    """A --prove or --fail result for one case; 1 when the case cannot be recorded."""
    if name not in items:
        print("No axes for %s yet; the user declares them with --axes." % name)
        return 1
    note = rest[rest.index("--note") + 1] if "--note" in rest else ""
    cell = parse_cell(rest[1:rest.index("--note")] if "--note" in rest else rest[1:])
    if sorted(cell) != sorted(items[name]["axes"]):
        print("A case names every axis: %s" % ", ".join(sorted(items[name]["axes"])))
        return 1
    items[name].setdefault("results", {})[key(cell)] = {
        "status": "PROVEN" if rest[0] == "--prove" else "FAILED", "note": note, "on": now()}
    return 0


def main(argv):
    utf8()
    data = load(DATA) or {"items": {}}
    items = data.setdefault("items", {})
    if not argv:
        print("\n".join(summary()) or "Every declared case is proven (or nothing is declared).")
        return 0
    name, rest = argv[0], argv[1:]
    if rest and rest[0] == "--axes":
        _declare(items, name, rest)
        save(DATA, data)
    elif rest and rest[0] in ("--prove", "--fail"):
        if _record(items, name, rest):
            return 1
        save(DATA, data)
    if name not in items:
        print("No item %s." % name)
        return 1
    print(show(name, items[name]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
