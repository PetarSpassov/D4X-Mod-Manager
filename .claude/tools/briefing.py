"""SessionStart hook: print where the project is, so a fresh session opens oriented, not hunting.

It never fails a session: anything it cannot find, it says so and moves on.
"""
import glob
import os
import re
import subprocess

from _common import (ROOT, STATE, TOOLS, event, now, path, read_text, rel, save, session_dir,
                     session_id, utf8)

PENDING = os.path.join(STATE, "pending_check.md")


def record_start(ev, sid):
    """Write down which transcripts exist NOW: every one of them is an earlier conversation, so
    `prevconvo.py` never has to guess which file is the live one."""
    tp = ev.get("transcript_path") or ""
    d = os.path.dirname(tp)
    me = os.path.basename(tp)
    roster = sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, "*.jsonl"))
                    if os.path.basename(p) != me) if d else None
    save(os.path.join(session_dir(sid), "start.json"),
         {"at": now(), "source": ev.get("source") or "unknown", "transcript_dir": d,
          "transcript": me, "roster": roster})


def git_hooks():
    """Point git at the repository's own hooks, so the pre-commit check runs on every clone."""
    if not (os.path.isdir(os.path.join(ROOT, ".git"))
            and os.path.isdir(os.path.join(ROOT, ".githooks"))):
        return
    got = subprocess.run(["git", "config", "core.hooksPath"], cwd=ROOT, capture_output=True,
                         text=True)
    if got.stdout.strip() != ".githooks":
        subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=ROOT,
                       capture_output=True)


def state_section(h):
    m = re.search(r"(?ms)^## State[^\n]*\n(.*?)(?=^## |\Z)", h)
    return m.group(1).strip() if m else ""


def say(fn, *args):
    try:
        fn(*args)
    except Exception as broke:
        print("(%s skipped: %s)" % (fn.__name__, broke))


def project_state():
    h = read_text(path("handoff"))
    if not h:
        print("%s could not be read. Orient from CLAUDE.md and ask the user."
              % rel(path("handoff")))
    else:
        print(state_section(h) or "No `## State` section in %s." % rel(path("handoff")))
        say(on_age)


def on_age():
    """How many commits ago the WE ARE ON line last moved, so a stale one shows on every start."""
    def git(*args):
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True, text=True,
                              stdin=subprocess.DEVNULL).stdout.strip()
    moved = git("log", "-1", "--format=%h", "-G", "WE ARE ON", "--", rel(path("handoff")))
    if moved:
        n = int(git("rev-list", "--count", moved + "..HEAD") or 0)
        print("\nWE ARE ON last moved %d commit(s) ago (%s)%s" % (
            n, moved, ": check it is still true" if n >= 3 else "."))


def owed_check():
    if os.path.exists(PENDING):
        print("\n*** A CHECK IS OWED FROM THE PREVIOUS SESSION -- RUN IT FIRST, then delete %s ***"
              % rel(PENDING))
        print(read_text(PENDING).rstrip())


def doc_health():
    import doccheck
    import rules
    n = len(rules.parse())
    if n:
        print("\n%d traps in %s. Never read it whole: the hooks push the ones a call touches, and "
              "`python .claude/tools/rules.py <thing>` fetches one." % (n, rel(path("gotchas"))))
    bad = doccheck.problems()
    if bad:
        print("DOCS: %d problem(s) -- `python .claude/tools/doccheck.py` lists them." % len(bad))


def coverage():
    if os.path.isfile(os.path.join(TOOLS, "coverage.py")):
        import coverage as cov
        lines = cov.summary()
        if lines:
            print("\nCOVERAGE -- what is PROVEN, not what feels finished:")
            print("\n".join(lines))


def main():
    utf8()
    ev = event()
    sid = session_id(ev)
    say(record_start, ev, sid)
    say(git_hooks)
    print("=== PROJECT STATE (printed by .claude/tools/briefing.py, not by the assistant) ===")
    say(project_state)
    say(owed_check)
    say(doc_health)
    say(coverage)
    print("\nPICKING UP:")
    print("* Do not open by asking what to do: WE ARE ON and the journal below say where "
          "we are. Ask only")
    print("  if they conflict -- and say how.")
    print("* The previous conversation is one command: `python .claude/tools/prevconvo.py`. "
          "Run it the")
    print("  moment the user refers to anything said before a /clear.")
    print("* A reported test result updates the docs before the reply: `/result`.")
    print("=== END PROJECT STATE ===")
    try:
        import journal
        block = journal.render()
        if block:
            print("\n" + block)
    except Exception:
        pass  # the briefing still prints without the journal


if __name__ == "__main__":
    try:
        main()
    except Exception as broke:
        print("(briefing failed: %s)" % broke)
