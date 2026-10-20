"""codecheck.py: rule 12's countable limits, through the real script."""
import os

from tests.harness import S, check, run, snippet, write

BAD = ("def f(a, b, c, d, e, g):\n    # 2026-10-17 IMPORTANT \u2705\n"
       "    for x in a:\n        if x:\n            while b:\n                if c:\n"
       "                    pass\n    try:\n        g()\n    except Exception:\n"
       "        pass\n    return '%s'\n" % ("x" * 100))
GOOD = ("def g(x):\n    \"\"\"Says why.\"\"\"\n    if x == 1:\n        return 1\n"
        "    elif x == 2:\n        return 2\n    elif x == 3:\n        for y in x:\n"
        "            if y:\n                return y\n    try:\n        return x\n"
        "    except KeyError:\n        pass  # a missing key is an answer\n")
FLAGS = ("parameters over 5", "nesting over 3", "has a date", "emphasis capitals",
         "has an emoji", "line over 100", "except swallows")


def files():
    bad_py, good_py = os.path.join(S.tmp, "bad.py"), os.path.join(S.tmp, "good.py")
    write(bad_py, BAD)
    code, out, _ = run("codecheck.py", args=[bad_py], env=S.live_env)
    for key in FLAGS:
        check("codecheck flags %s" % key, code == 1 and key in out, out)
    write(good_py, GOOD)
    code, out, _ = run("codecheck.py", args=[good_py], env=S.live_env)
    check("codecheck passes clean code with an elif chain", code == 0, out)


def rules():
    said = snippet(S.live_env, "import codecheck as c; old = 'x = 1  # ' + 'y' * 100 + '\\n'\n"
                               "print(len(c.added('a.py', old, old + 'z = 2\\n')),"
                               " len(c.added('a.py', old, old + 'w = 3  # ' + 'q' * 100 + '\\n')))")
    check("codecheck refuses only what a commit adds", said == "0 1", said)
    said = snippet(S.live_env, "import codecheck as c; print([len(c.path_violations(p)) for p in"
                               " ('src/utils/x_v2.py', 'main.py', 'a/b/c/d/e/f.txt', 'src/a.py')])")
    check("codecheck path rules: banned, copy, root, depth", said == "[2, 1, 1, 0]", said)
