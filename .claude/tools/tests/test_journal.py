"""briefing.py, journal.py and prevconvo.py; no Stop hook can send a reply back."""
import json
import os
import re

from _common import ROOT, TOOLS
from tests.harness import S, SID, check, line, run, write


def main():
    old = os.path.join(S.tmp, "proj", "old.jsonl")
    live = os.path.join(S.tmp, "proj", "live.jsonl")
    write(old, line("user", "the earlier question") + "\n"
          + line("assistant", "the earlier answer") + "\n")
    start = {"session_id": SID, "transcript_path": live, "source": "startup"}
    code, out, _ = run("briefing.py", start, env=S.env)
    check("briefing prints the state",
          code == 0 and "PROJECT STATE" in out and "WE ARE ON" in out, out[-400:])
    write(live, line("user", "hello") + "\n" + line("assistant", "Result: done") + "\n")
    for _ in range(2):
        code, _, err = run("journal.py", {"session_id": SID, "transcript_path": live}, env=S.env)
    with open(os.path.join(S.tmp, "state", "journal.jsonl"), encoding="utf-8") as fh:
        rows = fh.read().splitlines()
    check("journal records the reply", code == 0 and "Result: done" in rows[-1], err)
    check("journal keeps one entry per turn", len(rows) == 1, "%d rows" % len(rows))
    code, out, _ = run("journal.py", env=S.env)
    check("journal renders", "TURN JOURNAL" in out, out)
    code, out, err = run("prevconvo.py", env=S.env)
    check("prevconvo prints the conversation before this one",
          "the earlier answer" in out and "Result: done" not in out, out + err)


def _source(script):
    with open(os.path.join(TOOLS, script), encoding="utf-8") as fh:
        return fh.read()


def stop_never_blocks():
    with open(os.path.join(ROOT, ".claude", "settings.json"), encoding="utf-8") as fh:
        groups = json.load(fh)["hooks"].get("Stop", [])
    scripts = [os.path.basename(h["command"].split("/")[-1].strip('"'))
               for g in groups for h in g["hooks"]]
    blocking = [s for s in scripts
                if re.search(r"exit\(2\)|\"decision\"|'decision'", _source(s))]
    check("no Stop hook can block or send a reply back", scripts and not blocking, blocking)
