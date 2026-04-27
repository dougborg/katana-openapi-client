---
name: write-tests
description: >-
  Write comprehensive tests using project conventions: AAA pattern, edge-case
  checklist, httpx.MockTransport, conftest fixtures, parametrize where it
  reads better than copy-paste.
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash(uv run poe test)
  - Bash(uv run poe test-coverage)
  - Bash(uv run poe quick-check)
---

# /write-tests — Write Tests

## PURPOSE

Add or extend test coverage following Katana's conventions and 87% core threshold.

## CRITICAL

- **Test behavior, not implementation** — refactors must not break unrelated tests.
- **Cover error paths** — happy-path-only is a blocker.
- **Mock list responses with the `data` envelope** — Katana wraps every list as `{"data": [...]}`. Raw arrays in mocks don't match production shape.
- **No skipped tests** — never `@pytest.mark.skip` to make CI green.

## STANDARD PATH

### 1. Identify the target

Use `LSP documentSymbol` on the target file to list functions/classes + line numbers without reading the whole file. Then `LSP hover` on each to get signatures, types, and docstrings.

### 2. Map the contract

For each function, run `LSP findReferences` to see real callers. Call sites often reveal intended contracts and edge cases the docstring omits.

### 3. Enumerate test cases

For every function, walk this checklist:

- **Empty inputs** — empty strings, lists, dicts, zero
- **Boundary values** — off-by-one, max/min, exactly-at-limit
- **Invalid inputs** — wrong types, malformed data, negatives where positive expected
- **None / UNSET** — None where a value is expected; UNSET attrs fields
- **Error conditions** — network failures, API errors (401, 404, 422, 429, 500)
- **Concurrency** — race conditions in async code where applicable

### 4. Write tests

Naming: `test_<what>_<condition>_<expected>`

```python
def test_unwrap_as_with_401_response_raises_authentication_error():
    # Arrange
    response = mock_response(status=401, content=b'{"error":"unauthorized"}')

    # Act + Assert
    with pytest.raises(AuthenticationError):
        unwrap_as(response, ManufacturingOrder)
```

Use `@pytest.mark.parametrize` when the same logic is tested with multiple inputs.

### 5. Use project test infrastructure

- `httpx.MockTransport` from `conftest.py` for HTTP mocking
- `unittest.mock` for non-HTTP mocking
- Mock list responses with `{"data": [...]}` envelope
- See `katana_public_api_client/utils.py` for `unwrap_*` helpers

### 6. Run and verify

```bash
uv run poe test
uv run poe test-coverage
```

Core logic must be ≥87%. Fix any failures — never skip.

## EDGE CASES

- **Surprising API behavior discovered** — update `CLAUDE.md` Known Pitfalls. Tests are often where you first find what docs don't cover.
- **Test infrastructure feels missing** — propose adding a fixture to `conftest.py` rather than copy-pasting setup across tests.

## RELATED

- `code-reviewer` agent — flags missing coverage in PR review
- `/review` skill — full branch review including test coverage
- `verifier` agent — confirms tests pass before PR
