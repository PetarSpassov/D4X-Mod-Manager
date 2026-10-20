"""Why a CLAUDE.md rule exists: `why.py <N>` for rule N, no argument for the list."""
import re
import sys

from _common import path, read_text, utf8


def sections():
    text = read_text(path("why"))
    return {m.group(1): m.group(0).strip()
            for m in re.finditer(r"(?ms)^## WHY (\S+)[^\n]*\n.*?(?=^## |\Z)", text)}


if __name__ == "__main__":
    utf8()
    found = sections()
    if len(sys.argv) > 1:
        print(found.get(sys.argv[1].upper()) or found.get(sys.argv[1])
              or "No `## WHY %s` in docs/WHY.md." % sys.argv[1])
    else:
        print("\n".join(s.splitlines()[0] for s in found.values()))
