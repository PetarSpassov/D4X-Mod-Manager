"""Each hook against its contract: a real-shaped payload to the real script, in a scratch state
folder. The cases live in tests/, one file per tool, and run here in ORDER, since later ones use
the state earlier ones leave. A new guard adds its case there in the same change.
"""
import importlib
import shutil
import sys
import tempfile

from _common import utf8
from tests import harness

ORDER = (("turnstart", "main"), ("pregate", "reads"), ("postgate", "main"), ("postgate", "budget"),
         ("journal", "main"), ("replycap", "main"), ("journal", "stop_never_blocks"),
         ("handback", "first_dot"), ("handback", "not_a_handback"), ("docs", "main"),
         ("docs", "precommit"), ("codecheck", "files"), ("codecheck", "rules"), ("noask", "main"),
         ("plan", "go_word"), ("plan", "gate"), ("plan", "answer_turn"), ("pregate", "size"),
         ("pregate", "declare"), ("optional", "main"), ("newproject", "main"))


def main():
    for module, case in ORDER:
        getattr(importlib.import_module("tests.test_" + module), case)()


if __name__ == "__main__":
    utf8()
    tmp = tempfile.mkdtemp(prefix="starter-selftest-")
    try:
        harness.setup(tmp)
        main()
    except Exception as broke:
        harness.check("selftest ran to the end", False, "%s: %s" % (type(broke).__name__, broke))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in harness.RESULTS:
        shown = "" if ok else "\n      " + " ".join(detail.split())[:300]
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, shown))
    bad = sum(1 for _, ok, _ in harness.RESULTS if not ok)
    print("\n%d of %d passed" % (len(harness.RESULTS) - bad, len(harness.RESULTS)))
    sys.exit(1 if bad else 0)
