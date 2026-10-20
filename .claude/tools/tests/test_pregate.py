"""pregate.py: the read cap, the size limit and the turn's declaration line."""
import json
import os
import subprocess
import sys
import time

from _common import ROOT, TOOLS
from tests.harness import S, SID, check, line, run, tool_event, tool_line, write


def _gate(tool, inp):
    return run("pregate.py", tool_event(tool, inp), env=S.env)


def reads():
    code, _, _ = _gate("Read", {"file_path": S.small})
    check("pregate lets a small read through", code == 0)
    code, _, err = _gate("Read", {"file_path": S.big})
    check("pregate refuses a whole read over the cap", code == 2 and "read cap" in err, err)
    code, _, _ = _gate("Read", {"file_path": S.big, "limit": 50})
    check("pregate allows a ranged read of a big file", code == 0)
    code, _, err = _gate("Read", {"file_path": S.secret})
    check("pregate refuses a never-read file", code == 2 and "never-read" in err, err)
    code, _, err = _gate("Bash", {"command": "cat big.txt"})
    check("pregate refuses `cat` of a big file", code == 2, err)
    code, _, _ = _gate("Bash", {"command": "cat > big.txt <<EOF\nhi\nEOF"})
    check("pregate treats `cat >` as a write", code == 0)
    code, _, _ = _gate("Bash", {"command": "grep -n x big.txt"})
    check("pregate allows a search of a big file", code == 0)


def size():
    """Past 800 lines a code file may only shrink."""
    run("turnstart.py", {"session_id": SID, "prompt": "go: grow it"}, env=S.env)
    run("plan.py", args=["grow", "--touch", "*"], env=S.env)
    code_f, doc_f = os.path.join(S.tmp, "big.py"), os.path.join(S.tmp, "big.md")
    code, _, err = _gate("Write", {"file_path": code_f, "content": "x\n" * 801})
    check("size: a new code file over 800 lines is refused", code == 2 and "801 lines" in err, err)
    code, _, err = _gate("Write", {"file_path": code_f, "content": "x\n" * 800})
    check("size: 800 lines is allowed", code == 0, err)
    write(code_f, "x\n" * 900)
    code, _, err = _gate("Edit", {"file_path": code_f, "old_string": "x\n", "new_string": "x\ny\n"})
    check("size: a file over the limit may not grow", code == 2 and "901 lines" in err, err)
    code, _, err = _gate("Edit", {"file_path": code_f, "old_string": "x\nx\n", "new_string": "x\n"})
    check("size: a file over the limit may shrink", code == 0, err)
    every_x = [{"old_string": "x\n", "new_string": "", "replace_all": True}]
    code, _, err = _gate("MultiEdit", {"file_path": code_f, "edits": every_x})
    check("size: MultiEdit is measured too", code == 0, err)
    code, _, err = _gate("Write", {"file_path": doc_f, "content": "x\n" * 2000})
    check("size: a non-code file is not limited", code == 0, err)


def _declared(tp, *lines):
    write(tp, "\n".join([line("user", "earlier"), line("assistant", "Answer turn. Old."),
                         line("user", "what is x?")] + list(lines)) + "\n")
    event = dict(tool_event("Read", {"file_path": S.small}), transcript_path=tp)
    return run("pregate.py", event, env=S.env)


def declare():
    """Rule 3.0: no tool call before the turn's declaration line."""
    run("turnstart.py", {"session_id": SID, "prompt": "what is x?"}, env=S.env)
    tp = os.path.join(S.tmp, "declare", "t.jsonl")
    code, _, err = _declared(tp)
    check("declare: a tool call before any text is refused",
          code == 2 and "Answer turn." in err, err)
    code, _, err = _declared(tp, line("assistant", "Let me look."))
    check("declare: text without the declaration is refused", code == 2, err)
    code, _, err = _declared(tp, line("assistant", "Answer turn. Reading x."))
    check("declare: a declared turn may call tools", code == 0, err)
    code, _, err = _declared(tp, line("assistant", "Change turn. Edit x."),
                             tool_line({"command": "ls"}), line("user", "Tool loaded."))
    check("declare: a line the harness injects does not restart the turn", code == 0, err)
    _declared(tp)
    _late_text(tp)


def _late_text(tp):
    late = subprocess.Popen([sys.executable, os.path.join(TOOLS, "pregate.py")],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=S.env, cwd=ROOT)
    event = dict(tool_event("Read", {"file_path": S.small}), transcript_path=tp)
    late.stdin.write(json.dumps(event).encode())
    late.stdin.close()
    time.sleep(0.6)
    with open(tp, "a", encoding="utf-8") as fh:
        fh.write(line("assistant", "Answer turn. Late.") + "\n")
    check("declare: text that reaches the transcript late still counts",
          late.wait(timeout=20) == 0, late.stderr.read().decode("utf-8", "replace"))
