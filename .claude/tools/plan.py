"""The turn's plan: declared before its first write, then compared with what the turn does.
A change turn needs a message starting with "Go"; an answer turn cannot become one.
Reading is never gated, nor files outside the project. Usage: .claude/README.md.
"""
import fnmatch
import os
import re
import sys

from _common import SHELLS, WRITERS, load, rel, save, session_dir, turn, utf8

USAGE = ('python .claude/tools/plan.py "<what this turn does>" --touch <files> '
         '--leave "<what it leaves alone>"'
         ' -- or, if this turn only answers: '
         'python .claude/tools/plan.py --answer "<what it answers>"')
ANSWER_LOCKED = ("this turn was declared an answer turn, so it writes nothing. "
                 "Finish the answer and name "
                 "the change as the next step; a message starting with \"Go\" opens a change turn.")


NO_GO = ("the user's message does not start with \"Go\", so this is an answer turn. "
         "Propose the change "
         "and stop; a message starting with \"Go\" opens the change turn.")


def go(prompt):
    """True when the message's first word is `go`, in any case, with or without punctuation."""
    return bool(re.match(r"\s*go\b", (prompt or "").lower()))


def _file():
    return os.path.join(session_dir(), "plan.json")


def current():
    """This turn's plan, or {}: a plan expires with the turn that declared it."""
    p = load(_file())
    return p if p.get("turn") and p.get("turn") == turn().get("id") else {}


def _gated(tool, inp):
    """The project file this call writes, or "" when the gate does not apply to it."""
    if tool in SHELLS and "plan.py" in (inp.get("command") or ""):
        return ""
    if tool not in WRITERS:
        return ""
    f = rel(inp.get("file_path") or inp.get("notebook_path") or "")
    return "" if f.startswith("../") or os.path.isabs(f) else f


def refusal(tool, inp):
    f = _gated(tool, inp)
    if not f:
        return ""
    p = current()
    if not p:
        return "no plan for this turn, and it is about to write. First: " + USAGE
    if p.get("answer"):
        return ANSWER_LOCKED
    if any(f == t or fnmatch.fnmatch(f, t) for t in p.get("touch") or []):
        return ""
    return ("`%s` is outside this turn's plan (%s). If it is needed: python .claude/tools/plan.py "
            "--widen %s \"<why>\" -- and say so in the reply."
            % (f, ", ".join(p.get("touch") or []), f))


def _show(p):
    if p.get("answer"):
        print("ANSWER: %s" % p["doing"])
    elif not p:
        print("No plan for this turn.")
    else:
        print("DOING : %s\nTOUCH : %s\nLEAVES: %s\nWIDENED: %s" % (
            p.get("doing", "-"), ", ".join(p.get("touch") or []) or "-", p.get("leave", "-"),
            "; ".join(p.get("widened") or []) or "-"))
    return 0


def _answer(p, argv):
    if p:
        print("Refused: this turn already declared a change plan.")
        return 1
    if len(argv) < 2:
        print(USAGE)
        return 1
    save(_file(), {"turn": turn().get("id"), "answer": True, "doing": " ".join(argv[1:])})
    print("Answer turn recorded: no writes this turn.")
    return 0


def _widen(p, argv):
    if not p or len(argv) < 3:
        print("Widen needs a plan for this turn, a file and a reason.")
        return 1
    p["touch"].append(rel(argv[1]))
    p.setdefault("widened", []).append("%s: %s" % (rel(argv[1]), " ".join(argv[2:])))
    save(_file(), p)
    print("Widened to %s." % rel(argv[1]))
    return 0


def _parse(argv):
    """The words saying what the turn does, the files after --touch, the words after --leave."""
    doing, touch, leave, key = [], [], [], None
    for a in argv:
        if a in ("--touch", "--leave"):
            key = a
        elif key == "--touch":
            touch.append(rel(a))
        elif key == "--leave":
            leave.append(a)
        else:
            doing.append(a)
    return doing, touch, leave


def main(argv):
    utf8()
    p = current()
    if not argv or argv[0] == "--show":
        return _show(p)
    if p.get("answer"):
        print("Refused: " + ANSWER_LOCKED)
        return 1
    if argv[0] == "--answer":
        return _answer(p, argv)
    if argv[0] == "--widen":
        return _widen(p, argv)
    return _change(argv)


def _change(argv):
    doing, touch, leave = _parse(argv)
    if not doing or not touch:
        print(USAGE)
        return 1
    if not go(turn().get("prompt")):
        print("Refused: " + NO_GO)
        return 1
    save(_file(), {"turn": turn().get("id"), "doing": " ".join(doing), "touch": touch,
                   "leave": " ".join(leave) or "unsaid"})
    print("Plan recorded. Touching: %s" % ", ".join(touch))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
