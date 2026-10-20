"""noask.py: question popups and wrap-up questions are refused unless the message allows them."""
import os

from tests.harness import S, SID, check, run, tool_event, write

POPUP, WRAP = ("AskUserQuestion", {}), "mcp__ccd_turn__wrap_up"
CASES = (("Go", POPUP, False), ("Go", (WRAP, {"ask": "Commit?"}), False),
         ("Go", (WRAP, {"recap": "done"}), True), ("Go, Questions are allowed", POPUP, True))


def main():
    for prompt, (tool, inp), ok in CASES:
        run("turnstart.py", {"session_id": SID, "prompt": prompt}, env=S.env)
        code, _, err = run("noask.py", tool_event(tool, inp), env=S.env)
        check("noask: %r, %s, %s" % (prompt, tool, ok), code == (0 if ok else 2), err)
    write(os.path.join(S.tmp, "x"), "")
    broken = dict(S.env, STARTER_STATE=os.path.join(S.tmp, "x"))
    code, _, err = run("noask.py", tool_event(*POPUP), env=broken)
    check("noask fails closed when it breaks", code == 2 and "failed closed" in err, err)
