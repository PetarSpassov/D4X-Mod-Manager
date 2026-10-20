"""newproject.bat given a folder: copies the template, skips .git and state, keeps what's there."""
import os
import subprocess

from _common import TOOLS
from tests.harness import S, check, write


def main():
    if os.name != "nt":
        return
    dest = os.path.join(S.tmp, "newproject")
    write(os.path.join(dest, "README.md"), "theirs")
    p = subprocess.run(["cmd", "/c", os.path.join(TOOLS, "newproject.bat"), dest],
                       capture_output=True, text=True, errors="replace", timeout=120)
    check("newproject.bat copies the template", p.returncode == 0
          and os.path.isfile(os.path.join(dest, "CLAUDE.md")), p.stdout[-300:])
    check("newproject.bat leaves out .git and .claude/state",
          not os.path.exists(os.path.join(dest, ".git"))
          and not os.path.exists(os.path.join(dest, ".claude", "state")), p.stdout[-300:])
    with open(os.path.join(dest, "README.md"), encoding="utf-8") as fh:
        check("newproject.bat never overwrites a file already there", fh.read() == "theirs")
