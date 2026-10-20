"""Shared pieces of the self-test: run a real script with a real-shaped payload, record results."""
import json
import os
import shutil
import subprocess
import sys
import types

from _common import ROOT, TOOLS

OPTIONAL = os.path.join(ROOT, ".claude", "optional")
SID = "selftest-%d" % os.getpid()
RESULTS = []
S = types.SimpleNamespace()


def run(script, payload=None, args=(), env=None, where=TOOLS):
    p = subprocess.run([sys.executable, os.path.join(where, script)] + list(args),
                       input=json.dumps(payload) if payload is not None else "",
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=env, cwd=ROOT, timeout=60)
    return p.returncode, p.stdout, p.stderr


def snippet(env, code):
    full = "import sys; sys.path[:0] = %r\n%s" % ([TOOLS], code)
    p = subprocess.run([sys.executable, "-c", full], capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=ROOT, timeout=60)
    return p.stdout.strip() + p.stderr.strip()


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def line(kind, text):
    role = "user" if kind == "user" else "assistant"
    content = [{"type": "text", "text": text}]
    return json.dumps({"type": kind, "message": {"role": role, "content": content}})


def tool_line(inp=None):
    """A transcript entry that is only a tool call."""
    use = {"type": "tool_use", "id": "t1", "name": "Bash", "input": inp or {}}
    return json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [use]}})


def tool_event(tool, inp, resp=None):
    return {"session_id": SID, "tool_name": tool, "tool_input": inp, "tool_response": resp,
            "cwd": S.tmp}


def setup(tmp):
    """A scratch state folder with its own config: the live journal and docs are never touched."""
    S.tmp = tmp
    S.env = dict(os.environ, STARTER_STATE=os.path.join(tmp, "state"),
                 STARTER_CONFIG=os.path.join(tmp, "cfg.json"), CLAUDE_CODE_SESSION_ID=SID,
                 PYTHONIOENCODING="utf-8")
    S.live_env = dict(os.environ, PYTHONIOENCODING="utf-8")
    S.live_env.pop("STARTER_CONFIG", None)
    S.live_env.pop("STARTER_STATE", None)
    shutil.copy(os.path.join(ROOT, "docs", "HANDOFF.md"), os.path.join(tmp, "HANDOFF.md"))
    write(os.path.join(tmp, "GOTCHAS.md"), "## T — test group\n\n- **A test rule.**\n"
                                           "  names: `selftest_subject`\n  sign: it fired\n")
    write(os.path.join(tmp, "cfg.json"), json.dumps({
        "handoff": os.path.join(tmp, "HANDOFF.md"), "gotchas": os.path.join(tmp, "GOTCHAS.md"),
        "why": os.path.join(ROOT, "docs", "WHY.md"),
        "coverage": os.path.join(tmp, "coverage.json"),
        "read_cap_bytes": 1000, "never_read": ["*.secretdump"], "turn_budget_chars": 2000,
        "long_turn_phrase": "long turn", "long_turn_multiplier": 5}))
    S.small, S.big, S.secret = (os.path.join(tmp, n)
                                for n in ("small.txt", "big.txt", "x.secretdump"))
    write(S.small, "tiny\n")
    write(S.big, "x" * 5000)
    write(S.secret, "s")
    S.turn_file = os.path.join(tmp, "state", "sessions", SID, "turn.json")
