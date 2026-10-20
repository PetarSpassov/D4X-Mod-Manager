# Optional: coverage

For projects where testing is manual and "it works" quietly means "one case worked". The user declares
an item's axes, and every combination is a case. "Done" becomes a count of unproven cases, and the
session briefing prints that count for every unfinished item.

**Enable**
1. Copy `coverage.py` into `.claude/tools/`. The briefing picks it up by itself.
2. Add to CLAUDE.md, under Project rules:
   `**C1. An item's axes are declared by the user** (coverage.py <item> --axes ...); a reported pass is recorded with --prove, and the reply names the cases still unproven.`
3. In `.claude/skills/result/SKILL.md`, add a step: record the case with `--prove` or `--fail`, and put
   the unproven cases in the reply.

The record lives in `docs/coverage.json` and is committed.
