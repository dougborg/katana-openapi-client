# ADR-007: Generate Domain Helper Classes

## Status

**PROPOSED**

Date: 2024-10-17

## Context

The current API is excellent for direct, transparent access to all endpoints:

```python
from katana_public_api_client.api.product import get_all_products

response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True,
    is_producible=True,
    include_deleted=False,
    include_archived=False,
    limit=100
)
products = unwrap_data(response)
```

However, common operations require:

- Repeated filter combinations
- Boilerplate for CRUD operations
- Business logic scattered across application code
- No domain-specific abstractions

Users want:

1. **Ergonomic wrappers** for common operations
1. **Smart methods** for domain patterns (e.g., "active sellable products")
1. **Type-safe** helpers with full IDE support
1. **Backward compatible** - generated API remains primary

## Decision

We will **generate domain helper classes** that combine auto-generated CRUD wrappers
with hand-written domain logic.

### Architecture

```python
# AUTO-GENERATED: CRUD wrappers
class ProductHelper:
    async def list(self, **filters) -> list[Product]:
        """Generated wrapper for get_all_products."""
        response = await get_all_products.asyncio_detailed(
            client=self._client,
            **filters
        )
        return unwrap_data(response)

    async def get(self, product_id: int) -> Product:
        """Generated wrapper for get_product."""
        ...

    async def create(self, data: dict) -> Product:
        """Generated wrapper for create_product."""
        ...

    async def update(self, product_id: int, data: dict) -> Product:
        """Generated wrapper for update_product."""
        ...

    async def delete(self, product_id: int) -> None:
        """Generated wrapper for delete_product."""
        ...

    # === HAND-WRITTEN: Domain logic ===

    async def active_sellable(self) -> list[Product]:
        """Get active sellable products (common filter)."""
        return await self.list(
            is_sellable=True,
            include_deleted=False,
            include_archived=False
        )

    async def low_stock(self, threshold: int = 10) -> list[tuple[Product, int]]:
        """Find products below stock threshold."""
        # Complex business logic combining products + inventory
        ...

    async def search(self, query: str) -> list[Product]:
        """Smart search across product fields."""
        ...
```

### Usage

```python
async with KatanaClient() as client:
    # Access via client property
    products = client.products

    # Generated wrappers (clean CRUD)
    all_products = await products.list(is_sellable=True)
    product = await products.get(123)
    new_product = await products.create({"name": "Widget"})

    # Hand-written domain logic
    active = await products.active_sellable()
    low_stock_items = await products.low_stock(threshold=5)
    search_results = await products.search("widget")

    # Other resources
    revenue = await client.sales_orders.revenue_by_period(start, end)
    in_progress = await client.manufacturing_orders.in_progress()
```

### Generation Strategy

1. **Parse OpenAPI spec** to identify resources and operations
1. **Generate helper class template** with CRUD wrappers
1. **Mark section for custom methods** (hand-written)
1. **Add helper properties to KatanaClient**
1. **Include in regeneration workflow**

The helpers are:

- ✅ **Auto-generated** - CRUD wrappers always in sync with API
- ✅ **Extensible** - Easy to add custom methods
- ✅ **Type-safe** - Full type hints and IDE support
- ✅ **Opt-in** - Direct API still available
- ✅ **Maintainable** - Clear separation of generated vs. custom

## Consequences

### Positive Consequences

1. **Reduced Boilerplate**: Common operations become one-liners
1. **Domain Intelligence**: Business logic in reusable helpers
1. **Discoverability**: `client.products.` shows all operations
1. **Type Safety**: Full IDE autocomplete
1. **Opt-In**: Direct API remains primary, helpers are sugar
1. **No Breaking Changes**: Purely additive
1. **Auto-Generated**: Stays in sync with OpenAPI spec
1. **Testable**: Easy to test helper logic

### Negative Consequences

1. **More Code**: Adds helper classes to codebase
1. **Two Ways**: Can do everything two ways (direct API vs helper)
1. **Learning Curve**: Users need to learn helper API
1. **Maintenance**: Custom methods need manual updates
1. **Abstraction**: Hides some underlying API details

### Neutral Consequences

1. **Generated + Manual**: Mix of auto-generated and hand-written code
1. **Documentation Needed**: Must document helpers and when to use them

## Alternatives Considered

### Alternative 1: Traditional Builder Pattern

See [ADR-008](0008-avoid-builder-pattern.md) for full analysis.

```python
query = (
    ProductQuery(client)
    .sellable()
    .producible()
    .created_between(start, end)
    .all()
)
```

**Why Rejected:**

- Too much abstraction
- Harder to debug
- Breaks type safety
- Current direct API is better for most cases
- See full analysis in ADR-008

### Alternative 2: No Helpers (Status Quo)

Keep only the direct API:

```python
response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True,
    is_producible=True,
    include_deleted=False,
    include_archived=False
)
```

**Pros:**

- Simplest approach
- No additional code
- Transparent and direct

**Cons:**

- Repetitive boilerplate
- No domain abstraction
- Business logic scattered
- Common patterns not reusable

**Why Rejected:** Misses opportunity to provide ergonomic improvements without
downsides.

### Alternative 3: Hand-Written Helpers Only

Write helpers manually, don't generate:

**Pros:**

- Full control
- Can optimize for common cases

**Cons:**

- Need to maintain 248+ wrapper methods manually
- Out of sync when API changes
- Lots of manual work
- Inconsistent across resources

**Why Rejected:** Too much manual work, doesn't scale.

## Implementation Plan

See [DOMAIN_HELPERS_DESIGN.md](../DOMAIN_HELPERS_DESIGN.md) for complete design.

### Phase 1: Core Infrastructure (1 week)

- Create `scripts/generate_helpers.py`
- Parse OpenAPI spec to extract resources
- Generate helper class templates
- Add to `regenerate_client.py` workflow

### Phase 2: Initial Helpers (1 week)

- Generate ProductHelper
- Generate SalesOrderHelper
- Generate ManufacturingOrderHelper
- Add helper properties to KatanaClient
- Write tests

### Phase 3: Custom Methods (2 weeks)

- Add domain methods to each helper
- Write tests for custom methods
- Create examples

### Phase 4: Documentation (1 week)

- Update README with helper examples
- Create API reference for helpers
- Add cookbook recipes using helpers

## Success Metrics

- [ ] 3+ core helpers implemented
- [ ] 10+ custom domain methods across helpers
- [ ] 80%+ test coverage for helper code
- [ ] Documentation with examples
- [ ] Positive user feedback

## References

- [DOMAIN_HELPERS_DESIGN.md](../DOMAIN_HELPERS_DESIGN.md) - Complete design document
- [BUILDER_PATTERN_ANALYSIS.md](../BUILDER_PATTERN_ANALYSIS.md) - Why not builders
- [ADR-008](0008-avoid-builder-pattern.md) - Builder pattern rejection
- Issue #29: Generate Domain Helper Classes for Common Operations
