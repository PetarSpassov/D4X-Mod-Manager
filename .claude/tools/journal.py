"""The turn journal: one entry per turn, written as each reply finishes, so it never lags.

    journal.py [N]   the last N turns, as the briefing shows them. As the Stop hook it records
"""
import json
import os
import sys
import time

from _common import (STATE, assistant_text, clip, config, event, now, path, rel, session_id,
                     transcript, turn, user_text, utf8)

JOURNAL = os.path.join(STATE, "journal.jsonl")
KEEP = 2000


def rows():
    out = []
    try:
        with open(JOURNAL, encoding="utf-8") as fh:
            for line in fh:
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue  # a torn line is skipped
    except OSError:
        pass  # no journal yet means no rows
    return out


def reply_text(tp):
    """The assistant's text since the user's last real message, read from the transcript's end."""
    texts = []
    for o in reversed(transcript(tp, tail_bytes=2000000) if tp else []):
        if user_text(o):
            break
        said = assistant_text(o)
        if said:
            texts.append(said)
    return "\n".join(reversed(texts))


def record():
    ev = event()
    sid = session_id(ev)
    t = turn(sid)
    entry = {"turn": t.get("id") or now(), "sid": sid[:8], "t": now(),
             "u": clip(t.get("prompt"), 300),
             "calls": t.get("calls", 0), "wrote": t.get("wrote", []),
             "r": clip(reply_text(ev.get("transcript_path") or ""), 300)}
    old = rows()
    # Stop can fire more than once for one turn; the turn keeps one entry
    if old and old[-1].get("turn") == entry["turn"] and old[-1].get("sid") == entry["sid"]:
        old[-1] = entry
    else:
        old.append(entry)
    os.makedirs(STATE, exist_ok=True)
    tmp = JOURNAL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in old[-KEEP:]:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, JOURNAL)


def render(n=None):
    n = n or int(config().get("journal_turns") or 6)
    recent = rows()[-n:]
    if not recent:
        return ""
    docs = [path("handoff"), path("gotchas")]
    names = {rel(d) for d in docs}
    stamps = [os.path.getmtime(d) for d in docs if os.path.exists(d)]
    written = time.strftime("%Y-%m-%d %H:%M", time.localtime(max(stamps))) if stamps else "never"
    quiet = sum(1 for r in recent if not names & set(r.get("wrote") or []))
    out = ["=== TURN JOURNAL -- written as each reply finished, so it does not lag ===",
           "RECEIPT: last turn %s; the docs were last written %s. %d of the last %d turns "
           "wrote no doc -- what happened in those is here and nowhere else."
           % (recent[-1].get("t"), written, quiet,
                                                                     len(recent))]
    for r in recent:
        out.append("%s  [%s calls]  YOU: %s" % (r.get("t"), r.get("calls"), r.get("u")))
        if r.get("wrote"):
            out.append("    wrote: " + ", ".join(r["wrote"][:8]))
        if r.get("r"):
            out.append("    ME: " + r["r"])
    return "\n".join(out)


if __name__ == "__main__":
    utf8()
    if event():
        try:
            import handback
            import replycap
            ev = event()
            sid = session_id(ev)
            record()
            handback.finish(sid)
            post = handback.last_post(ev.get("transcript_path") or "", tail_bytes=2000000)
            replycap.note(sid, turn(sid).get("prompt"), post)
        except Exception as broke:
            sys.stderr.write("journal.py failed: %s: %s\n" % (type(broke).__name__, broke))
    else:
        print(render(int(sys.argv[1]) if len(sys.argv) > 1 else None) or "The journal is empty.")
