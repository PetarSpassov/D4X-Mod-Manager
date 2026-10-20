"""The reply cap in prose characters; fenced blocks and table rows are free. The Stop hook
only notes an over-cap post for the next turn: the user has read it, so a copy only doubles it.
"""
import os
import re

from _common import config, load, save, session_dir

ASKED = ("explain", "why", "walk me through", "tell me", "how does", "how do", "elaborate")
FENCE = re.compile(r"(?ms)^\s*```.*?^\s*```[^\n]*$")


def cap(prompt):
    """This turn's cap, or 0 when there is none: a `.` hand-back, or the long-reply phrase."""
    c = config()
    said = (prompt or "").strip().lower()
    phrase = (c.get("long_reply_phrase") or "").lower()
    if said == "." or (phrase and phrase in said):
        return 0
    if any(w in said for w in ASKED):
        return c.get("reply_cap_asked_chars") or 0
    return c.get("reply_cap_chars") or 0


def prose(text):
    """The post minus fenced blocks and table rows, whitespace collapsed."""
    kept = [l for l in FENCE.sub("", text or "").split("\n") if not l.strip().startswith("|")]
    return " ".join(" ".join(kept).split())


def _file(sid):
    return os.path.join(session_dir(sid), "overage.json")


def note(sid, prompt, post):
    """Stop: remember an over-cap post for the next turn. Never refuses."""
    n, c = len(prose(post)), cap(prompt)
    if c and n > c:
        save(_file(sid), {"n": n, "cap": c})


def reminder(sid, prompt):
    """Turn start: this turn's cap, and last turn's overage once."""
    out = []
    over = load(_file(sid))
    if over:
        os.remove(_file(sid))
        out.append("LAST REPLY OVER CAP: %d prose characters, the cap was %d. Cut this one."
                   % (over["n"], over["cap"]))
    c = cap(prompt)
    if c:
        out.append("REPLY CAP: this turn's final post is at most %d prose characters." % c)
    return "\n".join(out)
