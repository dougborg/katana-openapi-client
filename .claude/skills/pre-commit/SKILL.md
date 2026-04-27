---
name: pre-commit
description: >-
  Quick pre-flight validation of staged and unstaged changes before
  committing. Lighter than the verifier/code-reviewer agents — focuses on
  catching common mistakes in the current changeset.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(uv run poe agent-check)
  - Bash(uv run poe quick-check)
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
---

# /pre-commit — Pre-Commit Check

## PURPOSE

Fast pre-flight before `git commit` — catches mistakes the editor missed.

## CRITICAL

- **No shortcuts** — never `--no-verify`, `noqa`, or `type: ignore` to make this pass.
- **Generated-file edits are blockers** — any change to `api/**/*.py`, `models/**/*.py`, `client.py` outside of regeneration is wrong.

## STANDARD PATH

### 1. Run Tier 2 validation

```bash
uv run poe agent-check
```

If this fails, stop. Fix and re-run. Don't commit on red.

### 2. Scan the diff for anti-patterns

```bash
git diff
git diff --cached
```

Look for:

- Generated-file edits (`api/**/*.py`, `models/**/*.py`, `client.py`) without spec change
- Anti-patterns from `CLAUDE.md` "Known Pitfalls" and "Anti-Patterns to Avoid"

### 3. Verify test coverage

If new or changed code is in the diff, check that the corresponding test files were also modified or created. Flag any new functions without test coverage.

### 4. Check commit message format

If a message is provided, verify conventional format: `type(scope): description`. Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`, `ci`, `perf`. Valid scopes: `client`, `mcp`, or none.

## OUTPUT

```text
## Pre-Commit Report

### Status: [PASS | FAIL]

### Validation: [PASS/FAIL]
[details if failed]

### Anti-Pattern Scan: [PASS/FAIL]
[findings]

### Test Coverage: [PASS/FAIL]
[uncovered changes]

### Commit Format: [PASS/FAIL]
[issues]
```

## RELATED

- `verifier` agent — heavier final pre-PR gate
- `/review` skill — full branch review (slower)
- `code-modernizer` agent — actively rewrites anti-patterns
