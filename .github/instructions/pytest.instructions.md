______________________________________________________________________

## description: 'Testing standards using pytest for katana-openapi-client project' applyTo: \['**/test\_\*.py', '**/\*\_test.py', '\*\*/conftest.py'\]

# Pytest Testing Standards

## Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Setup test data
    client = KatanaClient(api_key="test")
    expected = "result"

    # Act - Execute the code
    result = function_under_test(client)

    # Assert - Verify outcome
    assert result == expected
```

## Test Naming

- **Files**: `test_*.py` or `*_test.py`
- **Functions**: `test_descriptive_name_when_condition_then_outcome`
- **Classes**: `TestClassName`

```python
def test_get_product_returns_404_when_not_found():
    """Test product retrieval with non-existent ID."""
    ...

def test_create_order_success_with_valid_data():
    """Test successful order creation."""
    ...
```

## Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_api_call():
    """Test async API operation."""
    async with KatanaClient() as client:
        response = await get_products.asyncio_detailed(client=client)
        assert response.status_code == 200
```

## Fixtures

Define reusable test setup in `conftest.py`:

```python
import pytest
from katana_public_api_client import KatanaClient

@pytest.fixture
def katana_client():
    """Provide test KatanaClient."""
    return KatanaClient(api_key="test-key")

@pytest.fixture
async def async_client():
    """Provide async KatanaClient."""
    async with KatanaClient(api_key="test") as client:
        yield client

@pytest.fixture
def mock_product_data():
    """Provide sample product data."""
    return {
        "id": "prod_123",
        "name": "Test Product",
        "sku": "TEST-001",
    }
```

## Parametrization

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    ("valid-sku", True),
    ("invalid", False),
    ("", False),
    (None, False),
])
def test_sku_validation(input, expected):
    """Test SKU validation with various inputs."""
    result = validate_sku(input)
    assert result == expected
```

## Mocking HTTP Requests

```python
import responses

@responses.activate
def test_api_call():
    """Test API call with mocked response."""
    responses.add(
        responses.GET,
        "https://api.katanamrp.com/v1/products",
        json={"data": [{"id": "1", "name": "Product"}]},
        status=200,
    )

    async with KatanaClient() as client:
        response = await get_products.asyncio_detailed(client=client)
        assert response.status_code == 200
```

## Testing Error Paths

Always test error scenarios:

```python
@responses.activate
def test_api_401_unauthorized():
    """Test handling of unauthorized error."""
    responses.add(
        responses.GET,
        "https://api.katanamrp.com/v1/products",
        json={"error": "Unauthorized"},
        status=401,
    )

    async with KatanaClient() as client:
        response = await get_products.asyncio_detailed(client=client)
        assert response.status_code == 401
```

## Coverage Requirements

- **Core logic**: 87%+ coverage (required)
- **Helper functions**: 90%+ coverage
- **Critical paths**: 95%+ coverage

```bash
# Run with coverage
uv run poe test-coverage

# View missing lines
uv run pytest --cov-report=term-missing
```

## Test Marks

```python
# Unit tests
@pytest.mark.unit
def test_helper_function():
    """Test helper utility."""
    ...

# Integration tests (require KATANA_API_KEY)
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("KATANA_API_KEY"), reason="No API key")
async def test_real_api():
    """Test against real API."""
    ...

# Slow tests
@pytest.mark.slow
def test_expensive_operation():
    """Long-running test."""
    ...
```

## Edge Cases

Always test:

- Empty inputs
- None values
- Boundary conditions
- Invalid data

```python
def test_edge_cases():
    """Test edge cases."""
    # Empty
    assert process([]) == []

    # None
    with pytest.raises(ValueError):
        process(None)

    # Boundary
    assert process([1]) == [1]
```

## Assertions

```python
# Basic assertions
assert result == expected
assert result is not None
assert len(items) == 3

# Exception testing
with pytest.raises(ValueError, match="invalid"):
    risky_function()

# Approximate for floats
assert result == pytest.approx(3.14159, rel=1e-5)

# Helpful messages
assert result == expected, f"Expected {expected}, got {result}"
```

## Critical Reminders

1. **Test before implementing** (TDD approach when possible)
1. **Mock external dependencies** - Don't hit real APIs in unit tests
1. **Test error paths** - Not just success scenarios
1. **Maintain 87%+ coverage** - Required for core logic
1. **Use fixtures** - Avoid code duplication in tests
1. **Mark integration tests** - Separate from unit tests
1. **Provide helpful assertions** - Include failure messages
