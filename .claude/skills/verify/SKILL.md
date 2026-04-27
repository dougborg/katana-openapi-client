---
name: verify
description: >-
  Skeptically validate that implementation is complete and works. Heavier
  than the verifier agent — exercises the feature, checks integration, and
  confirms regression protection.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(uv run poe agent-check)
  - Bash(uv run poe test)
  - Bash(uv run poe test-coverage)
  - Bash(git diff *)
  - Bash(git status)
---

# /verify — Verify Implementation

## PURPOSE

Skeptical end-to-end check: not just "compiles green" but "actually works."

## CRITICAL

- **Be skeptical** — never accept "should work"; prove it.
- **Run real commands, read real files** — claims without evidence are not verified.
- **Don't fix anything** — surface failures; don't quietly patch.

## STANDARD PATH

### 0. Exercise the feature

Before any infrastructure check, **use** what was implemented:

- New MCP tool? Invoke it via the test harness or MCP inspector.
- New API method? Make a test call (or run the matching integration test).
- Bug fix? Reproduce the original failure scenario; confirm it no longer fails.
- Behavior change? Demonstrate before-vs-after.

This catches "compiles but doesn't work" failures the test suite missed.

### 1. Code exists

- All claimed files present (not just planned)
- No stubs, TODOs, or "will do later" gaps
- All imports resolve

### 2. Code works

```bash
uv run poe agent-check    # format + lint + type check
uv run poe test           # tests
```

ALL green, no new warnings.

### 3. Code is complete

- All requirements addressed
- Edge cases handled (empty, error, None/UNSET)
- Error handling uses appropriate exception types

### 4. Code is integrated

For each new public function/class, run `LSP findReferences`. Zero references means something is unfinished — flag it.

### 5. Generated files intact

- `api/**/*.py`, `models/**/*.py`, `client.py` not manually edited
- If client was regenerated, pydantic models also regenerated

### 6. Coverage maintained

```bash
uv run poe test-coverage
```

Core logic ≥87%. New code has both success and error path coverage.

### 7. Regression check

- Confirm step 2 ran the FULL test suite (not a subset)
- No tests deleted or skipped accidentally
- If coverage dropped, identify what lost coverage and why

## OUTPUT

```text
## Verification Report

### Status: [PASS | FAIL]

### Verified
- [item]: [evidence]

### Failed
- [item]: [what's wrong + fix]

### Recommendations
- [improvements noticed]
```

## EDGE CASES

- **Instructions are wrong** — if `CLAUDE.md` or another doc misled the implementation, fix the doc as part of verification. The goal is that future work doesn't repeat this failure.

## RELATED

- `verifier` agent — fast mechanical gate (this skill is the heavier audit)
- `pr-preparer` agent — process readiness (commits, ADRs, help resource sync)
- `code-reviewer` agent — design review (this skill is correctness, not design)
