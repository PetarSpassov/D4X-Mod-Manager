# The night run

A STEP is `- **N — TITLE.**`, what to do, and `DONE WHEN:`, in 6 lines at most. A step that passes is
DELETED, not struck. Findings go to `GOTCHAS.md`, what changed goes to `HANDOFF.md`.

## The state: the only line that moves

    STEP: 1

## The steps

- **1 — <TITLE>.** <what to do>.
  `DONE WHEN:` <a check anyone can run, with the result it must give>.

- **2 — END.** Reached only from a met `DONE WHEN` on the step before. Write `docs/MORNING.md`, stop the
  loop, and say what every step proved and what it did not.

## The morning list: `docs/MORNING.md`, and the ONLY things that wait for the user

- **Only these kinds:** <e.g. a manual test only they can run; a call that is theirs to make>. Each carries
  `KIND:` and `TRIED:`.
- Everything else is the run's own work: a design fork, a missing tool, an unclear `DONE WHEN`, a fault.
  Take the reading this sheet implies, file it as `DECIDED FOR YOU:` with how to undo it, and carry on.
  Three tries without progress means a new approach, never a parked step.

## Rules that apply at night

- Take the lock first: `python .claude/tools/nightlock.py take`. `HELD` means end this run now. Take it
  again before each long step, and release it at END.
- Usage limits are not the run's to manage. A tick that a limit cuts off just ends; the next one resumes
  at `STEP`.
- On a loop tick with no step done, send nothing. `Step N success` only after a met `DONE WHEN`.
- Nothing is called good. The user does that, in their own words, on waking.
- Every step ends with what it proved AND what it did not.
- A prior failure is a cause to answer, not prior art to cite.
