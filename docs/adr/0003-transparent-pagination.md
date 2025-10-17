# ADR-003: Transparent Automatic Pagination

## Status

Accepted

Date: 2024-08-13 (estimated based on transport implementation)

## Context

The Katana API uses cursor-based pagination with Link headers:

- Default page size: 50 items
- Maximum page size: 250 items
- Link header provides `next` URL for additional pages
- Many resources have hundreds or thousands of items

Users need to fetch all items efficiently. Pagination strategies include:

1. **Manual Pagination**: User handles `page` parameter and loops
1. **Iterator Pattern**: Provide async iterator that yields pages
1. **Explicit Pagination Helper**: `client.paginate(endpoint, ...)`
1. **Transparent Pagination**: Automatically fetch all pages, return complete list

Considerations:

- Most use cases need all items, not just first page
- Manual pagination is error-prone
- Should work automatically without user code changes
- Need safety limits to prevent infinite loops
- Must be opt-out (users can get single page if needed)

## Decision

We will implement **transparent automatic pagination** at the transport layer.

When a paginated endpoint is called:

1. Fetch first page (default limit: 50)
1. Check for `Link` header with `rel="next"`
1. Automatically fetch additional pages
1. Aggregate results into single response
1. Respect safety limit (max 100 pages = 5,000-25,000 items)
1. Return complete dataset transparently

Implementation in `AutoPaginationTransport`:

```python
class AutoPaginationTransport(AsyncHTTPTransport):
    async def handle_async_request(self, request):
        # Fetch first page
        response = await super().handle_async_request(request)

        # Check if endpoint supports pagination
        if not self._should_paginate(request, response):
            return response

        # Auto-fetch additional pages
        all_data = [response]
        next_url = self._get_next_url(response)

        while next_url and len(all_data) < max_pages:
            next_response = await self._fetch_page(next_url)
            all_data.append(next_response)
            next_url = self._get_next_url(next_response)

        # Aggregate and return
        return self._aggregate_responses(all_data)
```

Users can still get single page by specifying `page` parameter:

```python
# Automatic pagination (gets all pages)
response = await get_all_products.asyncio_detailed(client=client)

# Single page (manual pagination)
response = await get_all_products.asyncio_detailed(
    client=client,
    page=1,
    limit=50
)
```

## Consequences

### Positive Consequences

1. **Zero Boilerplate**: No pagination loops in user code
1. **Complete Data**: Always get all items by default
1. **Consistent Behavior**: Works same for all paginated endpoints
1. **Transparent**: Users don't think about pagination
1. **Safety Limits**: Prevents infinite loops
1. **Opt-Out Available**: Can get single page if needed
1. **Efficient**: Single logical operation
1. **Error Handling**: Handles pagination errors automatically

### Negative Consequences

1. **Implicit Behavior**: Not obvious pagination is happening
1. **Memory Usage**: Loads all items in memory
1. **Latency**: Multiple requests increase response time
1. **Rate Limiting**: Multiple requests count toward rate limit
1. **Debugging**: Harder to see individual page requests
1. **Breaking Expectations**: Some users expect single page

### Neutral Consequences

1. **Safety Limit**: Max 100 pages (reasonable for most use cases)
1. **Performance**: Trade latency for completeness
1. **Network Traffic**: More requests but complete data

## Alternatives Considered

### Alternative 1: Manual Pagination

Users handle pagination explicitly:

```python
page = 1
all_products = []
while True:
    response = await get_all_products.asyncio_detailed(
        client=client,
        page=page,
        limit=50
    )
    products = response.parsed.data
    if not products:
        break
    all_products.extend(products)
    page += 1
```

**Pros:**

- Explicit and clear
- Full control over pagination
- Easy to understand

**Cons:**

- Boilerplate in every usage
- Error-prone (forget to increment page)
- Inconsistent (different users implement differently)
- Tedious for simple "get all" use case

**Why Rejected:** Too much boilerplate for common case.

### Alternative 2: Iterator Pattern

Provide async iterator:

```python
async for page in client.paginate(get_all_products):
    for product in page:
        process(product)
```

**Pros:**

- Explicit pagination
- Memory efficient (stream pages)
- Pythonic pattern

**Cons:**

- Still requires loop in user code
- Different API than direct calls
- Need to learn pagination API
- More complex for simple "get all"

**Why Rejected:** Adds API complexity, still requires user code changes.

### Alternative 3: Explicit Pagination Helper

```python
products = await client.fetch_all(get_all_products, limit=50)
```

**Pros:**

- Explicit "fetch all" intent
- Can have different method for single page
- Clear what's happening

**Cons:**

- Different API from direct calls
- Need to remember to use `fetch_all` vs direct call
- Inconsistent with generated API
- Extra method to learn

**Why Rejected:** Creates two ways to do everything, confusing API.

### Alternative 4: Page Size = Max by Default

Set default `limit=250` (API maximum):

**Pros:**

- Fewer requests
- Still single-page response
- Simple implementation

**Cons:**

- Still requires manual pagination for >250 items
- Wastes bandwidth if \<250 items
- Doesn't solve the fundamental problem

**Why Rejected:** Doesn't solve pagination problem, just reduces it.

## Implementation Details

### Pagination Detection

Auto-pagination only triggers when:

1. Response has `Link` header with `rel="next"`
1. User didn't specify explicit `page` parameter
1. Response is successful (2xx status)
1. Haven't hit safety limit (100 pages)

### Safety Limits

```python
MAX_PAGES = 100  # Default safety limit

# With default limit=50:  50 × 100 = 5,000 items max
# With limit=250:         250 × 100 = 25,000 items max
```

Users can override if needed:

```python
client = KatanaClient(max_pagination_pages=200)
```

### Response Aggregation

For list responses (e.g., `ProductListResponse`):

```python
# Merge all data arrays
aggregated_data = []
for response in all_responses:
    aggregated_data.extend(response.parsed.data)

# Return first response with aggregated data
final_response = all_responses[0]
final_response.parsed.data = aggregated_data
return final_response
```

### Opting Out

Get single page by specifying `page`:

```python
# Just first page
response = await get_all_products.asyncio_detailed(
    client=client,
    page=1
)

# Second page
response = await get_all_products.asyncio_detailed(
    client=client,
    page=2
)
```

## Observability

Pagination is logged at DEBUG level:

```python
logger.debug(f"Auto-pagination: Fetched page 1, found next page")
logger.debug(f"Auto-pagination: Fetched page 2, found next page")
logger.debug(f"Auto-pagination: Fetched page 3, no more pages")
logger.info(f"Auto-pagination: Fetched 3 pages, 127 total items")
```

## References

- [AutoPaginationTransport Implementation](../../katana_public_api_client/katana_client.py)
- [Katana API Pagination Documentation](https://help.katanamrp.com/api)
- [REVISED_ASSESSMENT.md](../REVISED_ASSESSMENT.md#transparent-pagination)
- Issue #31: Test coverage for pagination edge cases
