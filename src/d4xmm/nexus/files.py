"""Which Nexus file a downloaded archive is, found by its exact name through the keyless API."""
import json
import re
import urllib.error
import urllib.request

API = "https://api.nexusmods.com/v2/graphql"
GAME_ID = 7811  # Dune: Spice Wars
TIMEOUT = 10
QUERY = ("query($mod: ID!, $game: ID!) { mod(modId: $mod, gameId: $game) { name } "
         "modFiles(modId: $mod, gameId: $game) { fileId name version uri category } }")


class Offline(Exception):
    """Nexus could not be reached."""


class Refused(Exception):
    """Nexus was reached but answered with an error."""


def _mod(mod_id):
    """{name: the mod's own name or None, files: [its file records]}."""
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
    return {"name": (data.get("mod") or {}).get("name"), "files": data.get("modFiles") or []}


def lookup(file_name, mod=_mod):
    """The Nexus file whose download name is exactly file_name, with its mod's name, or None.

    Raises Offline when Nexus can't be reached, Refused when it answers with an error.
    """
    # the mod id is one of the name's all-digit parts; each is only a candidate until uri matches
    for mod_id in dict.fromkeys(re.findall(r"(?<=-)\d+(?=-)", file_name)):
        found = mod(mod_id)
        for f in found["files"]:
            if f["uri"] == file_name:
                return {"nexus_id": int(mod_id), "file_id": f["fileId"], "name": f["name"],
                        "mod_name": found["name"] or f["name"], "version": f["version"],
                        "category": f["category"]}
    return None
