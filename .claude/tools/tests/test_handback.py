"""The `.` hand-back: the last post from before the /clear, word for word, once."""
import os

from tests.harness import S, SID, check, line, run, tool_event, tool_line, write


def _earlier(tag, sid):
    """An earlier conversation whose last post is `Final post <tag>.`, then a session after it."""
    d = os.path.join(S.tmp, tag)
    write(os.path.join(d, "old_%s.jsonl" % tag), "\n".join([
        line("user", "do x"), line("assistant", "working on it"), tool_line(),
        line("assistant", "Final post %s.\nSecond line." % tag)]) + "\n")
    live = os.path.join(d, "live.jsonl")
    run("briefing.py", {"session_id": sid, "transcript_path": live}, env=S.env)
    return live


def _read_as(sid):
    event = dict(tool_event("Read", {"file_path": S.small}), session_id=sid)
    return run("pregate.py", event, env=S.env)


def _dot(sid, prompt="."):
    return run("turnstart.py", {"session_id": sid, "prompt": prompt}, env=S.env)


def first_dot():
    sid = SID + "-hb"
    live = _earlier("hb", sid)
    _, out, err = _dot(sid)
    check("`.` first hands back the last post, whole",
          "HAND-BACK" in out and "Final post hb.\nSecond line." in out, out + err)
    check("the hand-back skips text before the last tool call", "working on it" not in out, out)
    code, _, err = _read_as(sid)
    check("pregate refuses a tool during a hand-back", code == 2 and "hand-back" in err, err)
    write(live, line("user", ".") + "\n"
          + line("assistant", "Here is what we did: something else") + "\n")
    code, _, err = run("journal.py", {"session_id": sid, "transcript_path": live}, env=S.env)
    check("Stop never sends a wrong hand-back back", code == 0 and not err.strip(), err)
    code, _, _ = _read_as(sid)
    check("tools are free again once the hand-back is done", code == 0)


def not_a_handback():
    sid = SID + "-again"
    _earlier("hb", sid)
    _, out, _ = _dot(sid)
    check("a post is handed back only once",
          "already handed back once" in out and "Final post" not in out, out)
    sid = SID + "-later"
    _earlier("later", sid)
    _dot(sid, "hi")
    _, out, _ = _dot(sid)
    check("`.` on a later message is not a hand-back", out.strip() == "", out)
    sid = SID + "-notdot"
    _earlier("notdot", sid)
    _, out, _ = _dot(sid, "go on.")
    check("a first message that is not exactly `.` is not a hand-back", "HAND-BACK" not in out, out)
