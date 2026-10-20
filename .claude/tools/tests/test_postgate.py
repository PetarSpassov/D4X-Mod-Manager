"""postgate.py: empty searches, the trap push, recorded writes and the turn's budget."""
import os

from _common import ROOT
from tests.harness import S, SID, check, line, run, tool_event, tool_line, write


def _post(tool, inp, resp):
    return run("postgate.py", tool_event(tool, inp, resp), env=S.env)


def main():
    code, _, err = _post("Grep", {"pattern": "zz"}, {"filenames": [], "numFiles": 0})
    check("postgate flags an empty Grep", code == 2 and "EMPTY SEARCH" in err, err)
    code, _, _ = _post("Grep", {"pattern": "x"}, {"filenames": ["a"], "numFiles": 1})
    check("postgate is quiet on a Grep that found something", code == 0)
    code, _, err = _post("Bash", {"command": "grep -c foo *.py"}, {"stdout": "a.py:0\nb.py:0"})
    check("postgate flags a grep -c of all zeros", code == 2 and "EMPTY SEARCH" in err, err)
    code, _, _ = _post("Bash", {"command": "ls"}, {"stdout": ""})
    check("postgate ignores empty output that is not a search", code == 0)
    touch = {"command": "python run.py selftest_subject"}
    first, second = _post("Bash", touch, {"stdout": "ok"}), _post("Bash", touch, {"stdout": "ok"})
    check("postgate pushes a trap when its name is touched",
          first[0] == 2 and "A test rule" in first[2], first[2])
    check("postgate pushes it only once a session", second[0] == 0, second[2])
    code, _, _ = _post("Write", {"file_path": os.path.join(ROOT, "src", "a.py")}, {})
    with open(S.turn_file, encoding="utf-8") as fh:
        check("postgate records a write", code == 0 and "src/a.py" in fh.read())
    mid_turn()


def mid_turn():
    """Text past the turn's opening line is flagged, each piece once."""
    run("turnstart.py", {"session_id": SID, "prompt": "Go: fix it"}, env=S.env)
    tp = os.path.join(S.tmp, "mid", "t.jsonl")
    opening = [line("user", "Go: fix it"), line("assistant", "Change turn. Plan: x"), tool_line()]
    ev = dict(tool_event("Bash", {"command": "ls"}, {"stdout": "ok"}), transcript_path=tp)
    write(tp, "\n".join(opening) + "\n")
    code, _, err = run("postgate.py", ev, env=S.env)
    check("postgate allows the opening line", "MID-TURN" not in err, err)
    write(tp, "\n".join(opening + [line("assistant", "Now reading y."), tool_line()]) + "\n")
    code, _, err = run("postgate.py", ev, env=S.env)
    check("postgate flags mid-turn text", code == 2 and "Now reading y." in err, err)
    code, _, err = run("postgate.py", ev, env=S.env)
    check("postgate flags the same text only once", "MID-TURN" not in err, err)


def budget():
    """The turn's budget, and the user's phrase that widens it."""
    big_read = {"file": {"content": "y" * 2500}}
    code, _, err = _post("Read", {"file_path": S.small}, big_read)
    check("postgate warns when the turn crosses its budget", code == 2 and "BUDGET" in err, err)
    code, _, err = run("pregate.py", tool_event("Read", {"file_path": S.small}), env=S.env)
    check("pregate refuses a read over budget", code == 2 and "budget" in err, err)
    code, _, _ = run("pregate.py", tool_event("Edit", {"file_path": S.small}), env=S.env)
    check("pregate never refuses a write for budget", code == 0)
    run("turnstart.py", {"session_id": SID, "prompt": "a long turn please"}, env=S.env)
    code, _, err = _post("Read", {"file_path": S.small}, big_read)
    check("'long turn' widens the budget", code == 0, err)
