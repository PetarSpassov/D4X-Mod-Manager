"""Mod profiles: each a load order with ticks, kept in profiles.json under the home folder.

With no profiles.json yet, the order kept before profiles existed (order.json) becomes "Default".
"""
import json
import os

FILE = "profiles.json"
OLD_ORDER = "order.json"
FIRST = "Default"


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load(home):
    """{"active": a name, "profiles": {name: [{folder, enabled}], first loaded first}}."""
    path = os.path.join(home, FILE)
    if os.path.isfile(path):
        return _read(path)
    old = os.path.join(home, OLD_ORDER)
    return {"active": FIRST, "profiles": {FIRST: _read(old) if os.path.isfile(old) else []}}


def save(home, data):
    with open(os.path.join(home, FILE), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def clean(entries):
    """Only folder and a real bool from each entry the page sends."""
    return [{"folder": e["folder"], "enabled": bool(e["enabled"])} for e in entries]


def create(data, name, entries):
    """Add profile name holding entries and make it the active one."""
    name = name.strip()
    if not name:
        raise ValueError("a profile needs a name")
    if name in data["profiles"]:
        raise ValueError("there is already a profile called %s" % name)
    data["profiles"][name] = clean(entries)
    data["active"] = name


def switch(data, name):
    if name not in data["profiles"]:
        raise ValueError("no profile called %s" % name)
    data["active"] = name


def delete(data, name):
    """Remove profile name; deleting the active one makes the first left active."""
    if name not in data["profiles"]:
        raise ValueError("no profile called %s" % name)
    if len(data["profiles"]) == 1:
        raise ValueError("the last profile can't be deleted")
    del data["profiles"][name]
    if data["active"] == name:
        data["active"] = next(iter(data["profiles"]))
