# ADR-005: Provide Both Sync and Async APIs

## Status

Accepted

Date: 2024-07-01 (generated client includes both)

## Context

Modern Python applications use both synchronous and asynchronous patterns:

- **Async**: Web servers (FastAPI, Sanic), high-concurrency apps
- **Sync**: Scripts, Jupyter notebooks, simple applications, legacy code

The client generator (openapi-python-client) can generate:

- Async-only (asyncio)
- Sync-only
- Both sync and async

Considerations:

- Not all users want to use async/await
- Some environments don't support async well (REPL, notebooks)
- Async provides better performance for concurrent operations
- Supporting both means larger codebase

## Decision

We will **provide both synchronous and asynchronous APIs** for all endpoints.

Every generated endpoint module includes:

- `sync_detailed()` - Synchronous, returns full Response
- `sync()` - Synchronous, returns parsed data only
- `asyncio_detailed()` - Async, returns full Response
- `asyncio()` - Async, returns parsed data only

Example from `api/product/get_all_products.py`:

```python
# Synchronous
def sync_detailed(...) -> Response[ProductListResponse]:
    """List all products (sync)."""
    ...

def sync(...) -> ProductListResponse | None:
    """List all products (sync, parsed only)."""
    ...

# Asynchronous
async def asyncio_detailed(...) -> Response[ProductListResponse]:
    """List all products (async)."""
    ...

async def asyncio(...) -> ProductListResponse | None:
    """List all products (async, parsed only)."""
    ...
```

Users choose based on their needs:

```python
# Async application (recommended for web servers)
async def main():
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)
        products = response.parsed.data

# Sync application (scripts, notebooks)
def main():
    with KatanaClient() as client:
        response = get_all_products.sync_detailed(client=client)
        products = response.parsed.data
```

## Consequences

### Positive Consequences

1. **Universal Compatibility**: Works in any Python environment
1. **User Choice**: Users pick what fits their architecture
1. **No Migration Required**: Can start sync, move to async later
1. **REPL/Notebook Friendly**: Sync works in interactive environments
1. **Script Friendly**: No async complexity for simple scripts
1. **Performance When Needed**: Async available for concurrent operations
1. **Complete**: Both APIs have same functionality

### Negative Consequences

1. **Larger Codebase**: 2× the endpoint methods (~500 methods total)
1. **Maintenance**: Need to ensure both work correctly
1. **Documentation**: Must document both patterns
1. **Choice Paralysis**: New users may not know which to use

### Neutral Consequences

1. **Generated Code**: Generator handles both automatically
1. **Testing**: Need tests for both sync and async paths

## Alternatives Considered

### Alternative 1: Async Only

Provide only async API:

```python
async def main():
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)
```

**Pros:**

- Smaller codebase
- Forces modern async patterns
- Better performance potential
- Simpler to maintain

**Cons:**

- Doesn't work in notebooks/REPL
- Complex for simple scripts
- Requires async knowledge
- Excludes sync-only users

**Why Rejected:** Too limiting, excludes valid use cases.

### Alternative 2: Sync Only

Provide only sync API:

```python
def main():
    with KatanaClient() as client:
        response = get_all_products.sync_detailed(client=client)
```

**Pros:**

- Simpler for beginners
- Works everywhere
- No async complexity
- Smaller codebase

**Cons:**

- Can't leverage async performance
- Doesn't fit modern async applications
- Poor performance for concurrent operations
- Not future-proof

**Why Rejected:** Limits performance, not modern.

### Alternative 3: Sync with Async Wrapper

Provide sync API, users can wrap in async:

```python
import asyncio

async def async_wrapper():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: get_all_products.sync_detailed(client=client)
    )
```

**Pros:**

- One codebase (sync)
- Can "fake" async

**Cons:**

- Not true async (no concurrency benefit)
- Complex boilerplate for users
- Poor performance
- Misleading API

**Why Rejected:** Fake async is worse than true async or sync.

## Usage Guidance

### When to Use Async

✅ Use async when:

- Building web servers (FastAPI, Sanic, etc.)
- Need concurrent operations (multiple API calls in parallel)
- Application is already async
- Performance is critical

Example:

```python
# Concurrent requests (much faster than sync)
async with KatanaClient() as client:
    products_task = get_all_products.asyncio_detailed(client=client)
    orders_task = get_all_sales_orders.asyncio_detailed(client=client)

    products, orders = await asyncio.gather(products_task, orders_task)
```

### When to Use Sync

✅ Use sync when:

- Writing scripts or CLI tools
- Working in Jupyter notebooks
- Learning the API
- Application is synchronous
- Simplicity is more important than performance

Example:

```python
# Simple script
with KatanaClient() as client:
    response = get_all_products.sync_detailed(client=client)
    for product in response.parsed.data:
        print(product.name)
```

## Implementation Details

### Both APIs Get Same Features

Resilience features work for both:

- ✅ Automatic retries
- ✅ Rate limit handling
- ✅ Auto-pagination
- ✅ Error handling

### Transport Layer Handles Both

`KatanaClient` provides both sync and async transports:

```python
class KatanaClient(AuthenticatedClient):
    def __init__(self, **kwargs):
        # Async transport (default)
        async_transport = ResilientAsyncTransport.create(...)

        # Sync transport (also available)
        sync_transport = ResilientSyncTransport.create(...)

        super().__init__(
            transport=sync_transport,
            async_transport=async_transport,
            **kwargs
        )
```

### Examples Provided

Both patterns documented:

- `examples/basic_usage.py` - Async examples
- `examples/sync_usage.py` - Sync examples

## References

- [httpx Async Support](https://www.python-httpx.org/async/)
- [examples/basic_usage.py](../../examples/basic_usage.py)
- [examples/sync_usage.py](../../examples/sync_usage.py)
- [REVISED_ASSESSMENT.md](../REVISED_ASSESSMENT.md#sync-api)
