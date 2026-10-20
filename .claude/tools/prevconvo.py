"""The conversation before a /clear, minus tool noise; run it when the user refers back to it.

    prevconvo.py [--turns N | --all]   default: the most recent part of the previous session
"""
import glob
import os
import re
import sys

from _common import ROOT, assistant_text, clip, load, session_dir, transcript, user_text, utf8

CAP = 12000
EACH = 1500


def previous():
    """(file, note): the conversation before this one."""
    start = load(os.path.join(session_dir(), "start.json"))
    d = start.get("transcript_dir")
    if not d or not os.path.isdir(d):
        d = os.path.join(os.path.expanduser("~"), ".claude", "projects",
                         re.sub(r"[^A-Za-z0-9]", "-", ROOT))
    files = sorted(glob.glob(os.path.join(d, "*.jsonl")), key=os.path.getmtime, reverse=True)
    roster = start.get("roster")
    note = ""
    if roster is not None:
        # every transcript that existed when this session started is an earlier one
        files = [f for f in files if os.path.basename(f) in roster]
    else:
        files, note = files[1:], ("(no record of this session's start, so the newest "
                                  "transcript was "
                                  "taken to be this one and skipped)")
    # a `.` hand-back-only session holds nothing new: the conversation is the one before it
    for f in files:
        turns = exchanges(f)
        if not (len(turns) == 1 and turns[0]["u"].strip() == "."):
            return f, note
    return None, note


def exchanges(p):
    out = []
    for o in transcript(p):
        u = user_text(o)
        if u:
            out.append({"u": u, "r": []})
            continue
        said = assistant_text(o)
        if said and out:
            out[-1]["r"].append(said)
    return out


def main(argv):
    utf8()
    p, note = previous()
    if not p:
        print("No previous conversation found for this project.")
        return
    turns = exchanges(p)
    if "--turns" in argv:
        turns = turns[-int(argv[argv.index("--turns") + 1]):]
    blocks = []
    for t in turns:
        reply_text = clip("\n".join(t["r"]), EACH) or "(no text)"
        blocks.append("YOU: %s\nME: %s" % (clip(t["u"], EACH), reply_text))
    if "--all" not in argv:
        kept, size = [], 0
        for b in reversed(blocks):
            if size + len(b) > CAP and kept:
                break
            kept.append(b)
            size += len(b)
        if len(kept) < len(blocks):
            left = "(%d earlier exchanges left out; --all prints them)"
            note = (note + " " if note else "") + left % (
                len(blocks) - len(kept))
        blocks = list(reversed(kept))
    print("=== PREVIOUS CONVERSATION: %s ===" % os.path.basename(p))
    if note:
        print(note)
    print("\n\n".join(blocks))


if __name__ == "__main__":
    main(sys.argv[1:])
