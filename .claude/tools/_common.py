"""Shared plumbing for hooks and tools: paths, config, utf-8 output, session state, transcripts."""
import fnmatch
import json
import os
import re
import sys
import time

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(TOOLS))

# the self-test points these at a scratch folder so it never touches the live record
STATE = os.environ.get("STARTER_STATE") or os.path.join(ROOT, ".claude", "state")
CONFIG = os.environ.get("STARTER_CONFIG") or os.path.join(ROOT, ".claude", "starter.json")

DEFAULTS = {
    "handoff": "docs/HANDOFF.md",
    "gotchas": "docs/GOTCHAS.md",
    "why": "docs/WHY.md",
    "read_cap_bytes": 200000,
    "never_read": [],
    "turn_budget_chars": 150000,
    "long_turn_phrase": "long turn",
    "long_turn_multiplier": 5,
    "journal_turns": 6,
    "claude_md_cap_chars": 7000,
    "handoff_state_cap_lines": 20,
    "handoff_watch": ["CLAUDE.md", ".claude/tools/*", ".claude/skills/*", ".claude/settings.json",
                      ".claude/starter.json", ".githooks/*"],
    "plan_required": True,
    "declare_required": True,
    "file_lines_refuse": 800,
    "code_globs": ["*.py", "*.js", "*.jsx", "*.ts", "*.tsx", "*.go", "*.rs", "*.java", "*.kt",
                   "*.cs", "*.c", "*.cpp", "*.h", "*.hpp", "*.rb", "*.php", "*.swift", "*.gd",
                   "*.lua", "*.sh"],
    "code_limits": {"line": 100, "function": 50, "nesting": 3, "params": 5, "complexity": 10,
                    "file": 400, "comment_block": 2, "docstring": 3, "depth": 4},
    "banned_folders": ["utils", "misc", "helpers"],
    "questions_phrase": "questions are allowed",
    "reply_cap_chars": 700,
    "reply_cap_asked_chars": 1800,
    "long_reply_phrase": "long reply",
}
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
SHELLS = ("Bash", "PowerShell")


def utf8():
    """Windows hands hooks the console code page; one non-ASCII character would kill the hook."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass  # a stream without reconfigure keeps its encoding


_CFG = None


def config():
    global _CFG
    if _CFG is None:
        _CFG = dict(DEFAULTS)
        try:
            with open(CONFIG, encoding="utf-8") as fh:
                _CFG.update(json.load(fh))
        except Exception:
            pass  # no config file, or a bad one, means the defaults
    return _CFG


def path(key):
    """A configured project file as an absolute path."""
    p = config()[key]
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


_EVENT = None


STDIN_WAIT = 2.0


def _read_stdin(wait):
    """stdin, or "" if it stays open past `wait` seconds: a backgrounded shell never closes it."""
    import threading
    got = []
    reader = threading.Thread(target=lambda: got.append(sys.stdin.read()), daemon=True)
    reader.start()
    reader.join(wait)
    return got[0] if got else ""


def event():
    """The hook's JSON from stdin, read once: stdin can only be consumed once."""
    global _EVENT
    if _EVENT is None:
        _EVENT = {}
        try:
            if sys.stdin is not None and not sys.stdin.isatty():
                raw = _read_stdin(STDIN_WAIT)
                if raw.strip():
                    _EVENT = json.loads(raw) or {}
        except Exception:
            _EVENT = {}
    return _EVENT


def session_id(ev=None):
    """Hooks get it from their event; a tool run from the shell gets it from the environment."""
    ev = event() if ev is None else ev
    sid = str(ev.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    return sid or "unnamed"


def session_dir(sid=None):
    """Per-session state: a second session in this folder must never touch this one's markers."""
    d = os.path.join(STATE, "sessions", sid or session_id())
    os.makedirs(d, exist_ok=True)
    return d


def load(p, default=None):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {} if default is None else default


def save(p, data):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def turn(sid=None):
    return load(os.path.join(session_dir(sid), "turn.json"))


def save_turn(data, sid=None):
    save(os.path.join(session_dir(sid), "turn.json"), data)


def read_text(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


def rel(p):
    """A path as the project names it: relative to the root, forward slashes."""
    try:
        r = os.path.relpath(os.path.abspath(p), ROOT)
    except ValueError:
        r = p
    return r.replace("\\", "/")


def matches_any(p, patterns):
    r, base = rel(p), os.path.basename(p)
    return any(fnmatch.fnmatch(r, pat) or fnmatch.fnmatch(base, pat) for pat in patterns)


def budget(t=None):
    """This turn's allowance of tool output in characters; 0 is off. The user's phrase widens it."""
    cfg = config()
    base = int(cfg.get("turn_budget_chars") or 0)
    t = turn() if t is None else t
    phrase = (cfg.get("long_turn_phrase") or "").lower()
    if base and phrase and phrase in (t.get("prompt") or "").lower():
        base *= int(cfg.get("long_turn_multiplier") or 1)
    return base


def now():
    return time.strftime("%Y-%m-%d %H:%M")


def clip(s, n):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 3] + "..."


# ---- transcripts: Claude Code's JSONL record of a session

NOISE = re.compile(r"<(system-reminder|local-command-stdout|local-command-stderr|command-[a-z-]+)>"
                   r".*?</\1>", re.S)


def transcript(p, tail_bytes=0):
    """A transcript's entries, oldest first; `tail_bytes` reads only the end of a big one."""
    out = []
    try:
        with open(p, "rb") as fh:
            if tail_bytes:
                fh.seek(0, os.SEEK_END)
                fh.seek(max(0, fh.tell() - tail_bytes))
            data = fh.read().decode("utf-8", "replace")
    except Exception:
        return out
    for line in data.splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue  # a half-written last line is skipped
    return out


def blocks(o):
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return c if isinstance(c, list) else []


def user_text(o):
    """What the user typed in this entry, or "" for a tool result, meta entry or command noise."""
    if o.get("type") != "user" or o.get("isMeta") or o.get("isSidechain"):
        return ""
    got = blocks(o)
    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in got):
        return ""
    text = "\n".join(b.get("text", "") for b in got
                     if isinstance(b, dict) and b.get("type") == "text")
    return NOISE.sub("", text).strip()


def assistant_text(o):
    if o.get("type") != "assistant" or o.get("isSidechain"):
        return ""
    return "\n".join(b.get("text", "") for b in blocks(o)
                     if isinstance(b, dict) and b.get("type") == "text").strip()


def uses_a_tool(o):
    return o.get("type") == "assistant" and any(
        isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks(o))
