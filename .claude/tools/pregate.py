"""PreToolUse hook: refuse the reads that sink a session, and code files growing past the limit.
Exit 2 refuses, with the reason."""
import os
import re
import shlex
import sys
import time

from _common import (ROOT, SHELLS, TOOLS, assistant_text, budget, config, event, matches_any, rel,
                     since_prompt, turn, utf8)

WHOLE = re.compile(r"^(cat|type|less|more|get-content|gc)(\.exe)?$", re.I)
READERS = re.compile(r"^(cat|type|less|more|head|tail|get-content|gc|sed|awk|grep|rg|findstr|"
                     r"select-string|wc|ls|dir|find|get-childitem)(\.exe)?$", re.I)
SEGMENT = re.compile(r"\|\||&&|[|;\n]")
REDIRECT = re.compile(r"^\d?>>?$|^<<")


def tokens(seg):
    try:
        return shlex.split(seg, posix=True)
    except ValueError:
        return seg.split()


def too_big(p):
    cap = int(config().get("read_cap_bytes") or 0)
    try:
        return bool(cap) and os.path.getsize(p) > cap
    except OSError:
        return False


def why_not(p):
    if matches_any(p, config().get("never_read") or []):
        return "`%s` is on the never-read list in .claude/starter.json" % rel(p)
    if too_big(p):
        return "`%s` is %d KB, over the read cap" % (rel(p), os.path.getsize(p) // 1024)
    return ""


def check_read(inp):
    p = inp.get("file_path") or ""
    if not p or inp.get("limit") or not os.path.isfile(p):
        return ""
    said = why_not(p)
    return said and said + ". Find the anchor with Grep, then Read a range with offset/limit."


def check_shell(cmd, cwd):
    """A whole-file reader aimed at a refused file. A write (`cat > f`) or heredoc is no read."""
    for seg in SEGMENT.split(cmd or ""):
        toks = tokens(seg.strip())
        if not toks or not WHOLE.match(os.path.basename(toks[0])):
            continue
        for tok in toks[1:]:
            if REDIRECT.match(tok) or tok.startswith(">"):
                break
            if tok.startswith("-"):
                continue
            p = tok if os.path.isabs(tok) else os.path.join(cwd, tok)
            said = os.path.isfile(p) and why_not(p)
            if said:
                return said + ". Search it with grep -n, then print a range (sed -n 'X,Yp')."
    return ""


def is_read(tool, inp):
    if tool in ("Read", "Grep", "Glob", "WebFetch"):
        return True
    if tool in SHELLS:
        segs = [tokens(s.strip()) for s in SEGMENT.split(inp.get("command") or "") if s.strip()]
        return bool(segs) and all(t and READERS.match(os.path.basename(t[0])) for t in segs)
    return False


def check_budget(tool, inp):
    t = turn()
    cap = budget(t)
    if not cap or t.get("chars", 0) < cap or not is_read(tool, inp):
        return ""
    return ("this turn has taken in %d characters of tool output; its budget is %d. Stop reading: "
            "answer with what you have and say what is missing. "
            "(The user can say \"%s\" to widen it.)"
            % (t.get("chars", 0), cap, config().get("long_turn_phrase")))


def check_plan(tool, inp):
    if not config().get("plan_required"):
        return ""
    if not os.path.isfile(os.path.join(TOOLS, "plan.py")):
        return "plan_required is on but .claude/tools/plan.py is missing"
    import plan
    return plan.refusal(tool, inp)


def _lines(text):
    return text.count("\n") + (1 if text and not text.endswith("\n") else 0)


def _landed(tool, inp, old):
    """The file's text once this write or edit lands."""
    if tool == "Write":
        return inp.get("content") or ""
    new = old
    for e in inp.get("edits") or [inp]:
        new = new.replace(e.get("old_string") or "", e.get("new_string") or "",
                          -1 if e.get("replace_all") else 1)
    return new


def check_size(tool, inp):
    """A code file may not grow past `file_lines_refuse`; one already past it may only shrink."""
    c = config()
    limit, f = c.get("file_lines_refuse") or 0, inp.get("file_path") or ""
    if not limit or tool not in ("Write", "Edit", "MultiEdit"):
        return ""
    if not matches_any(f, c.get("code_globs") or []):
        return ""
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            old = fh.read()
    except OSError:
        old = ""
    before, after = _lines(old), _lines(_landed(tool, inp, old))
    if after <= limit or after <= before:
        return ""
    return ("`%s` would be %d lines; the limit is %d (rule 12h). "
            "Propose a split to the user and stop."
            % (rel(f), after, limit))


DECLARED = re.compile(r"^(Answer|Change) turn\.")
DECLARE_TRIES, DECLARE_WAIT = 4, 0.5


def check_declared(tp):
    """Rule 3.0: no tool call until this turn's first text opens with `Answer turn.` or
    `Change turn.`. The turn starts at the user's recorded message; lines the harness injects
    later do not restart it."""
    prompt = (turn().get("prompt") or "").strip()
    if not config().get("declare_required") or not tp or not prompt:
        return ""
    for attempt in range(DECLARE_TRIES):
        entries = since_prompt(tp, prompt)
        if entries is None:
            return ""
        said = next((t for t in map(assistant_text, entries) if t), "")
        if said:
            break
        # the first call of a message can arrive before its text reaches the transcript
        time.sleep(DECLARE_WAIT)
    if DECLARED.match(said):
        return ""
    return ("this turn's text does not open with `Answer turn.` or `Change turn.` "
            "and the plan (rule 3.0). "
            "Write that line first, then call the tool again.")


def check_handback():
    import handback
    if not handback.due():
        return ""
    return ("this turn is a `.` hand-back: the whole reply is the held post, word for word, "
            "with no tool "
            "call. It was printed at the top of this turn.")


def main():
    utf8()
    ev = event()
    tool, inp = ev.get("tool_name") or "", ev.get("tool_input") or {}
    said = [check_handback() or check_declared(ev.get("transcript_path") or "")]
    if tool == "Read":
        said.append(check_read(inp))
    if tool in SHELLS:
        said.append(check_shell(inp.get("command") or "", ev.get("cwd") or ROOT))
    said.append(check_budget(tool, inp))
    said.append(check_plan(tool, inp))
    said.append(check_size(tool, inp))
    said =[s for s in said if s]
    if said:
        listed = "\n".join("- " + s for s in said)
        sys.stderr.write("REFUSED by .claude/tools/pregate.py\n" + listed + "\n")
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as broke:
        # a gate that crashes lets the call through: a broken guard must not stop all work
        sys.stderr.write("pregate.py failed open: %s: %s\n" % (type(broke).__name__, broke))
