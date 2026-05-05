______________________________________________________________________

## description: 'Generate comprehensive tests for a component following project testing standards'

# Create Comprehensive Tests

Generate complete test coverage for a component following pytest and project standards.

## Instructions

1. **Identify the component** to test:

   - Module path (e.g., `katana_public_api_client/helpers/products.py`)
   - Functions/classes to test
   - Dependencies to mock

1. **Create test file** following naming convention:

   - For `module.py` → create `tests/test_module.py`
   - For `path/to/module.py` → create `tests/path/to/test_module.py`

1. **Write comprehensive tests** covering:

   **Success paths** - Happy path scenarios

   ```python
   @pytest.mark.asyncio
   async def test_get_products_success():
       """Test successful product retrieval."""
       # Arrange
       ...
       # Act
       ...
       # Assert
       assert result.status_code == 200
   ```

   **Error paths** - Failure scenarios

   ```python
   @pytest.mark.asyncio
   async def test_get_products_404_not_found():
       """Test handling of 404 error."""
       # Setup mock 404 response
       ...
       assert result.status_code == 404
   ```

   **Edge cases** - Boundary conditions

   ```python
   def test_process_items_with_empty_list():
       """Test processing with empty input."""
       result = process_items([])
       assert result == []

   def test_process_items_with_none():
       """Test handling of None input."""
       with pytest.raises(ValueError):
           process_items(None)
   ```

1. **Setup fixtures** in `conftest.py` if reusable:

   ```python
   @pytest.fixture
   def mock_api_client():
       """Provide mocked API client."""
       return Mock(spec=KatanaClient)
   ```

1. **Mock external dependencies**:

   ```python
   import responses

   @responses.activate
   def test_api_call():
       responses.add(
           responses.GET,
           "https://api.katanamrp.com/v1/endpoint",
           json={"data": []},
           status=200
       )
       # Test code...
   ```

1. **Run tests and verify coverage**:

   ```bash
   # Run tests
   uv run poe test

   # Check coverage
   uv run poe test-coverage

   # View missing coverage
   uv run pytest --cov-report=term-missing
   ```

1. **Achieve coverage goals**:

   - Core logic: 87%+ (required)
   - Helper functions: 90%+
   - Critical paths: 95%+

## Test Structure Template

```python
import pytest
from unittest.mock import Mock, AsyncMock
import responses

# Import code under test
from katana_public_api_client.helpers.products import Products


class TestProductsList:
    """Tests for Products.list method."""

    @pytest.mark.asyncio
    async def test_success_with_filter(self):
        """Test successful product list with filter."""
        # Arrange
        client = Mock()
        products = Products(client)

        # Act
        result = await products.list(is_sellable=True)

        # Assert
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test get with non-existent product ID."""
        # Arrange
        client = Mock()
        products = Products(client)

        # Act & Assert
        with pytest.raises(APIError):
            await products.get(99999)

    @pytest.mark.parametrize("query,expected_min", [
        ("widget", 1),
        ("nonexistent-xyz", 0),
    ])
    async def test_search_with_queries(self, query, expected_min):
        """Test search with various queries."""
        client = Mock()
        products = Products(client)
        result = await products.search(query)
        assert len(result) >= expected_min
```

## Success Criteria

- [ ] All public functions have tests
- [ ] Success paths tested
- [ ] Error paths tested
- [ ] Edge cases covered
- [ ] External dependencies mocked
- [ ] Fixtures created for reusable setup
- [ ] Coverage meets goals (87%+)
- [ ] Tests pass: `uv run poe test`
- [ ] Following AAA pattern consistently
- [ ] Descriptive test names
