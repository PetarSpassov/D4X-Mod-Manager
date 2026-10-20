"""PreToolUse hook: no question popup, and no question box at the end of a turn, unless the user's
message this turn contains `questions_phrase`. A crash refuses, so a broken ban still bans.
"""
import sys

from _common import config, event, session_id, turn, utf8


def refusal(tool, inp, prompt):
    phrase = (config().get("questions_phrase") or "").lower()
    if phrase and phrase in prompt.lower():
        return ""
    if tool == "AskUserQuestion":
        return "question popups are banned; put the question in the reply text"
    if tool.endswith("wrap_up") and (inp.get("ask") or inp.get("actions")):
        return "no question or buttons in the wrap-up box; send the recap alone, ask in the reply"
    return ""


def main():
    utf8()
    ev = event()
    prompt = turn(session_id(ev)).get("prompt") or ""
    said = refusal(ev.get("tool_name") or "", ev.get("tool_input") or {}, prompt)
    if said:
        unlock = config().get("questions_phrase")
        sys.stderr.write("REFUSED by noask.py\n- %s (unlocked by \"%s\")\n" % (said, unlock))
        sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as broke:
        sys.stderr.write("REFUSED: noask.py failed closed: %s: %s\n" % (type(broke).__name__,
                                                                         broke))
        sys.exit(2)
