# Tech Debt Scanner

Scan the codebase for tech debt, anti-patterns, and improvement opportunities.

## Scope

Only scan **editable** files. NEVER flag or modify generated files:

- SKIP (generated): `katana_public_api_client/api/**/*.py`,
  `katana_public_api_client/models/**/*.py`, `katana_public_api_client/client.py`
- SCAN: `katana_public_api_client/` (excluding generated paths above),
  `katana_mcp_server/`, `tests/`, `scripts/`

## Categories to Check

### 1. Dead Code

- Unused imports, variables, functions, classes
- Unreachable code paths
- Commented-out code blocks

For candidate unused functions/classes, use `LSP findReferences` on the symbol
definition to confirm zero usages before flagging. Pyright walks the real import graph
(including `from module import *` and aliased re-exports) that a plain `Grep` can miss,
so LSP is the authoritative check. If there are no references outside the definition
itself, the symbol is dead and safe to remove.

### 2. Outdated Patterns (Project-Specific)

Flag anti-patterns from CLAUDE.md's "Known Pitfalls" and "Anti-Patterns to Avoid"
sections.

### 3. Code Duplication

- Repeated logic that should be extracted into helpers
- Copy-pasted test setup that should be fixtures
- Duplicate error handling patterns

### 4. Code Smells

- Overly broad exception handling (`except Exception`)
- Missing type annotations on public functions
- Issues listed in CLAUDE.md's "Proper fixes" section (parameter count, shadowing,
  circular imports)

### 5. Missing Best Practices

- Public functions without docstrings
- Tests without descriptive names
- Missing `@pytest.mark.asyncio` on async tests
- Fixtures that should use `@pytest.fixture(scope="session")`

## Process

1. Run `uv run poe quick-check` to get current lint status
1. Scan editable files category by category
1. For each finding, report:
   - **File and line**: exact location
   - **Category**: which of the 5 categories above
   - **Current code**: the problematic pattern
   - **Suggested fix**: concrete replacement
   - **Priority**: HIGH (breaks conventions), MEDIUM (code quality), LOW (nice to have)
1. Run `uv run poe fix` to auto-fix what's possible
1. Summarize findings by category with counts

## Output Format

```
## Tech Debt Report

### Summary
- Dead code: N findings
- Outdated patterns: N findings
- Code duplication: N findings
- Code smells: N findings
- Missing best practices: N findings

### HIGH Priority
[findings...]

### MEDIUM Priority
[findings...]

### LOW Priority
[findings...]

### Improvements to CLAUDE.md
[Any new anti-patterns or pitfalls discovered that should be added]
```

## Self-Improvement

If this scan reveals a recurring anti-pattern not already documented in CLAUDE.md's
"Known Pitfalls" or "Anti-Patterns to Avoid" sections, add it there so future sessions
can catch it earlier.
