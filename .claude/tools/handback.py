"""The `.` hand-back: a first message of exactly `.` gets the last post from before the /clear.
It keys on what the user typed, never SessionStart's `source`; each post goes back once.
turnstart.py pushes it, pregate.py refuses every tool while it is due, journal.py closes it.
"""
import os

from _common import (STATE, assistant_text, load, save, session_dir, transcript, user_text,
                     uses_a_tool)

SPENT = os.path.join(STATE, "handback_spent.json")


def asked(prompt, first):
    return first and (prompt or "").strip() == "."


def last_post(p, tail_bytes=0):
    """The text the user saw last: the assistant's words after its last tool call in the final turn,
    or the words before that call when the turn ended on a tool (a wrap-up, say)."""
    post, before = [], []
    for o in transcript(p, tail_bytes=tail_bytes):
        if user_text(o):
            post, before = [], []
        elif uses_a_tool(o):
            if post:
                before = post
            post = []
        else:
            said = assistant_text(o)
            if said:
                post.append(said)
    return "\n\n".join(post or before).strip()


def _file(sid=None):
    return os.path.join(session_dir(sid), "handback.json")


def due(sid=None):
    h = load(_file(sid))
    return h if h.get("status") == "due" else {}


def push(sid):
    """What the user's `.` puts in front of Claude: the post to give back, or why there is none."""
    import prevconvo
    p, _ = prevconvo.previous()
    if not p:
        return ("THE `.` HAND-BACK: there is nothing to hand back, because no earlier "
                "conversation is "
                "recorded for this project. Say so in one line, then pick up from the briefing.")
    name = os.path.basename(p)
    spent = load(SPENT, {}).get("spent", [])
    if name in spent:
        return ("THE `.` HAND-BACK: the last post of the previous conversation was already "
                "handed back "
                "once. Do not post it again. Say so in one line, then pick up from the briefing.")
    text = last_post(p)
    if not text:
        return ("THE `.` HAND-BACK: the previous conversation ended without a post. "
                "Say so in one line, "
                "then pick up from the briefing.")
    save(SPENT, {"spent": (spent + [name])[-200:]})
    save(_file(sid), {"status": "due", "source": name, "text": text})
    return ("=== THE `.` HAND-BACK -- their message is `.`: your WHOLE reply is the text below, "
            "word for word. No tool call, nothing added before or after. ===\n%s\n"
            "=== END OF THE HAND-BACK ===" % text)


def finish(sid):
    """Stop: close a due hand-back so tools are free again. It never judges the reply."""
    h = due(sid)
    if h:
        h["status"] = "done"
        save(_file(sid), h)
