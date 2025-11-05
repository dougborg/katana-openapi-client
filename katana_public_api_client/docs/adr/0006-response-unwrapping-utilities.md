# ADR-006: Use Utility Functions for Response Unwrapping

## Status

Accepted

Date: 2024-10-17

## Context

The generated API returns `Response[T]` objects with the structure:

```python
response = Response(
    status_code=200,
    content=b"...",
    headers={...},
    parsed=ProductListResponse(data=[...])  # or ErrorResponse
)
```

Users need to:

1. Check if the response was successful
1. Extract the parsed data
1. Handle different response types (success vs error)
1. Deal with nested `.data` fields in list responses
1. Get proper type hints

Common user code patterns were verbose:

```python
response = await get_all_products.asyncio_detailed(client=client)
if response.status_code == 200:
    if isinstance(response.parsed, ProductListResponse):
        products = response.parsed.data
        # Use products
```

This creates boilerplate and reduces code clarity.

## Decision

We will provide **utility functions** for common response operations in `utils.py`:

### Core Utilities

```python
# Extract parsed data with automatic error handling
def unwrap(response: Response[T], *, raise_on_error: bool = True) -> T:
    """Unwrap response and return parsed data or raise typed exception."""

# Extract .data field from list responses
@overload
def unwrap_data(response, *, raise_on_error: bool = True) -> list[Any]: ...
@overload
def unwrap_data(response, *, raise_on_error: bool = False) -> Optional[list[Any]]: ...

# Status checking
def is_success(response: Response[Any]) -> bool: ...
def is_error(response: Response[Any]) -> bool: ...

# Error message extraction
def get_error_message(response: Response[Any]) -> str | None: ...

# Custom handling
def handle_response(
    response: Response[T],
    *,
    on_success: Callable[[T], Any] | None = None,
    on_error: Callable[[ErrorResponse], Any] | None = None,
    raise_on_error: bool = True
) -> Any: ...
```

### Typed Exceptions

```python
class APIError(Exception): ...
class AuthenticationError(APIError): ...
class ValidationError(APIError): ...
class RateLimitError(APIError): ...
class ServerError(APIError): ...
```

### Usage

```python
# Before (verbose)
response = await get_all_products.asyncio_detailed(client=client)
if response.status_code == 200:
    if isinstance(response.parsed, ProductListResponse):
        products = response.parsed.data
else:
    raise Exception(f"Error: {response.status_code}")

# After (concise)
response = await get_all_products.asyncio_detailed(client=client)
products = unwrap_data(response)  # Automatic error handling!

# Or with explicit error handling
try:
    products = unwrap_data(response)
except AuthenticationError:
    # Re-authenticate
except ValidationError as e:
    # Handle validation
```

## Consequences

### Positive Consequences

1. **Reduced Boilerplate**: 5+ lines → 1 line for common case
1. **Type Safety**: Proper `@overload` decorators for type narrowing
1. **Better Errors**: Typed exceptions instead of generic errors
1. **IDE Support**: Full autocomplete and type hints
1. **Opt-In**: Can still use `Response` directly
1. **Composable**: Can combine utilities for complex scenarios
1. **Error Context**: Exceptions include status code, messages
1. **No Assertions Needed**: Type system knows return value is not None

### Negative Consequences

1. **Additional API**: Users need to learn utilities
1. **Magic**: Errors raised automatically (but this is usually good)
1. **Abstraction**: Hides some response details

### Neutral Consequences

1. **Comprehensive Tests**: 31 tests for utilities (98.1% coverage)
1. **Export from Main**: Available as `from katana_public_api_client import unwrap`

## Type System Design

Used `@overload` to make type checker understand behavior:

```python
@overload
def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = True,  # Default
    default: None = None,
) -> list[Any]:  # Never None when raise_on_error=True
    ...

@overload
def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = False,  # Explicitly False
    default: None = None,
) -> Optional[list[Any]]:  # Can be None
    ...
```

This means no assertions needed in user code:

```python
# Type checker knows this is list[Any], never None
products = unwrap_data(response)
print(f"Got {len(products)} products")  # No type error!
```

## Alternatives Considered

### Alternative 1: Monadic Result Type

Use Result/Either monad pattern:

```python
result = await get_all_products.asyncio_detailed(client=client)
products = (
    result
    .map(lambda r: r.data)
    .unwrap_or([])
)
```

**Pros:**

- Functional programming style
- Explicit error handling
- Composable

**Cons:**

- Not Pythonic
- Steep learning curve
- Overkill for simple case
- Need to learn monadic operations

**Why Rejected:** Too complex, not Pythonic.

### Alternative 2: Add Methods to Response Class

Extend Response with utility methods:

```python
response = await get_all_products.asyncio_detailed(client=client)
products = response.unwrap_data()
```

**Pros:**

- Method chaining
- Discoverable via IDE

**Cons:**

- Can't modify generated Response class
- Would break on regeneration
- Monkey-patching is fragile

**Why Rejected:** Can't safely modify generated classes.

### Alternative 3: Context Manager

Use context manager for error handling:

```python
with handle_response() as handler:
    response = await get_all_products.asyncio_detailed(client=client)
    products = handler.get_data(response)
```

**Pros:**

- Scoped error handling
- Clear error boundary

**Cons:**

- Verbose
- Unclear benefit over try/except
- Extra indentation

**Why Rejected:** More complex than simple function call.

## Implementation Quality

### Comprehensive Testing

31 tests in `tests/test_utils.py`:

- All utility functions tested
- Edge cases covered
- Type annotations tested
- Error paths validated
- 98.1% code coverage

### Error Handling

Handles nested error responses from Katana API:

```python
{
    "error": {
        "message": "Validation failed",
        "errors": [
            {"field": "name", "message": "Required"}
        ]
    }
}
```

Converted to:

```python
raise ValidationError(
    "Validation failed: name: Required",
    status_code=400,
    validation_errors=[...]
)
```

### UNSET Handling

Handles Katana's `UNSET` fields gracefully:

```python
# If response.parsed.data is UNSET
products = unwrap_data(response)  # Returns [] not crash
```

## References

- [utils.py Implementation](../../katana_public_api_client/utils.py)
- [tests/test_utils.py](../../tests/test_utils.py) - 31 tests, 98.1% coverage
- [examples/using_utils.py](../../examples/using_utils.py)
- [REVISED_ASSESSMENT.md](../REVISED_ASSESSMENT.md)
- GitHub commit: fix: correct unwrap_data type overloads and handle single objects
