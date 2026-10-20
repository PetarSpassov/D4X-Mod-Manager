"""The night lock: one unattended run at a time, and a line per run.

    nightlock.py take | release | clear | (nothing: who holds it). HELD on take: end the run
"""
import os
import sys
import time

from _common import STATE, load, now, save, session_id, utf8

LOCK = os.path.join(STATE, "night.lock.json")
RUNS = os.path.join(STATE, "night_runs.txt")
# a run that a usage limit cuts off never releases, so the lock goes stale by itself;
# the holder takes it again before each long step, which only moves the time
STALE_AFTER = 60 * 60


def log(line):
    os.makedirs(STATE, exist_ok=True)
    with open(RUNS, "a", encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (now(), line))


def _take(me, held):
    if held and held.get("by") != me and time.time() - held.get("at", 0) < STALE_AFTER:
        print("HELD by %s since %s -- end this run now." % (held["by"], held.get("since")))
        return 1
    word = "REFRESHED" if held.get("by") == me else ("STALE" if held else "TAKEN")
    save(LOCK, {"by": me, "at": time.time(),
                "since": held.get("since") if word == "REFRESHED" else now()})
    if word != "REFRESHED":
        log("%s by %s" % (word, me))
    print(word)
    return 0


def _status(held):
    print("held by %s since %s" % (held["by"], held.get("since")) if held else "free")
    try:
        print("".join(open(RUNS, encoding="utf-8").readlines()[-10:]).rstrip())
    except OSError:
        pass  # no runs file yet


def main(argv):
    utf8()
    me = session_id()[:36]
    held = load(LOCK)
    act = argv[0] if argv else ""
    if act == "take":
        return _take(me, held)
    if act in ("release", "clear"):
        if os.path.exists(LOCK) and (act == "clear" or held.get("by") == me):
            os.remove(LOCK)
            log("%s by %s" % (act.upper(), me))
        print("free")
    else:
        _status(held)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
