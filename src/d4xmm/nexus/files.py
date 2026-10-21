"""Which Nexus file a downloaded archive is, found by its exact name through the keyless API."""
import json
import re
import urllib.error
import urllib.request

API = "https://api.nexusmods.com/v2/graphql"
GAME_ID = 7811  # Dune: Spice Wars
TIMEOUT = 10
# what Nexus says about the mod as a whole; `updated` is an ISO time, the others text or counts
ABOUT = ("creator", "summary", "picture", "downloads", "endorsements", "updated")
QUERY = ("query($mod: ID!, $game: ID!) { mod(modId: $mod, gameId: $game) "
         "{ name summary pictureUrl uploader { name } downloads endorsements updatedAt } "
         "modFiles(modId: $mod, gameId: $game) { fileId name version uri category } }")


class Offline(Exception):
    """Nexus could not be reached."""


class Refused(Exception):
    """Nexus was reached but answered with an error."""


def post(query, variables):
    """The answer's data, {} when Nexus found nothing. Raises Offline or Refused."""
    body = json.dumps({"query": query, "variables": variables}).encode()
    # Nexus answers Python's default User-Agent with 403
    req = urllib.request.Request(API, body, {"Content-Type": "application/json",
                                             "User-Agent": "D4XModManager"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.load(r).get("data") or {}  # no such mod: the errors leave data null
    except urllib.error.HTTPError as e:  # an HTTPError is a URLError, so it is caught first
        raise Refused(str(e)) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise Offline(str(e)) from e


def _mod(mod_id):
    """{name and each of ABOUT: the mod's own, None if missing; files: [its file records]}."""
    data = post(QUERY, {"mod": mod_id, "game": GAME_ID})
    found = data.get("mod") or {}
    return {"name": found.get("name"), "creator": (found.get("uploader") or {}).get("name"),
            "summary": found.get("summary"), "picture": found.get("pictureUrl"),
            "downloads": found.get("downloads"), "endorsements": found.get("endorsements"),
            "updated": found.get("updatedAt"), "files": data.get("modFiles") or []}


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
                        **{k: found.get(k) for k in ABOUT}}
    return None
