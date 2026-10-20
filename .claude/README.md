# ClaudeStarter

A starting point for any project worked on with Claude Code. It carries over the practices that held up
in a long Claude project. They aren't about any particular codebase; they're about keeping Claude
oriented, honest and cheap across many sessions.

## Start a new project from it

1. Copy this folder, leaving out `.git/` and `.claude/state/` if it exists. On Windows, double-click
   `.claude/tools/newproject.bat`: it asks for the target folder and never overwrites a file there.
2. In `CLAUDE.md`, fill in the **Project** and **Layout** lines. Add rules only this project needs under
   *Project rules*, each with a `## WHY <id>` in `docs/WHY.md`.
3. Tune `.claude/starter.json`: the read cap, the never-read patterns (lock files, generated output,
   data dumps) and the per-turn budget.
4. `git init`. The first session points git at `.githooks/`, so commits run `doccheck.py`.
5. Run `python .claude/tools/selftest.py`, then start a session. The first thing Claude sees is the
   `=== PROJECT STATE ===` briefing.

On macOS or Linux, replace `python` with `python3` in `.claude/settings.json` and `.githooks/pre-commit`
if `python` isn't on the PATH.

## What's in it

| Piece | What it does |
|---|---|
| `CLAUDE.md` | Rules, not reasons: scope, reply shape, evidence checks, debugging, reading costs, files |
| `docs/WHY.md` | Why each rule exists. Read on demand with `why.py N` |
| `docs/HANDOFF.md` | What is true now: the **WE ARE ON** line, **LAST KNOWN GOOD**, standing decisions, what is untested. Pre-commit refuses a tools or rules change that leaves it alone; the briefing shows how many commits ago WE ARE ON moved |
| `docs/GOTCHAS.md` | Traps in a three-line format (title, `names:`, `sign:`), retrieved by subject |
| `/state`, `/result` skills | Orient after a /clear; record a reported test result before replying |

**Hooks** (`.claude/tools/`, wired in `.claude/settings.json`):

| Hook | Script | Does |
|---|---|---|
| SessionStart | `briefing.py` | Prints the HANDOFF state, an owed check, doc health and the recent turns |
| UserPromptSubmit | `turnstart.py` | Opens the turn: records the message, zeroes the counters, pushes the `.` hand-back, shows the reply cap, and on a "Go" turn the task-list reminder |
| PreToolUse | `pregate.py` | Refuses any call before the turn's `Answer turn.` / `Change turn.` line, whole reads of huge or never-read files, reads past the turn budget, any tool during a hand-back, project writes the turn's plan doesn't cover (none at all in an answer turn), and a code file growing past 800 lines |
| PostToolUse | `postgate.py` | Counts tool output, flags empty searches, records writes, pushes traps a call touches |
| Stop | `journal.py` | One journal entry per turn, so a `/clear` never loses what was just agreed; notes an over-cap reply for the next turn (`replycap.py`). It never blocks or sends a reply back |

**The `.` hand-back:** after a `/clear`, type `.` as the first message, and the reply is the last post
from before the clear, word for word (`handback.py`). Each post is handed back once.

**Tools:**

| Command | Does |
|---|---|
| `plan.py --answer "<what>"` | declares an answer turn: no writes |
| `plan.py "<doing>" --touch <files> --leave "<what>"` | declares a change turn, only when the message starts with "Go"; `--widen <file> "<why>"` adds a file. `plan_required` in `starter.json` switches the gate off |
| `rules.py <thing>` · `--index` | the traps about a thing |
| `on.py` | moves WE ARE ON |
| `why.py N` | the reason for rule N |
| `prevconvo.py` | the conversation before a /clear |
| `journal.py` | the recent turns |
| `doccheck.py` | are the docs consistent, and is `CLAUDE.md` under `claude_md_cap_chars` (7,000)? Pre-commit runs it |
| `noask.py` | PreToolUse hook: refuses question popups and a wrap-up question box unless the message says `questions_phrase` ("questions are allowed"); fails closed |
| `codecheck.py [files]` | rule 12's countable limits (`code_limits`, `banned_folders`). Pre-commit refuses only what a commit adds; with no arguments it lists every violation |
| `selftest.py` | run after any edit to a hook; runs the cases in `tests/`, one file per tool, in order |
| `handback.py` | shared by the three hooks above |

Per-session state lives in `.claude/state/sessions/<id>/`, so two sessions in one folder never trip over
each other's markers. Every hook but `noask.py` fails open: a broken guard must not stop work.

## Optional add-ons (`.claude/optional/`)

Each has a README that says how to switch it on.

* **coverage**: the user declares an item's test axes, and "done" becomes a count of unproven cases.
* **night-run**: a step sheet, a lock and a morning list for unattended `/loop` or scheduled runs.

## Growing it

Write a new rule as prose first. Promote it to a hook only after it has failed more than once despite
being written down, and add its case to `tests/` in the same change. Keep each guard narrow.
Guards that try to parse the user's English, or that exist to fix other guards, are the sign the set
has grown past what it buys.
