"""plan.py and its gate in pregate: a change turn needs a Go, an answer turn writes nothing."""
import os
import subprocess
import sys

from _common import ROOT, TOOLS
from tests.harness import S, SID, check, run, tool_event

SRC_A, SRC_B = os.path.join(ROOT, "src", "a.py"), os.path.join(ROOT, "src", "b.py")
PROMPTS = (("This hook needs to go", False), ("Commit and push", False), ("Please link it", False),
           ("Gone wrong. Fix it", False), ("Go", True), ("Go: do that.", True),
           ("  go ahead, write it", True), ("GO!", True))


def _say(prompt):
    run("turnstart.py", {"session_id": SID, "prompt": prompt}, env=S.env)


def _gate(tool, path):
    return run("pregate.py", tool_event(tool, {"file_path": path}), env=S.env)


def go_word():
    for prompt, ok in PROMPTS:
        _say(prompt)
        code, out, _ = run("plan.py", args=["edit a", "--touch", "src/a.py"], env=S.env)
        check("plan: %r %s a change turn" % (prompt, "opens" if ok else "does not open"),
              (code == 0) == ok and (ok or "\"Go\"" in out), out)
    p = subprocess.Popen([sys.executable, os.path.join(TOOLS, "plan.py"), "--show"],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         env=S.env, cwd=ROOT)
    try:
        p.wait(timeout=10)
        hung = False
    except subprocess.TimeoutExpired:
        p.kill()
        hung = True
    p.stdin.close()
    check("a tool run with stdin left open does not hang", not hung)


def gate():
    _say("go: edit a")
    code, _, err = _gate("Edit", SRC_A)
    check("plan: a write with no plan is refused", code == 2 and "no plan" in err, err)
    code, out, err = run("plan.py", args=["edit a", "--touch", "src/a.py"], env=S.env)
    check("plan: a change turn is recorded", code == 0 and "Plan recorded" in out, out + err)
    code, _, err = _gate("Edit", SRC_A)
    check("plan: a declared file may be written", code == 0, err)
    code, _, err = _gate("Edit", SRC_B)
    check("plan: an undeclared file is refused", code == 2 and "outside" in err, err)


def answer_turn():
    _say("is there a guard for this?")
    code, out, err = run("plan.py", args=["--answer", "whether the guard exists"], env=S.env)
    check("plan: an answer turn is recorded", code == 0 and "Answer turn" in out, out + err)
    code, _, err = _gate("Edit", SRC_A)
    check("plan: an answer turn refuses a project write", code == 2 and "answer turn" in err, err)
    code, out, _ = run("plan.py", args=["edit a", "--touch", "src/a.py"], env=S.env)
    check("plan: an answer turn cannot become a change turn", code == 1 and "Refused" in out, out)
    code, _, err = _gate("Read", S.small)
    check("plan: an answer turn still reads", code == 0, err)
    code, _, err = _gate("Write", S.small)
    check("plan: a file outside the project (memory) is never gated", code == 0, err)
    _say("now edit a")
    code, _, err = _gate("Edit", SRC_A)
    check("plan: a plan expires with its turn", code == 2 and "no plan" in err, err)
