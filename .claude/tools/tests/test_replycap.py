"""The reply cap, measured on the final post only: turnstart shows it, and the next turn's note."""
import os

from tests.harness import S, SID, check, line, run, tool_line, write


def _stop_with(prompt, *lines):
    tp = os.path.join(S.tmp, "cap", "t.jsonl")
    write(tp, "\n".join([line("user", prompt)] + list(lines)) + "\n")
    return run("journal.py", {"session_id": SID, "transcript_path": tp}, env=S.env)


def _start(prompt):
    return run("turnstart.py", {"session_id": SID, "prompt": prompt}, env=S.env)[1]


def main():
    out = _start("fix it")
    check("turnstart shows the plain cap", "REPLY CAP" in out and " 700 " in out, out)
    check("no task-list reminder without a Go", "TASK LIST" not in out, out)
    check("a Go turn gets the task-list reminder", "TASK LIST" in _start("Go: fix it"))
    out = _start("why does it fail?")
    check("a question asking why gets the bigger cap", "1800" in out, out)
    code, out, err = _stop_with("why does it fail?", line("assistant", "x" * 1900))
    check("Stop never sends an over-cap post back",
          code == 0 and not err.strip() and not out.strip(), out + err)
    out = _start("ok")
    check("the next turn starts with the overage", "LAST REPLY OVER CAP: 1900" in out, out)
    out = _start("ok")
    check("the overage is shown once", "LAST REPLY" not in out, out)
    _start("fix it")
    _stop_with("fix it", line("assistant", "x" * 900), tool_line({"command": "ls"}),
               line("assistant", "Done."))
    check("text before the last tool call is not counted", "LAST REPLY" not in _start("ok"))
    fenced = "Short.\n```\n" + "y" * 2000 + "\n```\n| a | " + "z" * 900 + " |"
    _stop_with("ok", line("assistant", fenced))
    check("fenced blocks and table rows are free", "LAST REPLY" not in _start("ok"))
    out = _start("long reply please: fix it")
    _stop_with("long reply please: fix it", line("assistant", "x" * 3000))
    check("'long reply' lifts the cap",
          "REPLY CAP" not in out and "LAST REPLY" not in _start("ok"), out)
