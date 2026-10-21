"""Every Dune: Spice Wars mod on Nexus, most downloaded first, through the keyless API."""
from d4xmm.nexus import bbcode, files

PAGE = 50
QUERY = ("query($game: String!, $count: Int, $offset: Int) { mods(filter: {gameId: "
         "[{value: $game, op: EQUALS}]}, sort: [{downloads: {direction: DESC}}], count: $count, "
         "offset: $offset) { totalCount nodes { modId name summary description pictureUrl "
         "thumbnailUrl downloads endorsements createdAt updatedAt version tags { name } "
         "uploader { name } } } }")


def _entry(node):
    """One mod in the names the window already uses for a library mod, plus Browse's own."""
    return {"nexus_id": node["modId"], "name": node["name"], "version": node.get("version"),
            "creator": (node.get("uploader") or {}).get("name"), "summary": node.get("summary"),
            "description": bbcode.to_html(node.get("description")),
            "picture": node.get("pictureUrl"),
            "thumbnail": node.get("thumbnailUrl"), "downloads": node.get("downloads"),
            "endorsements": node.get("endorsements"), "created": node.get("createdAt"),
            "updated": node.get("updatedAt"), "tags": [t["name"] for t in node.get("tags") or []]}


def browse(post=files.post):
    """[every mod's entry], fetched PAGE at a time. Raises files.Offline or files.Refused."""
    out = []
    while True:
        found = post(QUERY, {"game": str(files.GAME_ID), "count": PAGE,
                             "offset": len(out)}).get("mods") or {}
        nodes = found.get("nodes") or []
        out += [_entry(n) for n in nodes]
        if not nodes or len(out) >= found.get("totalCount", 0):
            return out
