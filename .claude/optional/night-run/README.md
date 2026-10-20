# Optional: the night run

For unattended work: a loop or scheduled task that works through a sheet of steps while you're away,
resumes where it stopped, and leaves a short morning list of what only you can do.

**Enable**
1. Copy `nightlock.py` into `.claude/tools/`, and `NIGHT_RUN.md` into `docs/`. Fill in the steps and the
   morning-list kinds.
2. Add `docs/NIGHT_RUN.md` and `docs/MORNING.md` to the table in CLAUDE.md. A new document needs your yes,
   and this is it.
3. Start it with `/loop` or a scheduled task whose prompt is: *"Follow docs/NIGHT_RUN.md from its STEP line."*
4. Add `"Bash(python .claude/tools/nightlock.py:*)"` to the allow list in `.claude/settings.json`.

Each step's `DONE WHEN:` must be a check a script or command can settle. "Looks right" can't be checked
at night.
