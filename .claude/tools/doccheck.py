"""Are the docs consistent? Run after a doc change, and by pre-commit. Exit 1 lists the problems."""
import os
import re
import subprocess
import sys

from _common import ROOT, config, matches_any, path, read_text, rel, utf8


def problems():
    out = []
    import on
    import rules
    h = read_text(path("handoff"))
    if not h:
        out.append("%s is missing" % rel(path("handoff")))
    else:
        n = len(on.LINE.findall(h))
        if n != 1:
            out.append("HANDOFF.md holds %d `**► WE ARE ON:**` lines; it must hold exactly one" % n)
        m = re.search(r"(?ms)^## State[^\n]*\n(.*?)(?=^## |\Z)", h)
        if not m:
            out.append("HANDOFF.md has no `## State` section")
        else:
            lines = [ln for ln in m.group(1).splitlines() if ln.strip()]
            cap = int(config().get("handoff_state_cap_lines") or 0)
            if cap and len(lines) > cap:
                out.append("HANDOFF.md `## State` is %d lines, over %d: history belongs in git"
                           % (len(lines), cap))
    out += ["GOTCHAS.md:%d %s" % (line, msg) for line, msg in rules.check()]
    claude = read_text(os.path.join(ROOT, "CLAUDE.md"))
    cap = int(config().get("claude_md_cap_chars") or 0)
    if cap and len(claude) > cap:
        out.append("CLAUDE.md is %d characters, over %d: move reasons to docs/WHY.md, "
                   "traps to GOTCHAS.md"
                   % (len(claude), cap))
    defined = set(re.findall(r"(?m)^## WHY (\S+)", read_text(path("why"))))
    for ref in sorted(set(re.findall(r"WHY (\w+)", claude)) - defined):
        out.append("CLAUDE.md points at WHY %s, which docs/WHY.md does not define" % ref)
    return out


def handoff_staged(staged):
    """A commit that changes the tools or rules must change HANDOFF too, or HANDOFF rots."""
    hand = rel(path("handoff"))
    if hand in staged:
        return []
    hit = [f for f in staged if matches_any(f, config().get("handoff_watch") or [])]
    if not hit:
        return []
    return ["this commit changes %s but not %s: update its State, decisions or Untested list"
            % (", ".join(hit[:4]) + (" ..." if len(hit) > 4 else ""), hand)]


def staged_files():
    got = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, capture_output=True,
                         text=True, stdin=subprocess.DEVNULL)
    return [f.strip() for f in got.stdout.splitlines() if f.strip()]


if __name__ == "__main__":
    utf8()
    bad = problems()
    if "--staged" in sys.argv:
        bad += handoff_staged(staged_files())
        import codecheck
        bad += codecheck.staged()
    for p in bad:
        print("- " + p)
    print("docs: %s" % ("%d problem(s)" % len(bad) if bad else "ok"))
    sys.exit(1 if bad else 0)
