"""Which Nexus file a downloaded archive is, found by its exact name through the keyless API."""
import json
import re
import urllib.error
import urllib.request

API = "https://api.nexusmods.com/v2/graphql"
GAME_ID = 7811  # Dune: Spice Wars
TIMEOUT = 10
QUERY = ("query($mod: ID!, $game: ID!) { mod(modId: $mod, gameId: $game) "
         "{ name summary pictureUrl uploader { name } } "
         "modFiles(modId: $mod, gameId: $game) { fileId name version uri category } }")


class Offline(Exception):
    """Nexus could not be reached."""


class Refused(Exception):
    """Nexus was reached but answered with an error."""


def _mod(mod_id):
    """{name, creator, summary, picture: the mod's own, each None if missing; files: [records]}."""
    body = json.dumps({"query": QUERY, "variables": {"mod": mod_id, "game": GAME_ID}}).encode()
    # Nexus answers Python's default User-Agent with 403
    req = urllib.request.Request(API, body, {"Content-Type": "application/json",
                                             "User-Agent": "D4XModManager"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.load(r).get("data") or {}  # no such mod: the errors leave data null
    except urllib.error.HTTPError as e:  # an HTTPError is a URLError, so it is caught first
        raise Refused(str(e)) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise Offline(str(e)) from e
    found = data.get("mod") or {}
    return {"name": found.get("name"), "creator": (found.get("uploader") or {}).get("name"),
            "summary": found.get("summary"), "picture": found.get("pictureUrl"),
            "files": data.get("modFiles") or []}


def lookup(file_name, mod=_mod):
    """The Nexus file named exactly file_name, or None; `latest` is the newest main file's version.

    Raises Offline when Nexus can't be reached, Refused when it answers with an error.
    """
    # the mod id is one of the name's all-digit parts; each is only a candidate until uri matches
    for mod_id in dict.fromkeys(re.findall(r"(?<=-)\d+(?=-)", file_name)):
        found = mod(mod_id)
        mains = [f for f in found["files"] if f["category"] == "MAIN"]
        latest = max(mains, key=lambda f: f["fileId"])["version"] if mains else None
        for f in found["files"]:
            if f["uri"] == file_name:
                return {"nexus_id": int(mod_id), "file_id": f["fileId"], "name": f["name"],
                        "mod_name": found["name"] or f["name"], "version": f["version"],
                        "category": f["category"], "latest": latest,
                        "creator": found.get("creator"), "summary": found.get("summary"),
                        "picture": found.get("picture")}
    return None
