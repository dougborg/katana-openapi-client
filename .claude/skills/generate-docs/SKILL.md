---
name: generate-docs
description: >-
  Generate or update docstrings, ADRs, README sections, cookbook recipes, or
  user guides following Katana's documentation standards.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(uv run poe format)
  - Bash(uv run poe docs-build)
  - Bash(ls docs/adr/*)
---

# /generate-docs — Generate Documentation

## PURPOSE

Write or update docs (docstrings, ADRs, README, cookbook, guides) using project standards.

## CRITICAL

- **Only document the public surface** — don't add docstrings or comments to code you didn't otherwise change.
- **Code examples must be tested** — never write usage examples that haven't actually run.
- **ADRs are sequential** — find the next number; never reuse.

## STANDARD PATH

### 1. Pick the doc type

| Type | Goes In | When |
| --- | --- | --- |
| Docstring (Google style) | inline | public functions/classes/modules |
| ADR | `docs/adr/NNNN-*.md` | architectural decision |
| README section | the relevant `README.md` | new package or major feature |
| Cookbook recipe | `docs/COOKBOOK.md` | new usage pattern |
| User guide | `docs/*.md` | complex feature needing step-by-step |

### 2. Docstrings (Google style)

```python
def unwrap_as(response: Response, expected_type: type[T]) -> T:
    """Extract and validate a parsed response as the expected type.

    Args:
        response: The HTTP response to unwrap.
        expected_type: The type to validate the parsed response against.

    Returns:
        The parsed response cast to the expected type.

    Raises:
        AuthenticationError: If 401.
        ValidationError: If 422.
        APIError: For other non-success status codes.
    """
```

### 3. ADRs

```bash
ls docs/adr/*.md | grep -o '[0-9]\{4\}' | sort -n | tail -1
```

Increment, copy `docs/adr/template.md`, fill in. Update `docs/adr/README.md` index.

### 4. Format

```bash
uv run poe format
```

88 char line length, ATX headers (`#`, not `===`).

If updating MkDocs content:

```bash
uv run poe docs-build
```

## EDGE CASES

- **Existing doc is wrong** — fix it as part of the work. Don't leave bad docs next to new ones.
- **Adding cookbook recipe** — every code block must be runnable; mention required imports and config.

## RELATED

- `harness-kit:documentation-writer` skill — generic progressive-disclosure doc style
- `/review` skill — flags missing or outdated docstrings
- `CLAUDE.md` "Detailed Documentation" — canonical project doc map
