# Pre-Commit Check

Quick pre-flight validation of staged and unstaged changes before committing. Lighter
than `/review` (which reviews the whole branch) - this focuses on catching common
mistakes in the current changeset.

## Process

### 1. Run Tier 2 Validation

```bash
uv run poe agent-check
```

If this fails, report the failures and stop. Fix before committing.

### 2. Scan the Diff for Anti-Patterns

Review the output of `git diff` and `git diff --cached` for:

- **Generated file modifications**: any changes to `api/**/*.py`, `models/**/*.py`, or
  `client.py` that didn't come from regeneration
- Anti-patterns listed in CLAUDE.md's "Known Pitfalls" and "Anti-Patterns to Avoid"
  sections

### 3. Verify Test Coverage

If new or changed code is in the diff:

- Check that corresponding test files were also modified or created
- Flag any new functions without test coverage

### 4. Check Commit Message Format

If a commit message is provided or can be inferred, verify it follows:

- Conventional commit format: `type(scope): description`
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`,
  `ci`, `perf`
- Valid scopes: `client`, `mcp`, or none for cross-cutting changes

## Output Format

```
## Pre-Commit Report

### Status: [PASS | FAIL]

### Validation: [PASS/FAIL]
[Details if failed]

### Anti-Pattern Scan: [PASS/FAIL]
[List of findings, if any]

### Test Coverage: [PASS/FAIL]
[Uncovered changes, if any]

### Commit Format: [PASS/FAIL]
[Issues with message format, if any]
```

## Key Principle

This check should be fast. If it passes, you can commit with confidence. If it fails,
fix the issues first - never use `--no-verify`.
