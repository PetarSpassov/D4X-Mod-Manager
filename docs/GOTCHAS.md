# Gotchas

Never read this whole: `python .claude/tools/rules.py <thing>` retrieves by subject, and the hooks push a
rule the first time a call in a session mentions one of its names. A rule is exactly three lines:
a bold title (≤120 characters), `names:` (≤6 backticked subjects no other rule carries), and an optional
`sign:` (≤120), saying what falling into it looks like. Reasons go to `WHY.md`. Groups are `##` headings.

## A — Tooling and hooks

- **Force utf-8 on a hook's stdout and stderr; Windows hands it the console code page.**
  names: `_common.py`, `reconfigure`, `UnicodeEncodeError`
  sign: a hook prints nothing, or dies on the first non-ASCII character

- **Key per-turn state by session: a second session in the same folder overwrites shared markers.**
  names: `session_dir`, `.claude/state`
  sign: a guard refuses work the user just asked for, or permits what it should refuse

- **A hand-written fixture tests a hook's logic, never its contract; run the real tool once and watch.**
  names: `selftest.py`, `tool_response`
  sign: every test passes and the hook does nothing in a real session

- **Key the hand-back on the user's `.`, never on SessionStart's `source`: it misreports clears.**
  names: `handback.py`, `handback.json`
  sign: a post quoted back after a restart, or a real clear that quotes nothing

- **A hook added mid-session may not load until a restart; leave the check in .claude/state/pending_check.md.**
  names: `settings.json`, `pending_check.md`
  sign: a brand-new guard "works" without ever having fired

- **A Stop hook never sends a reply back: the user has read it, so a redo only doubles it.**
  names: `journal.py`, `replycap.py`, `Stop`
  sign: the same reply posted twice, the second opening "Short version:"

- **A backgrounded shell leaves stdin open; a tool reading it to EOF hangs, so read it with a timeout.**
  names: `event()`, `stdin`, `_read_stdin`
  sign: a tool run in the background never returns, while the same run in the foreground is instant

- **A message's first tool call can reach PreToolUse before its text reaches the transcript.**
  names: `check_declared`, `transcript_path`, `DECLARE_TRIES`
  sign: the declaration gate refuses a first call whose text plainly opens with the declaration
