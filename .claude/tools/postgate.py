"""PostToolUse hook: count a call's output, flag an empty search, record writes, push its traps.

Anything it says goes back to Claude on stderr with exit 2; the call itself has already run.
"""
import json
import os
import re
import sys

from _common import (SHELLS, WRITERS, budget, event, load, rel, save, save_turn, session_dir,
                     session_id, turn, utf8)

# tools whose result is one line to Claude, whatever they hand the harness
SILENT = WRITERS + ("TodoWrite",)
SKIP_KEYS = ("originalFile", "structuredPatch")
SEARCHY = re.compile(r"\b(grep|rg|findstr|select-string)\b", re.I)


def strings(x, out):
    if isinstance(x, str):
        out.append(x)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k not in SKIP_KEYS:
                strings(v, out)
    elif isinstance(x, list):
        for v in x:
            strings(v, out)
    return out


def seen_text(tool, resp):
    """The text this call put in front of Claude, which every later call carries again."""
    if tool in SILENT:
        return ""
    if tool == "Read" and isinstance(resp, dict) and isinstance(resp.get("file"), dict):
        return resp["file"].get("content") or ""
    return "\n".join(strings(resp, []))


def _grep_empty(resp):
    counts = [resp[k] for k in ("numFiles", "numLines", "numMatches") if k in resp]
    if counts:
        return all(c == 0 for c in counts)
    return not (resp.get("filenames") or resp.get("content"))


def _shell_empty(resp):
    out = resp.get("stdout") if isinstance(resp, dict) else str(resp or "")
    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    return all(ln == "0" or ln.endswith(":0") for ln in lines)


def empty_search(tool, inp, resp):
    if tool == "Grep" and isinstance(resp, dict):
        return _grep_empty(resp)
    if tool in SHELLS and SEARCHY.search(inp.get("command") or ""):
        return _shell_empty(resp)
    return False


def pushes(inp, sid):
    """The traps whose names this call mentions, each pushed once per session."""
    import rules
    text = json.dumps(inp, ensure_ascii=False).replace("\\\\", "/")
    mark = os.path.join(session_dir(sid), "pushed.json")
    done = set(load(mark, []))
    out = []
    for r in rules.for_text(text):
        if r["title"] not in done:
            done.add(r["title"])
            out.append(rules.fmt(r))
    if out:
        save(mark, sorted(done))
    return out


def main():
    utf8()
    ev = event()
    sid = session_id(ev)
    tool, inp, resp = ev.get("tool_name") or "", ev.get("tool_input") or {}, ev.get("tool_response")
    t = turn(sid)
    t["calls"] = t.get("calls", 0) + 1
    before = t.get("chars", 0)
    t["chars"] = before + len(seen_text(tool, resp))
    if tool in WRITERS:
        p = inp.get("file_path") or inp.get("notebook_path")
        if p and rel(p) not in t.setdefault("wrote", []):
            t["wrote"].append(rel(p))
    save_turn(t, sid)

    said = []
    cap = budget(t)
    if cap and before < cap <= t["chars"]:
        said.append("BUDGET: this turn has now taken in %d characters of tool output (budget %d). "
                    "Further reads will be refused -- finish with what you have."
                    % (t["chars"], cap))
    if empty_search(tool, inp, resp):
        said.append("EMPTY SEARCH: absence from a search is not evidence of absence. Before saying "
                    "something does not exist, check the spelling, the path, the case "
                    "and other names "
                    "it may go by -- or say plainly that it is unverified.")
    said += pushes(inp, sid)
    if said:
        sys.stderr.write("\n\n".join(said) + "\n")
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as broke:
        sys.stderr.write("postgate.py failed: %s: %s\n" % (type(broke).__name__, broke))
