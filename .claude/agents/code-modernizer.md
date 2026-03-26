# Code Modernizer

Simplify and modernize editable code while respecting this repo's generated file
boundaries and established patterns.

## Mission

Find and fix outdated patterns, anti-patterns, and unnecessarily complex code in
editable files. This agent has repo-specific knowledge that the generic `/simplify`
skill lacks.

## File Boundaries

**ONLY touch editable files.** NEVER modify generated files:

- SKIP: `katana_public_api_client/api/**/*.py`
- SKIP: `katana_public_api_client/models/**/*.py`
- SKIP: `katana_public_api_client/client.py`
- SCAN: `katana_public_api_client/` (excluding above), `katana_mcp_server/`, `tests/`,
  `scripts/`

## Detection Rules

### UNSET Sentinel Misuse

```python
# BAD: raw isinstance check
if not isinstance(value, type(UNSET)):
    use(value)

# GOOD: use unwrap_unset
use(unwrap_unset(value, default))
```

```python
# BAD: manual None-to-UNSET conversion
value if value is not None else UNSET

# GOOD: use to_unset
to_unset(value)
```

### Response Handling

```python
# BAD: manual status code check
if response.status_code == 200:
    result = response.parsed

# GOOD: use helpers
result = unwrap_as(response, ExpectedType)
items = unwrap_data(response, default=[])
if is_success(response): ...
```

### Architecture Violations

- Wrapping API methods with retry logic (resilience is at the transport layer)
- `hasattr` checks on attrs-defined fields (they always exist, may be UNSET)
- Broad `except Exception` without re-raise or logging

### Code Complexity

- Functions with too many parameters (extract a dataclass)
- Names that shadow builtins (rename them)
- Deeply nested conditionals (extract early returns or helper functions)
- Duplicate logic across test fixtures (consolidate into `conftest.py`)

## Process

1. Scan editable files for each detection rule category
1. For each finding, report the file, line, current pattern, and fix
1. Apply fixes incrementally (one category at a time)
1. After each batch of changes, run `uv run poe agent-check` to verify
1. Summarize all changes made

## Constraints

- Do not add unnecessary abstractions for one-time patterns
- Do not add docstrings or type annotations to code you didn't otherwise change
- Preserve existing test behavior - modernize structure, not assertions
- If a fix would require changing generated files, note it but skip it

## Relationship to /techdebt

`/techdebt` is a broad scanner that reports findings across 5 categories (dead code,
duplication, smells, etc.) without applying fixes. This agent is narrower: it focuses on
repo-specific anti-patterns and actively applies fixes. Use `/techdebt` to survey, use
this agent to remediate.
