---
name: techdebt
description: >-
  Scan editable code for tech debt, anti-patterns, and improvement
  opportunities across 5 categories. Reports findings; the code-modernizer
  agent applies fixes.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(uv run poe quick-check)
---

# /techdebt — Tech Debt Scanner

## PURPOSE

Surface tech debt and anti-patterns in editable code; do not fix.

## CRITICAL

- **Skip generated files** — never flag or modify `api/**/*.py`, `models/**/*.py`, `client.py`.
- **Confirm dead code with LSP** — `grep` misses dynamic dispatch and re-exports; use `LSP findReferences` before declaring something dead.

## STANDARD PATH

### 1. Run lint baseline

```bash
uv run poe quick-check
```

### 2. Scan editable files by category

Categories:

1. **Dead code** — unused imports/vars/functions/classes; unreachable paths; commented-out blocks. Confirm with `LSP findReferences` before flagging.
2. **Outdated patterns** — anti-patterns from `CLAUDE.md` Known Pitfalls / Anti-Patterns sections (UNSET misuse, manual status checks, retry wrapping, hasattr on attrs models, raw list mocks).
3. **Code duplication** — repeated logic that should be a helper, copy-pasted test setup that should be a fixture.
4. **Code smells** — broad `except Exception`, missing type annotations on public functions, parameter explosions, name shadowing, circular imports.
5. **Missing best practices** — public functions without docstrings, async tests missing `@pytest.mark.asyncio`, fixtures that should be `scope="session"`.

### 3. Report each finding

```text
**File**: path/to/file.py:42
**Category**: outdated pattern
**Current**: if not isinstance(value, type(UNSET)): use(value)
**Fix**: use(unwrap_unset(value, default))
**Priority**: HIGH | MEDIUM | LOW
```

### 4. Output

```text
## Tech Debt Report

### Summary
- Dead code: N
- Outdated patterns: N
- Code duplication: N
- Code smells: N
- Missing best practices: N

### HIGH | MEDIUM | LOW
[grouped findings]

### Improvements to CLAUDE.md
[new anti-patterns discovered]
```

This skill is **report-only**. To apply fixes, run `harness-kit:simplify` for generic
cleanup, then spawn the `code-modernizer` agent for Katana-specific rewrites.

## EDGE CASES

- **Dead code candidate has zero `git grep` hits** — still run `LSP findReferences`. Pyright walks the real type graph including `from m import *` and aliased re-exports.
- **Recurring anti-pattern not in CLAUDE.md** — recommend adding it to "Known Pitfalls" so future scans catch it earlier.

## RELATED

- `code-modernizer` agent — actively rewrites the patterns this skill flags
- `harness-kit:simplify` skill — generic cleanup (run before code-modernizer)
- `/review` skill — design review (broader than tech debt)
