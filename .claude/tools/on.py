"""Read or move the one line in docs/HANDOFF.md that says what we are working on.

    on.py   print it;   on.py <what we are on>   move it (nothing else may)
"""
import re
import sys

from _common import path, read_text, utf8

LINE = re.compile(r"(?m)^\*\*► WE ARE ON:\*\*[^\n]*$")
TAIL = " *(moved only by `python .claude/tools/on.py`)*"


def current(text=None):
    text = read_text(path("handoff")) if text is None else text
    m = LINE.search(text)
    if not m:
        return None
    return m.group(0).replace("**► WE ARE ON:**", "").replace(TAIL, "").strip()


def move(what):
    text = read_text(path("handoff"))
    if len(LINE.findall(text)) != 1:
        raise SystemExit("HANDOFF.md must hold exactly one `**► WE ARE ON:**` line; "
                         "fix that by hand first.")
    new = "**► WE ARE ON:** %s%s" % (what.strip(), TAIL)
    with open(path("handoff"), "w", encoding="utf-8", newline="") as fh:
        fh.write(LINE.sub(lambda _: new, text, count=1))
    return new


if __name__ == "__main__":
    utf8()
    if len(sys.argv) > 1:
        print(move(" ".join(sys.argv[1:])))
    else:
        print(current() or "No WE ARE ON line in HANDOFF.md.")
