"""Rule 12's mechanical limits: sizes, nesting, comments, folder names. Judgement items stay rules.

    python .claude/tools/codecheck.py [files]    every violation (default: every tracked file)
"""
import ast
import collections
import io
import os
import re
import subprocess
import sys
import tokenize

from _common import ROOT, config, matches_any, read_text, rel, utf8

CONTENT = (
    ("has an emoji", re.compile("[☀-➿⭐️\U0001f000-\U0001faff]")),
    ("has a date", re.compile(r"\b(19|20)\d\d-[01]\d-[0-3]\d\b|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug"
                              r"|Sep|Oct|Nov|Dec)[a-z]* (19|20)\d\d\b")),
    ("has emphasis capitals",
     re.compile(r"\b(IMPORTANT|NEVER|ALWAYS|MUST|NOTE|WARNING|CRITICAL)\b")),
    ("tells history or quotes the user", re.compile(
        r"(?i)\b(previously|no longer|originally|was changed|we changed"
        r"|the user (said|asked|wants))\b")),
)
HASH = (".py", ".sh", ".rb", ".gd")
SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler)
BLOCKS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try) + tuple(
    getattr(ast, n) for n in ("Match", "TryStar") if hasattr(ast, n))


def limits():
    return config().get("code_limits") or {}


def _py_comments(text):
    toks = tokenize.generate_tokens(io.StringIO(text).readline)
    return [(t.start[0], t.string, not t.line[:t.start[1]].strip()) for t in toks
            if t.type == tokenize.COMMENT and not t.string.startswith("#!")]


def comments(name, text):
    """(line, text, whole_line) per comment: Python by its tokenizer, the rest by line prefix."""
    ext = os.path.splitext(name)[1]
    if ext == ".py":
        try:
            return _py_comments(text)
        except (tokenize.TokenError, SyntaxError):
            pass  # a file that does not tokenize falls back to the prefix scan below
    marks = ("#",) if ext in HASH else ("--",) if ext == ".lua" else ("//", "/*", "*")
    return [(i, ln.strip(), True) for i, ln in enumerate(text.splitlines(), 1)
            if ln.strip().startswith(marks) and not ln.strip().startswith("#!")]


def _block(block, lim):
    if len(block) <= lim["comment_block"]:
        return []
    key = "comment block over %d lines: `%s`" % (lim["comment_block"], block[0][1][:40])
    return [(block[0][0], key, " (%d)" % len(block))]


def comment_violations(found, lim):
    out, block = [], []
    for line, body, whole in found:
        out += [(line, "comment %s: `%s`" % (what, body[:40]), "") for what, rx in CONTENT
                if rx.search(body)]
        if whole and block and line == block[-1][0] + 1:
            block.append((line, body))
            continue
        out += _block(block, lim)
        block = [(line, body)] if whole else []
    return out + _block(block, lim)


def _inside(node):
    """Every node in a function's own body, not in the functions or classes it defines."""
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, SCOPES):
            yield child
            yield from _inside(child)


def _complexity(fn):
    n = 1
    for node in _inside(fn):
        if isinstance(node, BRANCHES):
            n += 1
        elif isinstance(node, ast.BoolOp):
            n += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            n += 1 + len(node.ifs)
    return n


def _depth(node, level=0):
    """Deepest block nesting below node; an elif counts at its if's level, not one deeper."""
    deepest = level
    for child in ast.iter_child_nodes(node):
        if isinstance(child, SCOPES):
            continue
        elif_ = isinstance(node, ast.If) and node.orelse == [child] and isinstance(child, ast.If)
        step = isinstance(child, BLOCKS) and not elif_
        deepest = max(deepest, _depth(child, level + step))
    return deepest


def _function(fn, lim):
    a = fn.args
    params = [x.arg for x in a.posonlyargs + a.args + a.kwonlyargs if x.arg not in ("self", "cls")]
    measures = (("lines", fn.end_lineno - fn.lineno + 1, lim["function"]),
                ("parameters", len(params) + bool(a.vararg) + bool(a.kwarg), lim["params"]),
                ("complexity", _complexity(fn), lim["complexity"]),
                ("nesting", _depth(fn), lim["nesting"]))
    return [(fn.lineno, "function `%s` %s over %d" % (fn.name, what, cap), " (%d)" % n)
            for what, n, cap in measures if n > cap]


def _docstring(node, lim):
    if not isinstance(node, (ast.Module,) + SCOPES):
        return []
    n = len((ast.get_docstring(node) or "").splitlines())
    if n <= lim["docstring"]:
        return []
    return [(getattr(node, "lineno", 1), "docstring of `%s` over %d lines"
             % (getattr(node, "name", "module"), lim["docstring"]), " (%d)" % n)]


def _silent(handler, commented):
    quiet = all(isinstance(s, (ast.Pass, ast.Continue)) for s in handler.body)
    return quiet and not commented & set(range(handler.lineno, handler.end_lineno + 1))


def python_violations(text, lim, commented):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return []  # an unparseable file gets the text checks only; Python itself reports the error
    out = []
    for node in ast.walk(tree):
        out += _docstring(node, lim)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += _function(node, lim)
        if isinstance(node, ast.ExceptHandler) and _silent(node, commented):
            out.append((node.lineno, "except swallows the error, no comment says why", ""))
    return out


def check_text(name, text):
    """Every violation in one file's text as (line, key, detail); edits elsewhere keep the key."""
    if not text or not matches_any(name, config().get("code_globs") or []):
        return []
    lim, lines = limits(), text.splitlines()
    out = [(i, "line over %d chars: `%s`" % (lim["line"], ln.strip()[:40]), " (%d)" % len(ln))
           for i, ln in enumerate(lines, 1) if len(ln) > lim["line"]]
    if len(lines) > lim["file"]:
        out.append((1, "file over %d lines" % lim["file"], " (%d)" % len(lines)))
    found = comments(name, text)
    out += comment_violations(found, lim)
    if name.endswith(".py"):
        out += python_violations(text, lim, {ln for ln, _, _ in found})
    return out


def added(name, old, new):
    """The violations new has over old, so code already over a limit does not block every commit."""
    before = collections.Counter(key for _, key, _ in check_text(name, old))
    now = check_text(name, new)
    after = collections.Counter(key for _, key, _ in now)
    return [v for v in now if after[v[1]] > before[v[1]]]


def path_violations(name):
    lim, parts = limits(), name.replace("\\", "/").split("/")
    folders, base = parts[:-1], parts[-1]
    if folders[:1] == [".."]:
        return []
    banned = set(map(str.lower, config()["banned_folders"]))
    out = ["folder `%s/` is banned: group by feature" % f for f in folders if f.lower() in banned]
    if len(folders) > lim["depth"]:
        out.append("is %d folders deep, over %d" % (len(folders), lim["depth"]))
    if re.search(r"_v\d+(\.|$)", base):
        out.append("is a second copy: change the first one instead")
    if not folders and matches_any(base, config()["code_globs"]):
        out.append("is code at the root, which holds config and README only")
    return ["%s %s" % (name, m) for m in out]


def _git(*args):
    got = subprocess.run(["git", "-c", "core.quotepath=off"] + list(args), cwd=ROOT,
                         capture_output=True, stdin=subprocess.DEVNULL)
    return got.stdout.decode("utf-8", "replace") if got.returncode == 0 else ""


def staged():
    """What a commit adds: new paths that break the folder rules, new violations in staged code."""
    new = _git("diff", "--cached", "--name-only", "--diff-filter=AR").splitlines()
    out = [p for f in new for p in path_violations(f)]
    for f in _git("diff", "--cached", "--name-only", "--diff-filter=ACMR").splitlines():
        found = added(f, _git("show", "HEAD:" + f), _git("show", ":" + f))
        out += ["%s:%d %s%s" % (f, line, key, detail) for line, key, detail in found]
    return out


if __name__ == "__main__":
    utf8()
    files = [rel(f) for f in sys.argv[1:]] or _git("ls-files").splitlines()
    bad = []
    for f in files:
        bad += path_violations(f)
        text = read_text(os.path.join(ROOT, f))
        bad += ["%s:%d %s%s" % (f, line, key, detail) for line, key, detail in check_text(f, text)]
    for p in bad:
        print("- " + p)
    print("code: %s" % ("%d problem(s)" % len(bad) if bad else "ok"))
    sys.exit(1 if bad else 0)
