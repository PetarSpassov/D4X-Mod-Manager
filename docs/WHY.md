# Why each rule exists

Read one with `python .claude/tools/why.py <N>`, and only when tempted to break the rule. These reasons
come from a long project where each rule was written after the failure it names.

## WHY 0 — re-read what the user says changed
Working from a remembered or cached version of a file the user has just edited produces confident
answers about a file that no longer exists. Saying what you found makes a stale read visible at once.

## WHY 1 — scope
Unasked "while I'm here" work is the most common way a turn goes wrong: it costs review time, hides the
change that was asked for, and is often undone. Re-proposing what the user already did reads as not
listening. A fix stalled on a question the code could settle wastes a round trip; taking a stated
direction can be redirected cheaply.

## WHY 2 — you don't close
A green test proves one case: one input, one path, one configuration. Calling the item done from it
repeatedly let untested neighbours ship broken. Naming the untested cases alongside the pass is what
lets the user decide, cheaply, what else they want covered.
Leaving every case to the user went too far the other way: a hook's own output, seen in Claude's context,
sat on the Untested list waiting for a confirmation that added nothing. A case closed with its evidence
quoted can be checked; a whole item called done from one case cannot.

## WHY 3 — reply shape
The user reads the result, not the process. Long replies bury the one line that matters, and narrating
tool calls repeats what the transcript already shows. A fixed shape makes the reply scannable.
The opening `Answer turn.` / `Change turn.` line exists because the user had to dig through commands to
see what a turn was doing. Stated first, a question misread as an order shows up before any file changes.
The gate enforces the declaration, not the user's wording: CodeCracker tried to tell orders from questions
with word lists, and it refused a plain "Go." and took "make it X" (a rename) as an order to build. Claude
reads the message, the user sees the declaration, and the hook only holds Claude to what it declared.
That still let Claude declare change turns off questions and complaints, so a change turn now also needs
the message to start with "Go". A go-word list was tried first and misread "Please link…" and "Confirm
the cause and fix it"; a model classifier can't see the last reply from a hook. A fixed signal can't be
misread, and a forgotten one costs one "Go"; a change nobody asked for costs a revert.
The line itself was marked (G) while only the plan record was checked, and Claude skipped it in two
change turns. The gate now reads the turn's text from the transcript before every tool call.
Mid-turn lines were once allowed for findings only, and Claude still posted one per step, mostly
announcing the next action. The user banned them outright: the reply carries everything, and
postgate names each one the moment it lands, so sending one costs more than it says.
"Short by default" was prose only, and replies kept running long. A character count is mechanical. The
Stop hook can't take back a post the user has seen: sending it back for a short version made the user
read every long reply twice. So the cap is shown at every turn start, and an overage is noted for the
next one. Only prose counts, because a command or a table is never the padding.

## WHY 4 — evidence checks
Judgement rules get read once and lost to momentum a hundred tool calls later; these are mechanical
checks at the moment of a claim. Each was a repeat failure: "it doesn't exist" from a `head -20` of a
search; describing a function from its name; inference written in the same voice as verified fact, which
removes the user's ability to catch it.

## WHY 5 — debugging
An experiment that changes several things gives a result nobody can attribute. Three failed tries in
the same direction is the reliable sign the model of the problem is wrong, not the details of the
attempt. A premise found false stays false everywhere it was written, so fix every copy at once.

## WHY 6 — hand off only what only the user can do
Handing the user a command to run, an edit to make or a build to start spends their time on work the
assistant can do, and puts a round trip in the middle of the task.

## WHY 7 — reading costs
Everything a tool returns is carried by every later call in the conversation. One whole read of a big
generated file cost half a session. A bounded turn that stops and says what is missing is cheaper than
an unbounded one that runs out of room mid-task.

## WHY 8 — files
Shell edits (`sed -i`, redirects) leave no reviewable diff and fail silently on quoting. Output dropped
wherever was convenient becomes a mess that someone must sweep by hand, every time; fixing the
generator fixes it once. A deleted file can't be recovered; one in `todelete/` can.

## WHY 9 — a reported result updates the docs first
An end-of-session checklist to "keep the docs current" failed: a list read once at session start is not
re-checked per result. The same duty bound to an event that actually happens works. Writing a verdict
in the turn a symptom arrives turned several real faults into "expected behaviour".

## WHY 10 — traps are written down
A lesson that lives only in a conversation is relearned at full price. A trap ledger that is read whole
grows until nobody reads it, so traps are retrieved by subject, and the hooks push one back when a call
touches what it names.

## WHY 11 — the `.` hand-back
The promise is that /clear is safe at any point: clear, type `.`, and the last post is back on screen
exactly as it was, with nothing re-derived. It keys on the user's `.` and not on detecting a clear,
because the session's start reason proved unreliable: the quote fired after restarts and compactions,
and missed some real clears. A post handed back twice is a post the user has read twice, so each is
handed back once.

## WHY 12 — writing code
Unchecked generation piles up second copies, dead code, speculative options and untested changes until
the codebase can't be changed safely. The named practices are standard, so there is nothing to invent.
The Boy Scout rule is left out on purpose: it contradicts 1a. Limits flag rather than force a split,
because splitting a deep module to meet a number makes it worse. Comments that tell history, quote the
user or shout were seen in a real project: they rot, and the commit log already holds that story.
A flag alone was not enough: CodeCracker's flagged files kept growing, one to 1,218 lines. So past 800
a code file may only shrink, and 400 matches 7b, so any file within the limit is one cheap read.
Folders by feature keep one change in one place; a `utils/` drawer is where unrelated code collects.

## WHY D — one home per fact
"Which version is good" was once recorded in several places, and they disagreed. Once it had exactly one
home it never drifted again. Every extra document is one more place for a fact to go stale.
HANDOFF once kept a Log too. It repeated git, and HANDOFF went five commits without an update because
nothing but memory moved it. So the Log went, and the update is now tied to the commit itself.

## Adding a rule
Write it as prose in CLAUDE.md first, with a WHY entry. Promote it to a hook only after it has failed
more than once despite being written down, and add the hook's case to `selftest.py` in the same change.
A guard that cries wolf gets ignored, and guards that parse the user's English are brittle, so keep each
one narrow.
