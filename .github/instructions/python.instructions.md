______________________________________________________________________

## description: 'Python development standards for katana-openapi-client project' applyTo: '\*\*/\*.py'

# Python Development Standards

## Code Style

- **PEP 8 compliance**: Follow Python style guide
- **Line length**: 88 characters (Black/ruff default)
- **Indentation**: 4 spaces (never tabs)
- **Imports**: Organized with isort/ruff (stdlib → third-party → local)
- **Quotes**: Prefer double quotes for strings

## Type Hints (Required)

- **All functions** must have complete type annotations
- **Parameters and return values** must be typed
- **Use modern syntax**: `list[str]` not `List[str]` (Python 3.11+)
- **Optional types**: Use `str | None` not `Optional[str]`
- **Import types correctly**: `from katana_public_api_client.client_types import ...`

```python
from typing import AsyncIterator
from katana_public_api_client.domain.product import Product

async def get_products_by_category(
    category: str,
    limit: int | None = None
) -> AsyncIterator[Product]:
    """Get products filtered by category."""
    ...
```

## Async/Await Patterns

- **Use async/await** for I/O-bound operations
- **Async context managers** for resource cleanup
- **httpx for HTTP**: All API calls use httpx AsyncClient

```python
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(client=client)
```

## Pydantic Models (ADR-011)

- **Use Pydantic** for domain models, not attrs
- **Validation**: Leverage Field() for constraints
- **Serialization**: Use model.model_dump() and model.model_validate()

```python
from pydantic import BaseModel, Field

class ProductSearchParams(BaseModel):
    """Parameters for product search."""
    query: str = Field(min_length=1, description="Search query")
    category: str | None = Field(default=None, description="Category filter")
    limit: int = Field(default=50, ge=1, le=100, description="Results limit")
```

## Error Handling

- **Catch specific exceptions**, not bare `except:`
- **Informative error messages** for users
- **Proper logging** at appropriate levels

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = await api_call()
except HTTPStatusError as e:
    logger.error(f"API error: {e.response.status_code}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

## Logging

- **Use Python logging module**, not print statements
- **Levels**: DEBUG (internal), INFO (user actions), ERROR (failures)
- **Format**: Include context in messages

```python
logger.info(f"Fetching products for category: {category}")
logger.debug(f"API response: {response.status_code}")
logger.error(f"Failed to process order {order_id}: {error}")
```

## Documentation

- **Docstrings required** for all public functions/classes
- **Format**: Google-style docstrings
- **Include**: Description, Args, Returns, Raises

```python
def process_order(order_id: str, confirm: bool = False) -> str:
    """Process an order with optional confirmation.

    Args:
        order_id: Unique identifier for the order
        confirm: If True, actually process; if False, preview only

    Returns:
        Success message or error description

    Raises:
        ValueError: If order_id is invalid
        HTTPError: If API call fails
    """
    ...
```

## Testing

- **Tests required** for all new code
- **Coverage target**: 87%+ on core logic
- **Use pytest** with fixtures
- **Mock external dependencies**

## Resource Management

- **Always use context managers** for resources
- **Async context managers** for async resources
- **Clean up in finally blocks** if context managers not available

```python
async with KatanaClient() as client:
    # Client automatically closed
    response = await api_call(client)
```

## Import Organization

```python
# 1. Standard library
import asyncio
import logging
from typing import AsyncIterator

# 2. Third-party
from pydantic import BaseModel, Field
import httpx

# 3. Local
from katana_public_api_client import KatanaClient
from katana_public_api_client.domain.product import Product
```

## Common Patterns

### UNSET Sentinel

```python
from katana_public_api_client.client_types import UNSET

def update_product(
    product_id: str,
    name: str | type[UNSET] = UNSET,
    price: float | type[UNSET] = UNSET
) -> None:
    """Update product with optional fields."""
    if name is not UNSET:
        # Name was explicitly provided
        ...
```

### Async Generators

```python
async def get_all_items() -> AsyncIterator[Item]:
    """Yield all items with automatic pagination."""
    offset = 0
    while True:
        response = await fetch_page(offset=offset)
        if not response.items:
            break

        for item in response.items:
            yield item

        offset += len(response.items)
```

## Code Quality Tools

- **ruff**: Linting and formatting (`uv run poe lint`)
- **mypy**: Type checking (strict mode)
- **pytest**: Testing framework
- **pre-commit**: Automated quality checks

## Critical Reminders

1. **Never edit generated files** - They're in `katana_public_api_client/api/` and
   `katana_public_api_client/models/`
1. **Always use type hints** - Required for all functions
1. **Import from client_types** - Not from `types` module
1. **Use Pydantic models** - For domain logic, not generated attrs
1. **Test everything** - Including error paths
1. **Log appropriately** - INFO for users, DEBUG for developers, ERROR for problems
