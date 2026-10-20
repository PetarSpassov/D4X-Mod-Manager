"""UserPromptSubmit hook: a turn begins -- record the user's message and zero the turn's counters.

A first message of exactly `.` asks for the hand-back (handback.py); its print reaches Claude.
"""
import os
import time

from _common import event, load, now, save, save_turn, session_dir, session_id, utf8

TASK_LIST = ("TASK LIST: send the whole plan with the first call, and advance it with the call "
             "that starts each step.")


def main():
    utf8()
    ev = event()
    sid = session_id(ev)
    prompt = ev.get("prompt") or ""
    seen = os.path.join(session_dir(sid), "prompts.json")
    n = load(seen).get("n", 0)
    save(seen, {"n": n + 1})
    save_turn({"id": "%d" % (time.time() * 1000), "started": now(), "prompt": prompt,
               "chars": 0, "calls": 0, "wrote": []}, sid)
    import handback
    if handback.asked(prompt, first=(n == 0)):
        print(handback.push(sid))
    import replycap
    said = replycap.reminder(sid, prompt)
    if said:
        print(said)
    import plan
    if plan.go(prompt):
        print(TASK_LIST)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # a broken hook must never cost the user their message
