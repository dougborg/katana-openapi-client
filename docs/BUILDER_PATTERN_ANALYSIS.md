# Builder Pattern Analysis for Katana OpenAPI Client

## Current State: Direct Function Calls

The current API uses direct function calls with keyword arguments:

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        is_sellable=True,
        is_producible=True,
        batch_tracked=False,
        created_at_min=datetime(2024, 1, 1),
        created_at_max=datetime(2024, 12, 31),
        limit=100,
        page=1
    )
```

**Pros:**

- ✅ Simple and direct
- ✅ Full type safety with IDE autocomplete
- ✅ Minimal abstraction - what you see is what you get
- ✅ Matches OpenAPI spec exactly
- ✅ No learning curve beyond the API itself

**Cons:**

- ⚠️ Can get verbose with many parameters (18+ params on some endpoints)
- ⚠️ No parameter grouping or validation before call
- ⚠️ Repeated client parameter on every call

______________________________________________________________________

## Option 1: Query Builder Pattern

### What it would look like:

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.builders import ProductQuery

async with KatanaClient() as client:
    # Fluent API for building queries
    query = (
        ProductQuery(client)
        .sellable()
        .producible()
        .not_batch_tracked()
        .created_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
        .limit(100)
        .page(1)
    )

    # Execute when ready
    response = await query.execute()
    # or
    products = await query.all()  # Auto-unwrap and paginate
```

### Benefits:

1. **Method Chaining = Readability**

   ```python
   # Before (hard to scan)
   response = await get_all_products.asyncio_detailed(
       client=client, is_sellable=True, is_producible=True,
       batch_tracked=False, limit=100, page=1
   )

   # After (reads like English)
   products = await (
       ProductQuery(client)
       .sellable()
       .producible()
       .not_batch_tracked()
       .limit(100)
       .all()
   )
   ```

1. **Smart Defaults & Validation**

   ```python
   class ProductQuery:
       def created_between(self, start: datetime, end: datetime):
           if start > end:
               raise ValueError("Start must be before end")
           self._created_at_min = start
           self._created_at_max = end
           return self

       def limit(self, value: int):
           if value < 1 or value > 250:
               raise ValueError("Limit must be 1-250")
           self._limit = value
           return self
   ```

1. **Parameter Grouping**

   ```python
   query = (
       ProductQuery(client)
       .filter(sellable=True, producible=True)  # Logical grouping
       .date_range(created_after=datetime(2024, 1, 1))
       .pagination(limit=100, page=1)
   )
   ```

1. **Reusable Query Templates**

   ```python
   # Define once, reuse many times
   active_products = ProductQuery(client).sellable().not_deleted()

   # Variations
   widgets = active_products.clone().name_contains("widget")
   recent = active_products.clone().created_after(last_week)
   ```

1. **Conditional Building**

   ```python
   query = ProductQuery(client)

   if user_filter.sellable:
       query = query.sellable()

   if user_filter.date_range:
       query = query.created_between(start, end)

   if user_filter.category:
       query = query.category(user_filter.category)

   products = await query.all()
   ```

### Downsides:

1. **Additional Abstraction Layer**

   - Hides the underlying API calls
   - Debugging becomes harder (need to trace through builder)
   - Not clear what the actual API request will be

1. **Type Safety Challenges**

   - Hard to maintain perfect type hints with dynamic chaining
   - IDE autocomplete might be weaker than direct function calls

1. **Learning Curve**

   - Users need to learn both the OpenAPI spec AND the builder API
   - Two ways to do everything = confusion

1. **Maintenance Burden**

   - Need to keep builders in sync with OpenAPI spec
   - 248 endpoint modules × builder code = lots of code
   - Breaking changes in OpenAPI require builder updates

1. **Performance Overhead (minimal)**

   - Extra method calls and object creation
   - Negligible but technically slower

______________________________________________________________________

## Option 2: Partial Application / Bound Client

### What it would look like:

```python
from katana_public_api_client import KatanaClient

async with KatanaClient() as client:
    # Bind client to API modules
    products = client.products
    orders = client.sales_orders

    # Client is implicit
    response = await products.get_all(
        is_sellable=True,
        is_producible=True,
        limit=100
    )

    # Create/update operations
    new_product = await products.create(name="Widget", ...)
    updated = await products.update(product_id=123, name="New Name")
```

### Benefits:

1. **Client Binding**

   - No need to pass `client=` on every call
   - Cleaner API surface

1. **Namespace Organization**

   ```python
   client.products.get_all()
   client.products.get(id=123)
   client.products.create(...)
   client.sales_orders.get_all()
   client.manufacturing_orders.get_all()
   ```

1. **Easier Mocking**

   ```python
   # Mock a specific resource
   mock_client.products = Mock()
   mock_client.products.get_all.return_value = [...]
   ```

### Downsides:

1. **Still verbose for complex queries**

   - Same parameter list problems as current approach

1. **Breaking the generated code pattern**

   - Current pattern: `from .api.product import get_all_products`
   - New pattern: `client.products.get_all`
   - Inconsistent with generated client architecture

______________________________________________________________________

## Option 3: Hybrid Approach (Recommended)

Keep the current direct function call approach as primary, but add **optional** builder
utilities for complex scenarios.

### Implementation:

```python
# Primary API (current) - unchanged
from katana_public_api_client.api.product import get_all_products

response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True,
    limit=100
)

# Optional builder for complex queries
from katana_public_api_client.builders import ProductQueryBuilder

builder = ProductQueryBuilder(client)
response = await (
    builder
    .sellable()
    .producible()
    .created_between(start, end)
    .execute(get_all_products)  # Explicitly ties to endpoint
)
```

### Why This is Best:

1. **No Breaking Changes** - Current API stays exactly the same
1. **Opt-in Complexity** - Use builders only when needed
1. **Clear Ownership** - Builders are helpers, not replacements
1. **Gradual Adoption** - Can add builders incrementally
1. **Type Safety Preserved** - Direct calls still have full types

### When to Use Each:

| Scenario                    | Use Direct API | Use Builder |
| --------------------------- | -------------- | ----------- |
| Simple query (1-3 params)   | ✅             | ❌          |
| Complex query (5+ params)   | ⚠️             | ✅          |
| Dynamic/conditional filters | ❌             | ✅          |
| One-off API call            | ✅             | ❌          |
| Repeated similar queries    | ⚠️             | ✅          |

______________________________________________________________________

## Code Generation Approach

### Builder Generation Strategy:

Since you asked about generating domain helpers, here's how we could auto-generate
builders from the OpenAPI spec:

```python
# scripts/generate_builders.py

def generate_query_builder(endpoint_spec: dict) -> str:
    """Generate a builder class from OpenAPI endpoint spec."""

    endpoint_name = endpoint_spec["operationId"]  # e.g., "get_all_products"
    parameters = endpoint_spec["parameters"]

    builder_methods = []

    # Generate method for each parameter
    for param in parameters:
        param_name = param["name"]
        param_type = param["schema"]["type"]

        if param_type == "boolean":
            # Generate toggle methods
            builder_methods.append(f"""
    def {param_name}(self, value: bool = True) -> Self:
        '''Set {param_name} filter.'''
        self._{param_name} = value
        return self
            """)

        elif param_type in ["string", "integer", "number"]:
            # Generate setter methods
            builder_methods.append(f"""
    def {param_name}(self, value: {python_type(param_type)}) -> Self:
        '''Set {param_name} filter.'''
        self._{param_name} = value
        return self
            """)

    # Generate the full builder class
    return f"""
class {to_class_name(endpoint_name)}Builder:
    '''Auto-generated builder for {endpoint_name}.'''

    def __init__(self, client: AuthenticatedClient):
        self._client = client
        {init_fields(parameters)}

    {chr(10).join(builder_methods)}

    async def execute(self) -> Response[...]:
        '''Execute the query.'''
        return await {endpoint_name}.asyncio_detailed(
            client=self._client,
            {build_kwargs()}
        )
    """
```

### Auto-Generated Output Example:

```python
# katana_public_api_client/builders/product.py (auto-generated)

from typing import Self
from ..client import AuthenticatedClient
from ..api.product import get_all_products

class GetAllProductsBuilder:
    '''Auto-generated builder for get_all_products endpoint.'''

    def __init__(self, client: AuthenticatedClient):
        self._client = client
        self._is_sellable = UNSET
        self._is_producible = UNSET
        self._limit = 50
        self._page = 1
        # ... etc

    def sellable(self, value: bool = True) -> Self:
        '''Filter by sellable products.'''
        self._is_sellable = value
        return self

    def producible(self, value: bool = True) -> Self:
        '''Filter by producible products.'''
        self._is_producible = value
        return self

    def limit(self, value: int) -> Self:
        '''Set pagination limit (1-250).'''
        if not 1 <= value <= 250:
            raise ValueError("Limit must be between 1 and 250")
        self._limit = value
        return self

    async def execute(self) -> Response[ErrorResponse | ProductListResponse]:
        '''Execute the query.'''
        return await get_all_products.asyncio_detailed(
            client=self._client,
            is_sellable=self._is_sellable,
            is_producible=self._is_producible,
            limit=self._limit,
            page=self._page,
        )

    async def all(self) -> list[Product]:
        '''Execute and unwrap to list of products with auto-pagination.'''
        response = await self.execute()
        return unwrap_data(response)
```

### Pros of Auto-Generation:

1. ✅ **Zero Maintenance** - Regenerate with client code
1. ✅ **Always in Sync** - Can't get out of date with API
1. ✅ **Complete Coverage** - Every endpoint gets a builder
1. ✅ **Consistent API** - All builders follow same pattern

### Cons of Auto-Generation:

1. ❌ **Generic Code** - Can't add domain-specific intelligence
1. ❌ **Large Codebase** - 248 endpoints = 248 builder classes
1. ❌ **Limited Customization** - Hard to add smart helpers

______________________________________________________________________

## Recommendation: Domain Helpers with Partial Generation

Instead of full builders, generate **domain-specific helper classes** that provide
intelligent, high-level operations:

```python
# katana_public_api_client/helpers/products.py (mix of generated + manual)

class ProductHelper:
    '''High-level operations for products (partially generated).'''

    def __init__(self, client: AuthenticatedClient):
        self._client = client

    # === Generated Methods ===

    async def list(self, **filters) -> list[Product]:
        '''List products with filters.'''
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            **filters
        )
        return unwrap_data(response)

    async def get(self, product_id: int) -> Product:
        '''Get a single product by ID.'''
        response = await get_product.asyncio_detailed(
            client=self._client,
            id=product_id
        )
        return unwrap(response)

    # === Hand-Written Domain Logic ===

    async def search(self, query: str) -> list[Product]:
        '''Search products by name (smart search).'''
        # Could add fuzzy matching, multiple filters, etc.
        return await self.list(name=query)

    async def active_sellable(self) -> list[Product]:
        '''Get all active sellable products (common query).'''
        return await self.list(
            is_sellable=True,
            include_deleted=False,
            include_archived=False
        )

    async def low_stock(self, threshold: int = 10) -> list[Product]:
        '''Find products below stock threshold.'''
        products = await self.list()
        # Filter by inventory levels
        return [p for p in products if self._check_stock(p) < threshold]

    async def bulk_update_prices(
        self,
        updates: dict[int, Decimal]
    ) -> list[Product]:
        '''Update prices for multiple products efficiently.'''
        results = []
        for product_id, new_price in updates.items():
            updated = await update_product.asyncio_detailed(
                client=self._client,
                id=product_id,
                price=new_price
            )
            results.append(unwrap(updated))
        return results
```

### Usage:

```python
async with KatanaClient() as client:
    products = ProductHelper(client)

    # Simple operations (generated)
    all_products = await products.list(is_sellable=True)
    widget = await products.get(product_id=123)

    # Smart operations (hand-written)
    low_stock_items = await products.low_stock(threshold=5)
    sellable = await products.active_sellable()

    # Bulk operations
    await products.bulk_update_prices({
        123: Decimal("29.99"),
        124: Decimal("39.99"),
    })
```

______________________________________________________________________

## Final Verdict

**Don't implement full builders.** They add complexity without enough benefit in this
context.

**Do implement domain helper classes** with:

- ✅ Generated wrapper methods (list, get, create, update, delete)
- ✅ Hand-written domain logic (search, common filters, bulk operations)
- ✅ Smart defaults and validation
- ✅ Ergonomic names for common operations

This gives you the best of both worlds:

- Keep the transparent, type-safe generated API
- Add convenience without hiding the underlying calls
- Provide domain intelligence where it matters
- Maintain clear documentation and debuggability
