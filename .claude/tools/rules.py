"""The traps ledger (docs/GOTCHAS.md), retrieved by subject instead of read whole.
    rules.py <thing> | --index | --for "<text>" (postgate) | --check (doccheck)
A rule: a bold line of at most 120 chars, `names:` unique to it, then an optional `sign:`.
"""
import re
import sys

from _common import path, read_text, utf8

GROUP = re.compile(r"^##\s+(.+?)\s*$")
RULE = re.compile(r"^- \*\*(.+?)\*\*\s*$")
NAMES = re.compile(r"^\s+names:\s*(.*)$")
SIGN = re.compile(r"^\s+sign:\s*(.*)$")
TICKED = re.compile(r"`([^`]+)`")
TITLE_MAX, SIGN_MAX, NAMES_MAX = 120, 120, 6


def parse(text=None):
    text = read_text(path("gotchas")) if text is None else text
    rules, group, cur = [], "", None
    for n, line in enumerate(text.splitlines(), 1):
        m = GROUP.match(line)
        if m:
            group, cur = m.group(1), None
            continue
        m = RULE.match(line)
        if m:
            cur = {"group": group, "title": m.group(1), "names": [], "sign": "", "line": n,
                   "extra": []}
            rules.append(cur)
            continue
        if cur is None:
            continue
        if not line.strip():
            cur = None
        elif NAMES.match(line):
            cur["names"] = TICKED.findall(NAMES.match(line).group(1))
        elif SIGN.match(line):
            cur["sign"] = SIGN.match(line).group(1).strip()
        else:
            cur["extra"].append(line.strip())
    return rules


def _word(name):
    return re.compile(r"(?<![\w])%s(?![\w])" % re.escape(name.replace("\\", "/")), re.I)


def for_text(text):
    return [r for r in parse() if any(_word(n).search(text) for n in r["names"])]


def about(thing):
    t = thing.lower()
    return [r for r in parse()
            if t in " ".join([r["title"], r["sign"]] + r["names"] + r["extra"]).lower()]


def fmt(r):
    out = ["TRAP (%s): **%s**" % (r["group"] or "GOTCHAS.md", r["title"])]
    if r["sign"]:
        out.append("  sign: " + r["sign"])
    return "\n".join(out)


def index():
    groups = {}
    for r in parse():
        groups.setdefault(r["group"], []).append(r)
    out = ["%d traps by group -- retrieve with `rules.py <thing>`; "
           "the hooks push the ones a call touches."
           % sum(len(v) for v in groups.values())]
    for g, rs in groups.items():
        names = [n for r in rs for n in r["names"]][:10]
        out.append("  %-34s %3d   %s" % (g[:34], len(rs), ", ".join(names)))
    return "\n".join(out)


def check(text=None):
    """(line, problem) for every rule that breaks the format."""
    out, owner = [], {}
    for r in parse(text):
        if len(r["title"]) > TITLE_MAX:
            out.append((r["line"], "title is %d characters, over %d"
                        % (len(r["title"]), TITLE_MAX)))
        if not r["names"]:
            out.append((r["line"], "no `names:` line -- a rule nobody can retrieve is never seen"))
        if len(r["names"]) > NAMES_MAX:
            out.append((r["line"], "%d names, over %d" % (len(r["names"]), NAMES_MAX)))
        if len(r["sign"]) > SIGN_MAX:
            out.append((r["line"], "sign is over %d characters" % SIGN_MAX))
        if r["extra"]:
            out.append((r["line"],
                        "a rule is a title, names and a sign; move the rest to docs/WHY.md"))
        for n in r["names"]:
            k = n.lower()
            if k in owner:
                out.append((r["line"], "`%s` is already a name of the rule at line %d; merge them"
                            % (n, owner[k])))
            else:
                owner[k] = r["line"]
    return out


def main(argv):
    utf8()
    if not argv or argv[0] == "--index":
        print(index())
    elif argv[0] == "--check":
        bad = check()
        for line, msg in bad:
            print("GOTCHAS.md:%d %s" % (line, msg))
        print("%d problem(s)" % len(bad))
        return 1 if bad else 0
    elif argv[0] == "--for":
        found = for_text(" ".join(argv[1:]))
        print("\n\n".join(fmt(r) for r in found) or "no rule names appear in that text")
    else:
        found = about(" ".join(argv))
        print("\n\n".join(fmt(r) + "\n  names: " + ", ".join("`%s`" % n for n in r["names"])
                          for r in found) or "no rule mentions that")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
