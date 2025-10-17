# ADR-008: Avoid Traditional Builder Pattern

## Status

**PROPOSED**

Date: 2024-10-17

## Context

The current API can be verbose for complex queries with many parameters:

```python
response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True,
    is_producible=True,
    is_purchasable=False,
    batch_tracked=False,
    created_at_min=datetime(2024, 1, 1),
    created_at_max=datetime(2024, 12, 31),
    limit=100,
    page=1
)
```

The **Builder Pattern** is a common approach for complex object construction:

```python
query = (
    ProductQuery(client)
    .sellable()
    .producible()
    .not_purchasable()
    .not_batch_tracked()
    .created_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    .limit(100)
    .execute()
)
```

Question: Should we implement the builder pattern?

## Decision

We will **NOT implement traditional builder pattern**.

Instead, we will:

1. **Keep the direct API as primary** - it's transparent and type-safe
1. **Add domain helpers** (ADR-007) for common operations
1. **Provide cookbook examples** for complex queries

The direct API is better because:

- ✅ **Transparent**: Clear what's happening
- ✅ **Type-safe**: Perfect IDE autocomplete
- ✅ **Debuggable**: Easy to trace
- ✅ **Matches OpenAPI**: Direct mapping to specification
- ✅ **No learning curve**: Just function parameters

Builders would add:

- ❌ **Abstraction**: Hides underlying API calls
- ❌ **Learning curve**: Need to learn builder methods
- ❌ **Two ways to do everything**: Confusing
- ❌ **Type safety challenges**: Dynamic chaining is hard to type
- ❌ **Maintenance burden**: 248 endpoints × builder code

## Consequences

### Positive Consequences

1. **Simplicity**: Single, straightforward API
1. **Transparency**: Users see exactly what API calls are made
1. **Type Safety**: Perfect type hints and IDE support
1. **Debuggability**: Easy to trace and debug
1. **Less Code**: No builder classes to maintain
1. **No Confusion**: One way to call each endpoint
1. **Matches OpenAPI**: Direct correspondence to spec

### Negative Consequences

1. **Verbosity**: Complex queries can be long
1. **No Method Chaining**: Can't chain operations
1. **No Validation**: Parameters validated by API, not client

### Neutral Consequences

1. **Domain Helpers**: Provides ergonomics without builder downsides
1. **Cookbook Examples**: Shows patterns for complex scenarios

## Detailed Analysis

See [BUILDER_PATTERN_ANALYSIS.md](../BUILDER_PATTERN_ANALYSIS.md) for comprehensive
analysis with code examples.

### What Builders Would Look Like

```python
# Fluent API
query = (
    ProductQuery(client)
    .sellable()
    .producible()
    .not_batch_tracked()
    .created_between(datetime(2024, 1, 1), datetime(2024, 12, 31))
    .limit(100)
    .all()
)
```

### Why This is Worse Than Direct API

**1. Abstraction**

```python
# Builder: What API call is this making?
products = await ProductQuery(client).sellable().all()

# Direct: Clear what's happening
response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True
)
products = unwrap_data(response)
```

**2. Type Safety**

```python
# Builder: Dynamic chaining breaks autocomplete
query.sellable().producible().???  # What methods exist?

# Direct: Perfect autocomplete
await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=  # IDE shows: bool
    is_producible=  # IDE shows: bool
)
```

**3. Debuggability**

```python
# Builder: Need to trace through multiple methods
query = ProductQuery(client).sellable()  # Step 1
query = query.producible()  # Step 2
result = await query.execute()  # Step 3: Where is the actual API call?

# Direct: Single step, clear
response = await get_all_products.asyncio_detailed(...)  # API call here
```

**4. Two Ways to Do Everything**

```python
# Builder way
products = await ProductQuery(client).sellable().all()

# Direct way
response = await get_all_products.asyncio_detailed(client=client, is_sellable=True)
products = unwrap_data(response)

# Which should users use? Confusion!
```

## Alternatives Considered

### Alternative 1: Full Builder Pattern

Implement builders for all 248 endpoints.

**Rejected**: Too much code, breaks transparency, hurts type safety.

### Alternative 2: Hybrid (Builders for Complex Queries Only)

Builders only for complex endpoints (e.g., `ProductQuery`, `SalesOrderQuery`).

**Rejected**: Still creates two ways to do things, inconsistent API.

### Alternative 3: Partial Application / Bound Client

```python
products = client.products
result = await products.get_all(is_sellable=True)
```

**Considered**: This is essentially what domain helpers provide (ADR-007).

## What We Do Instead

### 1. Domain Helpers (ADR-007)

Provide high-level operations without hiding the API:

```python
# Helper provides ergonomics
active = await client.products.active_sellable()

# But users can still see what it does
async def active_sellable(self):
    return await self.list(
        is_sellable=True,
        include_deleted=False,
        include_archived=False
    )

# And can use direct API if needed
response = await get_all_products.asyncio_detailed(client=client, ...)
```

### 2. Cookbook Examples

Provide examples for complex scenarios:

```python
# docs/COOKBOOK.md

## Complex Product Filtering

# Scenario: Find sellable, producible products created in 2024

response = await get_all_products.asyncio_detailed(
    client=client,
    is_sellable=True,
    is_producible=True,
    created_at_min=datetime(2024, 1, 1),
    created_at_max=datetime(2024, 12, 31),
    limit=250  # Use max limit for efficiency
)
products = unwrap_data(response)
```

### 3. Utility Functions

Provide utilities that work with responses:

```python
# Instead of builder methods
products = unwrap_data(response)

# Can compose with helpers
active_products = [p for p in products if p.is_sellable and not p.deleted]
```

## When Users Ask for Builders

If users request builders, we can:

1. **Explain the tradeoffs** (this ADR)
1. **Show domain helpers** as alternative (ADR-007)
1. **Provide cookbook examples** for their specific use case
1. **Consider their use case** - might reveal need for specific helper method

If builders are truly needed, revisit this decision with:

- Concrete use cases builders solve better
- Evidence current approach is limiting
- Proposal that maintains type safety

## References

- [BUILDER_PATTERN_ANALYSIS.md](../BUILDER_PATTERN_ANALYSIS.md) - Detailed analysis
- [ADR-007](0007-domain-helper-classes.md) - Domain helpers (better alternative)
- [DOMAIN_HELPERS_DESIGN.md](../DOMAIN_HELPERS_DESIGN.md) - Complete helper design
- Issue #29: Generate Domain Helper Classes (recommended approach)
