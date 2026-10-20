"""turnstart.py records the user's message for the turn's other hooks."""
from tests.harness import S, SID, check, run


def main():
    code, _, _ = run("turnstart.py", {"session_id": SID, "prompt": "please check"}, env=S.env)
    with open(S.turn_file, encoding="utf-8") as fh:
        check("turnstart records the prompt", code == 0 and "please check" in fh.read())
