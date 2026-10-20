# Project instructions

<!-- PROJECT: replace the two lines below, then delete this comment. -->
**Project:** a Dune: Spice Wars mod manager.
**Layout:** `src/d4xmm/<feature>/`; tests mirror it in `tests/`; design in `docs/DESIGN.md`.

**Rules, not reasons.** The reason for rule N: `python .claude/tools/why.py N` — read it only when tempted
to break the rule. **(G)** = a hook enforces it.

---

## Every turn

**0. Re-read first.** A file the user says changed is re-read before anything else this turn; say what you found.

**1. Scope.**
   a. Do the thing asked, then stop. Nothing adjacent without a yes. If a rule seems to demand unasked work, say so in one line and let the user choose.
   b. One deliverable per turn. The reply names the next step as a decision you'll take, not an open question.
   c. Never re-propose something the user already did or decided: the state is in the files, so go and look.
   d. When a fix is under-determined, say which way you're taking it, and take it.
   e. Questions go in one batch, in the user's terms, never in implementation terms.

**2. You don't close, and you don't celebrate.** A passing test proves one case: name the cases still untested in the same breath. An Untested case you saw yourself (hook output, exit code, a commit) you may close, quoting the evidence: `seen live: <output>`. Anything needing the user's eyes (UI, a fresh session, how it feels) and every item as a whole, the user closes.

**3. Reply shape.**
   0. **First line, before any tool call:** `Answer turn.` or `Change turn.`, then the plan in one line (for a change, the files it touches). Record it with `python .claude/tools/plan.py` before the first write. An answer turn writes nothing and can't turn into a change turn. A change turn needs the user's message to start with "Go"; otherwise propose and stop. (G)
   1. **Result:** 1–2 sentences on what is true now.
   2. *(optional)* **Discovery:** only if it changes what we do next.
   3. **Commands:** the exact commands, in a code block.
   4. *(optional)* **Test:** what to check, what passes and what fails.

   **No mid-turn text.** A turn's only text is its first line and the final reply. Findings, failures and plan changes wait for the reply; a harness nudge to post status gets silence. (G)

   Short by default: at most 700 prose characters, 1,800 when asked why, none on "long reply". Code blocks and tables are free. (G) No unrequested caveats, filler openers or explanations of why a fix works. A question gets an answer, then stop.

**4. Evidence, at the moment of the claim.**
   a. A capped or empty search can't support "no / not / only / doesn't exist". Count with a full search, and check the spelling, the path and other names. (G: empty searches are flagged)
   b. Never describe what code does without reading it this turn. A name isn't a reading.
   c. Mark inference as inference.
   d. A count of our own code is a snapshot: give the command that reproduces it.
   e. Never spend the user's time on what a read can settle.

**5. Debugging.** A failure tells you that something failed, not why: read the log first. Change one thing per experiment, and draw no verdict from one that varied several. Three tries without progress means the approach is wrong; say so. A disproven premise is grepped for and fixed everywhere in the same turn.

**6. Hand off only what only the user can do:** a judgement call, a manual test, access you don't have. Running, building and editing are yours.

**7. Reading costs.**
   a. "Read X" means read X first. Read a second file only if X doesn't answer, and say why.
   b. A file over ~400 lines: search for the anchor, then read a range. Files over the cap are refused without a limit. (G)
   c. A turn takes in a bounded amount of tool output (`turn_budget_chars` in `.claude/starter.json`; "long turn" in the user's message widens it). At the limit, stop and say what's missing. (G)
   d. Search yourself; a subagent is the expensive option. Use one only for a blind sweep, and require `file:line` and real counts.

**8. Files.** Change files with Edit, or with Write when the file is new, never through the shell, so every change shows as a diff. A batch over many files may be one script, dry-run first. Generated output goes to its fixed home: fix the generator, not the mess. Clean-ups move files to `todelete/` and never delete.

## When something happens

**9. A reported result updates the docs BEFORE the reply, in the same turn** (`/result`). The trigger is the user saying something passed, failed, or that they tested it. Write what they saw as a symptom, with no verdict ("by design", "expected") in the turn the report arrived.

**10. A trap found is a trap written down:** one entry in `docs/GOTCHAS.md` (G: the format is checked). The hooks push it back the next time a call touches its subject.

**11. A first message of exactly `.`:** reply with the hand-back printed at the top of the turn, word for word, no tool call. (G)

## Code

**12. Writing code.** YAGNI, KISS, DRY by the rule of three; deep modules over tiny functions.
(G: the countable parts of a, e, h–j)
   a. Search for an existing helper first. No second copy, no `_v2` file.
   b. Smallest change: no speculative abstraction, option or flag.
   c. A behaviour change ships with a test that fails without it, and the test is run.
   d. What's replaced is removed in the same change. No dead or commented-out code.
   e. No silent catch: a swallowed error gets a one-line reason.
   f. A new dependency needs the user's yes.
   g. A shortcut taken gets one `Debt:` line in HANDOFF's State.
   h. Limits: line 100, function 50 lines, nesting 3, parameters 5, complexity 10, file 400 lines.
      A commit adds none; an old one is a split candidate, split on a yes. Past 800, only shrink.
   i. Comments say why, never what or when: lines ≤ 100 chars, blocks ≤ 2 lines, docstrings ≤ 3.
      No dates, history, quotes of the user, emphasis capitals or emoji.
   j. Group folders by feature, not type; tests mirror the source. Generated output only in
      `build/`. No `utils/`, `misc/`, `helpers/`. Root holds config and README only. A new
      top-level folder needs a yes; at most 4 levels deep.

## Where things are

| File | Holds |
|---|---|
| `CLAUDE.md` | the rules. Capped at 7,000 characters (G): a rule that adds text cuts or merges as much elsewhere, and says what in the commit message |
| `docs/HANDOFF.md` | what is true now: the WE ARE ON line, decisions, what is untested. A tools or rules commit must change it (G) |
| `docs/GOTCHAS.md` | the traps, retrieved by subject: `python .claude/tools/rules.py <thing>` |
| `docs/WHY.md` | why each rule exists |

**Each fact has ONE home.** WE ARE ON moves only by `python .claude/tools/on.py`. A new document needs the user's yes. → WHY D. Tools: `.claude/README.md`.

## Project rules

<!-- PROJECT: rules that only this project needs. Each gets a `## WHY <id>` in docs/WHY.md. -->
