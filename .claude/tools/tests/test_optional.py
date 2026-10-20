"""The optional add-ons, run from where they ship."""
import os

from _common import TOOLS
from tests.harness import OPTIONAL, S, check, run


def main():
    env = dict(S.env, PYTHONPATH=TOOLS)
    cov = os.path.join(OPTIONAL, "coverage")
    run("coverage.py", args=["item", "--axes", "os=win,mac"], env=env, where=cov)
    run("coverage.py", args=["item", "--prove", "os=win", "--note", "seen"], env=env, where=cov)
    _, out, err = run("coverage.py", env=env, where=cov)
    check("coverage counts proven cases", "1 of 2" in out, out + err)
    night = os.path.join(OPTIONAL, "night-run")
    _, out, _ = run("nightlock.py", args=["take"], env=env, where=night)
    other = dict(env, CLAUDE_CODE_SESSION_ID="other")
    code, held, _ = run("nightlock.py", args=["take"], env=other, where=night)
    check("nightlock: taken, then held against another session",
          out.strip() == "TAKEN" and code == 1, out + held)
