"""on.py, doccheck.py and rules.py, and the pre-commit tie between the tools and HANDOFF."""
import json
import os

from tests.harness import S, check, run, snippet, write

TWIN_NAMES = "## G\\n\\n- **one**\\n  names: `a`\\n\\n- **two**\\n  names: `a`\\n"
STAGED = ((["CLAUDE.md"], False), ([".claude/tools/plan.py", "docs/HANDOFF.md"], True),
          (["README.md", "docs/WHY.md"], True), ([".githooks/pre-commit"], False))


def main():
    run("on.py", args=["the selftest"], env=S.env)
    _, out, _ = run("on.py", env=S.env)
    check("on.py moves and reads the WE ARE ON line", out.strip() == "the selftest", out)
    code, out, _ = run("doccheck.py", env=S.env)
    check("doccheck passes the moved handoff", code == 0, out)
    said = snippet(S.env, "import rules; print(len(rules.check('%s')))" % TWIN_NAMES)
    check("rules.check catches a name two rules share", said == "1", said)
    code, out, _ = run("doccheck.py", env=S.live_env)
    check("the live docs pass doccheck", code == 0, out)
    write(os.path.join(S.tmp, "cap.json"), json.dumps({"claude_md_cap_chars": 100}))
    capped = dict(S.live_env, STARTER_CONFIG=os.path.join(S.tmp, "cap.json"))
    code, out, _ = run("doccheck.py", env=capped)
    check("doccheck refuses a CLAUDE.md over its cap", code == 1 and "CLAUDE.md is" in out, out)


def precommit():
    for staged, ok in STAGED:
        code = "import doccheck; print(len(doccheck.handoff_staged(%r)))" % staged
        said = snippet(S.live_env, code)
        verb = "accepts" if ok else "refuses"
        check("pre-commit %s %s" % (verb, staged), said == ("0" if ok else "1"), said)
