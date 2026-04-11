# Write Tests

Write comprehensive tests for the specified code. If no target is specified, identify
untested or under-tested code and write tests for it.

## Test Structure

### Naming Convention

```
test_<what>_<condition>_<expected>
```

Examples:

- `test_unwrap_as_with_200_response_returns_parsed_model`
- `test_unwrap_as_with_401_response_raises_authentication_error`
- `test_pagination_with_empty_response_returns_empty_list`

### AAA Pattern (Arrange, Act, Assert)

Every test follows this structure:

```python
def test_example():
    # Arrange - set up test data and conditions
    client = KatanaClient(api_key="test-key")
    expected = "result"

    # Act - execute the code under test
    result = client.do_something()

    # Assert - verify the outcome
    assert result == expected
```

## Edge Case Checklist

For every function being tested, consider ALL of these:

- **Empty inputs**: empty strings, empty lists, empty dicts, zero
- **Boundary values**: off-by-one, max/min values, exactly-at-limit
- **Invalid inputs**: wrong types, malformed data, negative numbers
- **None/UNSET handling**: None where a value is expected, UNSET fields
- **Error conditions**: network failures, API errors (401, 404, 422, 429, 500)
- **Concurrent access**: race conditions in async code (if applicable)

## Project Test Infrastructure

Use `httpx.MockTransport` with fixtures from `conftest.py` for HTTP mocking,
`unittest.mock` for non-HTTP. See CLAUDE.md for test commands and coverage targets (87%+
core).

Use `@pytest.mark.parametrize` when testing the same logic with multiple inputs.

## Process

1. Identify the target code. Use `LSP documentSymbol` on the target file to get the full
   list of functions/classes + line numbers without reading the whole file, then
   `LSP hover` on each one to get its signature, type hints, and docstring.
1. For each function, use `LSP findReferences` to see existing callers — real-world call
   sites often reveal the intended contract and edge cases the docstring omits.
1. Enumerate test cases using the edge case checklist
1. Write tests following the naming convention and AAA pattern
1. Run `uv run poe test` to verify all tests pass
1. Run `uv run poe test-coverage` to check coverage meets targets
1. Fix any failures - NEVER skip or ignore test failures

## Anti-Patterns to Avoid

- Testing implementation details instead of behavior
- Overly coupled tests that break when internals change
- Missing error path coverage (only testing happy path)
- Flaky tests depending on timing or external state
- Asserting too many things in one test (split into focused tests)

## Self-Improvement

If writing tests reveals surprising API behavior, undocumented edge cases, or confusing
interfaces, update CLAUDE.md's "Known Pitfalls" section. Tests are often the first place
you discover things the docs don't cover.
