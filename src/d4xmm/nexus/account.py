"""What the player's personal API key allows: whose account it is, and Premium's direct downloads.

The v1 REST API, the one that takes a key; Nexus hands out download links only to Premium.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from d4xmm.nexus import files

API = "https://api.nexusmods.com/v1"
GAME = "dunespicewars"
# the page's heading has no anchor; a text fragment scrolls to it in Chrome, Edge and Firefox
KEY_PAGE = "https://www.nexusmods.com/settings/api-keys#:~:text=Personal%20API%20Key"
CHUNK = 1 << 20
DOWNLOAD_TIMEOUT = 60  # per read, not for the whole file


class InvalidKey(Exception):
    """Nexus doesn't accept the key: mistyped, or deleted or regenerated on the account page."""


class NotPremium(Exception):
    """The account is not Premium, so Nexus gives it no download links."""


def _get(path, key):
    headers = {"apikey": key, "User-Agent": "D4XModManager", "Accept": "application/json"}
    req = urllib.request.Request(API + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=files.TIMEOUT) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:  # an HTTPError is a URLError, so it is caught first
        if e.code == 401:
            raise InvalidKey(str(e)) from e
        if e.code == 403:
            raise NotPremium(str(e)) from e
        raise files.Refused(str(e)) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise files.Offline(str(e)) from e


def check(key):
    """{name, premium} of the key's account. Raises InvalidKey, files.Offline or files.Refused."""
    found = _get("/users/validate.json", key)
    return {"name": found.get("name"), "premium": bool(found.get("is_premium"))}


def download_url(key, mod_id, file_id, grant=None):
    """Where the file downloads from: the first of the servers Nexus lists. grant: the key and
    expires of a website "Mod Manager Download" link, which lets a free account download."""
    path = "/games/%s/mods/%d/files/%d/download_link.json" % (GAME, mod_id, file_id)
    if grant:
        path += "?" + urllib.parse.urlencode({"key": grant["key"], "expires": grant["expires"]})
    links = _get(path, key)
    if not links:
        raise files.Refused("Nexus gave no download address")
    return links[0]["URI"]


def fetch(url, dest):
    """Save url at dest, written as dest.part and renamed once whole, so no half file is seen."""
    part = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "D4XModManager"})
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as r, open(part, "wb") as f:
            while chunk := r.read(CHUNK):
                f.write(chunk)
    except (urllib.error.URLError, TimeoutError) as e:
        if os.path.exists(part):
            os.remove(part)  # our own half-written file, never the player's
        raise files.Offline(str(e)) from e
    os.replace(part, dest)
