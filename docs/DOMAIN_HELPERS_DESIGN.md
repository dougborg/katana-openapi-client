# Domain Helpers Design - Generated + Custom

## Overview

Domain helpers provide high-level, ergonomic APIs for common operations while keeping
the generated API as the source of truth. They combine:

1. **Generated boilerplate** - wrapper methods for CRUD operations
1. **Hand-written intelligence** - domain-specific logic and common patterns
1. **Type safety** - full type hints and IDE support

______________________________________________________________________

## Architecture

```
User Code
    ↓
Domain Helpers (generated wrappers + manual logic)
    ↓
Generated API Functions (from OpenAPI)
    ↓
KatanaClient (resilient transport)
```

______________________________________________________________________

## Generation Strategy

### Step 1: Analyze OpenAPI Spec to Identify Resources

```python
# scripts/generate_helpers.py

def extract_resources(openapi_spec: dict) -> dict[str, Resource]:
    """Extract resource groups from OpenAPI paths."""
    resources = defaultdict(lambda: {"operations": {}})

    for path, path_item in openapi_spec["paths"].items():
        # Extract resource name from path
        # /products -> products
        # /products/{id} -> products
        # /sales-orders -> sales_orders
        resource_name = extract_resource_name(path)

        for method, operation in path_item.items():
            if method not in ["get", "post", "put", "patch", "delete"]:
                continue

            operation_type = classify_operation(method, path, operation)
            resources[resource_name]["operations"][operation_type] = {
                "method": method,
                "path": path,
                "operation_id": operation["operationId"],
                "parameters": operation.get("parameters", []),
                "request_body": operation.get("requestBody"),
                "responses": operation["responses"],
            }

    return resources

def classify_operation(method: str, path: str, operation: dict) -> str:
    """Classify operation type for helper generation."""
    if method == "get" and "{id}" not in path:
        return "list"
    elif method == "get" and "{id}" in path:
        return "get"
    elif method == "post":
        return "create"
    elif method == "put" or method == "patch":
        return "update"
    elif method == "delete":
        return "delete"
    else:
        return "custom"
```

### Step 2: Generate Helper Class Template

````python
# Generated output: katana_public_api_client/helpers/products.py

from typing import Any, overload
from ..client import AuthenticatedClient
from ..api.product import (
    get_all_products,
    get_product,
    create_product,
    update_product,
    delete_product,
)
from ..models.product import Product
from ..models.product_list_response import ProductListResponse
from ..utils import unwrap, unwrap_data


class ProductHelper:
    """
    High-level helper for product operations.

    This class provides convenient methods for common product operations,
    combining generated wrappers with hand-written domain logic.

    Generated methods:
    - list(): List all products with optional filters
    - get(): Get a single product by ID
    - create(): Create a new product
    - update(): Update an existing product
    - delete(): Delete a product

    Custom methods (add manually):
    - search(): Smart search across product fields
    - active_sellable(): Common filter for active sellable products
    - low_stock(): Find products below stock threshold
    - bulk_update(): Update multiple products efficiently
    """

    def __init__(self, client: AuthenticatedClient):
        """Initialize the product helper with an authenticated client."""
        self._client = client

    # =========================================================================
    # Generated Methods - DO NOT EDIT MANUALLY
    # These methods are auto-generated from the OpenAPI specification.
    # To modify, edit scripts/generate_helpers.py and regenerate.
    # =========================================================================

    async def list(
        self,
        *,
        ids: list[int] | None = None,
        name: str | None = None,
        is_sellable: bool | None = None,
        is_producible: bool | None = None,
        limit: int = 50,
        page: int = 1,
        **kwargs: Any,
    ) -> list[Product]:
        """
        List products with optional filters.

        Args:
            ids: Filter by product IDs
            name: Filter by product name
            is_sellable: Filter by sellable status
            is_producible: Filter by producible status
            limit: Number of items per page (1-250)
            page: Page number
            **kwargs: Additional filters (see get_all_products parameters)

        Returns:
            List of Product objects

        Example:
            ```python
            async with KatanaClient() as client:
                products = ProductHelper(client)
                sellable = await products.list(is_sellable=True, limit=100)
            ```
        """
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            ids=ids,
            name=name,
            is_sellable=is_sellable,
            is_producible=is_producible,
            limit=limit,
            page=page,
            **kwargs,
        )
        return unwrap_data(response)

    def list_sync(
        self,
        *,
        ids: list[int] | None = None,
        name: str | None = None,
        is_sellable: bool | None = None,
        is_producible: bool | None = None,
        limit: int = 50,
        page: int = 1,
        **kwargs: Any,
    ) -> list[Product]:
        """Synchronous version of list()."""
        response = get_all_products.sync_detailed(
            client=self._client,
            ids=ids,
            name=name,
            is_sellable=is_sellable,
            is_producible=is_producible,
            limit=limit,
            page=page,
            **kwargs,
        )
        return unwrap_data(response)

    async def get(self, product_id: int) -> Product:
        """
        Get a single product by ID.

        Args:
            product_id: The product ID

        Returns:
            Product object

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the product doesn't exist or other API error

        Example:
            ```python
            product = await products.get(123)
            print(f"Product: {product.name}")
            ```
        """
        response = await get_product.asyncio_detailed(
            client=self._client,
            id=product_id,
        )
        return unwrap(response)

    def get_sync(self, product_id: int) -> Product:
        """Synchronous version of get()."""
        response = get_product.sync_detailed(
            client=self._client,
            id=product_id,
        )
        return unwrap(response)

    async def create(self, product_data: dict[str, Any]) -> Product:
        """
        Create a new product.

        Args:
            product_data: Product data dictionary

        Returns:
            Created Product object

        Example:
            ```python
            new_product = await products.create({
                "name": "Widget",
                "uom": "pcs",
                "is_sellable": True,
            })
            ```
        """
        response = await create_product.asyncio_detailed(
            client=self._client,
            json_body=product_data,
        )
        return unwrap(response)

    async def update(
        self,
        product_id: int,
        updates: dict[str, Any]
    ) -> Product:
        """
        Update an existing product.

        Args:
            product_id: The product ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated Product object

        Example:
            ```python
            updated = await products.update(123, {"name": "New Name"})
            ```
        """
        response = await update_product.asyncio_detailed(
            client=self._client,
            id=product_id,
            json_body=updates,
        )
        return unwrap(response)

    async def delete(self, product_id: int) -> None:
        """
        Delete a product.

        Args:
            product_id: The product ID to delete

        Example:
            ```python
            await products.delete(123)
            ```
        """
        response = await delete_product.asyncio_detailed(
            client=self._client,
            id=product_id,
        )
        unwrap(response)

    # =========================================================================
    # Custom Methods - ADD YOUR DOMAIN LOGIC HERE
    # These methods are hand-written and provide domain-specific functionality.
    # =========================================================================

    # TODO: Add custom helper methods below
    # Examples:
    # - async def search(self, query: str) -> list[Product]: ...
    # - async def active_sellable(self) -> list[Product]: ...
    # - async def low_stock(self, threshold: int) -> list[Product]: ...
````

______________________________________________________________________

## Custom Methods - Examples to Add Manually

````python
# Add these to the generated ProductHelper class

async def search(
    self,
    query: str,
    *,
    search_fields: list[str] | None = None,
    **filters: Any
) -> list[Product]:
    """
    Search products by text query.

    Args:
        query: Search term
        search_fields: Fields to search in (default: name, sku)
        **filters: Additional filters to apply

    Returns:
        List of matching products

    Example:
        ```python
        results = await products.search("widget", is_sellable=True)
        ```
    """
    # Start with name search (API supports this)
    products = await self.list(name=query, **filters)

    # Could add client-side filtering for other fields if needed
    if search_fields:
        # Filter by additional fields
        pass

    return products


async def active_sellable(
    self,
    *,
    limit: int = 100
) -> list[Product]:
    """
    Get all active sellable products.

    This is a common filter combination that excludes deleted and archived
    products while only returning sellable items.

    Returns:
        List of active sellable products

    Example:
        ```python
        sellable = await products.active_sellable()
        for product in sellable:
            print(f"{product.name}: ${product.price}")
        ```
    """
    return await self.list(
        is_sellable=True,
        include_deleted=False,
        include_archived=False,
        limit=limit,
    )


async def low_stock(
    self,
    threshold: int = 10,
    location_id: int | None = None
) -> list[tuple[Product, int]]:
    """
    Find products below stock threshold.

    Args:
        threshold: Stock level threshold
        location_id: Optional location filter

    Returns:
        List of (product, current_stock) tuples

    Example:
        ```python
        low_items = await products.low_stock(threshold=5)
        for product, stock in low_items:
            print(f"{product.name}: {stock} remaining")
        ```
    """
    # Get all products
    products = await self.list()

    # Get inventory levels
    from ..api.inventory import get_all_inventory
    inventory_response = await get_all_inventory.asyncio_detailed(
        client=self._client,
    )
    inventory = unwrap_data(inventory_response)

    # Build stock map
    stock_map = {}
    for inv in inventory:
        if location_id is None or inv.location_id == location_id:
            variant_id = inv.variant_id
            stock_map[variant_id] = stock_map.get(variant_id, 0) + inv.in_stock

    # Find low stock products
    low_stock_items = []
    for product in products:
        if product.variants:
            for variant in product.variants:
                current_stock = stock_map.get(variant.id, 0)
                if current_stock < threshold:
                    low_stock_items.append((product, current_stock))
                    break  # Only add product once

    return low_stock_items


async def bulk_update(
    self,
    updates: dict[int, dict[str, Any]]
) -> list[Product]:
    """
    Update multiple products efficiently.

    Args:
        updates: Dictionary mapping product_id -> update_dict

    Returns:
        List of updated products

    Example:
        ```python
        updated = await products.bulk_update({
            123: {"price": 29.99},
            124: {"price": 39.99, "name": "Premium Widget"},
        })
        ```
    """
    results = []
    for product_id, update_data in updates.items():
        updated = await self.update(product_id, update_data)
        results.append(updated)
    return results


async def by_category(
    self,
    category: str,
    **filters: Any
) -> list[Product]:
    """
    Get products by category name.

    Args:
        category: Category name to filter by
        **filters: Additional filters

    Returns:
        List of products in the category

    Example:
        ```python
        widgets = await products.by_category("Widgets")
        ```
    """
    all_products = await self.list(**filters)
    return [
        p for p in all_products
        if p.category_name and p.category_name.lower() == category.lower()
    ]


async def with_low_inventory(
    self,
    *,
    threshold: int = 10,
    include_stock_levels: bool = False
) -> list[Product] | list[tuple[Product, int]]:
    """
    Find products with low inventory across all locations.

    Args:
        threshold: Minimum stock threshold
        include_stock_levels: If True, return (product, stock) tuples

    Returns:
        List of products or (product, stock) tuples

    Example:
        ```python
        # Simple list
        low = await products.with_low_inventory(threshold=5)

        # With stock levels
        low_detailed = await products.with_low_inventory(
            threshold=5,
            include_stock_levels=True
        )
        for product, stock in low_detailed:
            print(f"{product.name}: {stock} units")
        ```
    """
    items = await self.low_stock(threshold)
    if include_stock_levels:
        return items
    return [product for product, _ in items]
````

______________________________________________________________________

## Other Resource Helpers

### SalesOrderHelper

```python
class SalesOrderHelper:
    """Helper for sales order operations."""

    def __init__(self, client: AuthenticatedClient):
        self._client = client

    # Generated CRUD methods
    async def list(self, **filters) -> list[SalesOrder]: ...
    async def get(self, order_id: int) -> SalesOrder: ...
    async def create(self, order_data: dict) -> SalesOrder: ...
    async def update(self, order_id: int, updates: dict) -> SalesOrder: ...

    # Custom domain methods
    async def open_orders(self) -> list[SalesOrder]:
        """Get all open sales orders."""
        return await self.list(status="open")

    async def overdue(self) -> list[SalesOrder]:
        """Get overdue orders."""
        from datetime import datetime
        orders = await self.list(status="open")
        return [
            o for o in orders
            if o.due_date and o.due_date < datetime.now()
        ]

    async def by_customer(
        self,
        customer_id: int,
        status: str | None = None
    ) -> list[SalesOrder]:
        """Get orders for a specific customer."""
        return await self.list(customer_id=customer_id, status=status)

    async def revenue_by_period(
        self,
        start: datetime,
        end: datetime
    ) -> Decimal:
        """Calculate total revenue for a period."""
        orders = await self.list(
            created_at_min=start,
            created_at_max=end,
            status="completed"
        )
        return sum(o.total_amount for o in orders if o.total_amount)
```

### ManufacturingOrderHelper

```python
class ManufacturingOrderHelper:
    """Helper for manufacturing order operations."""

    async def in_progress(self) -> list[ManufacturingOrder]:
        """Get all in-progress manufacturing orders."""
        return await self.list(status="in_progress")

    async def by_product(
        self,
        product_id: int
    ) -> list[ManufacturingOrder]:
        """Get manufacturing orders for a product."""
        return await self.list(product_id=product_id)

    async def production_capacity(
        self,
        start: datetime,
        end: datetime
    ) -> dict[int, int]:
        """
        Calculate production capacity by product for a period.

        Returns:
            Dictionary mapping product_id -> quantity produced
        """
        orders = await self.list(
            created_at_min=start,
            created_at_max=end,
            status="completed"
        )

        capacity = {}
        for order in orders:
            product_id = order.product_id
            quantity = order.quantity_to_manufacture
            capacity[product_id] = capacity.get(product_id, 0) + quantity

        return capacity
```

______________________________________________________________________

## Helper Registry (Optional)

Make helpers accessible via the main client:

```python
# katana_public_api_client/katana_client.py

class KatanaClient(AuthenticatedClient):
    """Enhanced Katana client with helpers."""

    @property
    def products(self) -> ProductHelper:
        """Access product helper methods."""
        if not hasattr(self, "_products_helper"):
            from .helpers.products import ProductHelper
            self._products_helper = ProductHelper(self)
        return self._products_helper

    @property
    def sales_orders(self) -> SalesOrderHelper:
        """Access sales order helper methods."""
        if not hasattr(self, "_sales_orders_helper"):
            from .helpers.sales_orders import SalesOrderHelper
            self._sales_orders_helper = SalesOrderHelper(self)
        return self._sales_orders_helper

    @property
    def manufacturing_orders(self) -> ManufacturingOrderHelper:
        """Access manufacturing order helper methods."""
        if not hasattr(self, "_manufacturing_orders_helper"):
            from .helpers.manufacturing_orders import ManufacturingOrderHelper
            self._manufacturing_orders_helper = ManufacturingOrderHelper(self)
        return self._manufacturing_orders_helper
```

### Usage:

```python
async with KatanaClient() as client:
    # Use helpers directly from client
    low_stock = await client.products.low_stock(threshold=5)
    open_orders = await client.sales_orders.open_orders()
    in_progress = await client.manufacturing_orders.in_progress()

    # Or instantiate directly
    from katana_public_api_client.helpers import ProductHelper
    products = ProductHelper(client)
    sellable = await products.active_sellable()
```

______________________________________________________________________

## Generation Script Structure

```bash
poetry run poe generate-helpers

# Output:
# Analyzing OpenAPI spec...
# Found 15 resource groups:
#   - products (5 operations)
#   - sales_orders (8 operations)
#   - manufacturing_orders (10 operations)
#   - ...
#
# Generating helper classes...
#   ✓ katana_public_api_client/helpers/products.py
#   ✓ katana_public_api_client/helpers/sales_orders.py
#   ✓ katana_public_api_client/helpers/manufacturing_orders.py
#   ...
#
# Generated 15 helper classes with 85 methods
# Add custom methods in the "Custom Methods" section of each file
```

______________________________________________________________________

## Benefits of This Approach

1. **Generated Boilerplate** ✅

   - CRUD operations auto-generated
   - Always in sync with OpenAPI spec
   - Type-safe with full hints

1. **Hand-Written Intelligence** ✅

   - Domain-specific logic where it matters
   - Common operation shortcuts
   - Business logic encapsulation

1. **Opt-In Complexity** ✅

   - Can still use direct API for simple cases
   - Helpers are sugar, not requirement
   - No breaking changes to existing code

1. **Maintainable** ✅

   - Clear separation of generated vs. custom
   - Regenerate doesn't clobber custom methods
   - Easy to extend with new helpers

1. **Discoverable** ✅

   - `client.products.` shows all options in IDE
   - Docstrings explain each method
   - Examples in every docstring

______________________________________________________________________

## Implementation Plan

### Phase 1: Core Infrastructure (1 week)

1. Create `scripts/generate_helpers.py`
1. Parse OpenAPI spec to extract resources
1. Generate helper class templates
1. Add to `regenerate_client.py` workflow

### Phase 2: Initial Helpers (1 week)

1. Generate ProductHelper
1. Generate SalesOrderHelper
1. Generate ManufacturingOrderHelper
1. Test and document

### Phase 3: Custom Methods (2 weeks)

1. Add custom methods to each helper
1. Write comprehensive tests
1. Create cookbook documentation
1. Add examples

### Phase 4: Integration (1 week)

1. Add helper properties to KatanaClient
1. Update documentation
1. Create migration guide
1. Update examples

______________________________________________________________________

## Conclusion

Domain helpers provide the **best balance** between:

- 🎯 Generated code (always correct, always in sync)
- 🧠 Domain intelligence (common patterns, smart defaults)
- 🔒 Type safety (full hints, IDE support)
- 📚 Discoverability (easy to find and use)

This approach gives users **both** options:

- Direct API for full control and transparency
- Helpers for ergonomics and common patterns

**Recommendation**: Start with 3-5 core helpers (products, sales orders, manufacturing
orders) and expand based on user feedback.
