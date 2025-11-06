______________________________________________________________________

## description: 'Generate comprehensive tests for a component following project testing standards'

# Create Comprehensive Tests

Generate complete test coverage for a component following pytest and project standards.

## Instructions

1. **Identify the component** to test:

   - Module path (e.g., `katana_public_api_client/helpers/inventory.py`)
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
from katana_public_api_client.helpers.inventory import check_inventory


class TestCheckInventory:
    """Tests for check_inventory function."""

    @pytest.mark.asyncio
    async def test_success_with_valid_sku(self):
        """Test successful inventory check with valid SKU."""
        # Arrange
        sku = "VALID-SKU"
        expected_stock = 10

        # Act
        result = await check_inventory(sku)

        # Assert
        assert result.stock_level == expected_stock

    @pytest.mark.asyncio
    async def test_not_found_with_invalid_sku(self):
        """Test inventory check with non-existent SKU."""
        # Arrange
        sku = "INVALID-SKU"

        # Act & Assert
        with pytest.raises(ProductNotFoundError):
            await check_inventory(sku)

    @pytest.mark.parametrize("sku,expected", [
        ("VALID-1", True),
        ("VALID-2", True),
        ("INVALID", False),
    ])
    async def test_validation_with_multiple_skus(self, sku, expected):
        """Test SKU validation with various inputs."""
        result = validate_sku(sku)
        assert result == expected
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
