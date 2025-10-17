# ADR-001: Use Transport-Layer Resilience Pattern

## Status

Accepted

Date: 2024-08-13 (estimated based on git history)

## Context

API clients need resilience features like retries, rate limiting, and error handling.
Traditional approaches include:

1. **Decorator Pattern**: Wrap each API method with retry/rate-limit decorators
1. **Wrapper Classes**: Create wrapper classes around generated client
1. **Middleware Pattern**: Intercept requests/responses at application layer
1. **Transport-Layer Pattern**: Implement resilience at the HTTP transport layer

The generated API client has 248 endpoint modules with both sync and async variants. Any
solution needs to:

- Work with both sync and async code
- Not require modifying 248+ generated files
- Survive client regeneration
- Be maintainable and debuggable
- Have minimal performance overhead

## Decision

We will implement resilience at the **HTTP transport layer** using httpx's native
extension points.

Specifically:

- Use `httpx-retries` library for retry logic
- Create custom `RateLimitAwareRetry` class that distinguishes between 429 (rate limit)
  and 5xx errors
- Compose transport layers: `ResilientAsyncTransport` = `ErrorLoggingTransport` +
  `AutoPaginationTransport` + `RetryTransport`
- All API calls through `KatanaClient` automatically get resilience without any code
  changes

Implementation in [katana_client.py](../../katana_public_api_client/katana_client.py):

```python
class ResilientAsyncTransport:
    @staticmethod
    def create(...):
        # Layer 1: Base httpx transport
        base_transport = httpx.AsyncHTTPTransport(...)

        # Layer 2: Error logging
        error_transport = ErrorLoggingTransport(base_transport, logger)

        # Layer 3: Auto-pagination
        pagination_transport = AutoPaginationTransport(error_transport, ...)

        # Layer 4: Retry logic
        retry = RateLimitAwareRetry(
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST", "PATCH"]
        )
        resilient_transport = RetryTransport(pagination_transport, retry=retry)

        return resilient_transport
```

## Consequences

### Positive Consequences

1. **Zero Boilerplate**: Users call generated API methods directly, resilience is
   automatic
1. **Survives Regeneration**: Generated code never needs modification
1. **Consistent Behavior**: All endpoints get same resilience automatically
1. **Type Safety Preserved**: No wrapper layers breaking type hints
1. **Debuggable**: Clear separation of concerns, easy to trace
1. **Performance**: Minimal overhead, happens at transport layer
1. **httpx Native**: Uses standard httpx patterns, no custom protocols
1. **Composable**: Easy to add/remove transport layers

### Negative Consequences

1. **Abstraction**: Resilience is "magical" - happens automatically without visible code
1. **Learning Curve**: Need to understand httpx transport architecture
1. **Limited Customization**: Per-endpoint customization requires more complex patterns
1. **Testing**: Need to mock at transport layer, not method level

### Neutral Consequences

1. **Dependency on httpx-retries**: External library for retry logic
1. **Transport Layers**: Multiple layers of wrapping (but this is standard httpx
   pattern)

## Alternatives Considered

### Alternative 1: Decorator Pattern

```python
@retry(max_attempts=5)
@rate_limit(calls=60, period=60)
async def get_all_products(...):
    # API call
```

**Pros:**

- Explicit and visible
- Easy to customize per endpoint
- Well-known pattern

**Cons:**

- Need to decorate 248+ generated methods
- Breaks on regeneration
- Violates DRY principle
- Harder to maintain consistency

**Why Rejected:** Doesn't survive client regeneration, too much boilerplate.

### Alternative 2: Wrapper Classes

```python
class ResilientProductAPI:
    def __init__(self, client):
        self._client = client

    async def get_all_products(self, **kwargs):
        return await retry_with_backoff(
            lambda: get_all_products.asyncio_detailed(client=self._client, **kwargs)
        )
```

**Pros:**

- Explicit control
- Easy to understand
- Can customize per resource

**Cons:**

- Need to maintain 248+ wrapper methods
- Type hints break
- Extra layer of indirection
- Doesn't survive API changes

**Why Rejected:** Too much manual maintenance, breaks type safety.

### Alternative 3: Middleware Pattern

```python
class RetryMiddleware:
    async def __call__(self, request, call_next):
        # Retry logic
        return await call_next(request)
```

**Pros:**

- Clean separation
- Works with any HTTP client

**Cons:**

- httpx doesn't have middleware concept (has transports instead)
- Would require implementing custom middleware system
- More complex than using native httpx features

**Why Rejected:** Reinventing httpx transports, not using native patterns.

## References

- [httpx Transports Documentation](https://www.python-httpx.org/advanced/#custom-transports)
- [httpx-retries Library](https://github.com/karpetrosyan/httpx-retries)
- [katana_client.py Implementation](../../katana_public_api_client/katana_client.py)
- [REVISED_ASSESSMENT.md](../REVISED_ASSESSMENT.md)
- Issue #31: Improve Test Coverage for Core Logic
