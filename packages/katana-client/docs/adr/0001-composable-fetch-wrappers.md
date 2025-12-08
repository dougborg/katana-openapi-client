# ADR-TS-001: Composable Fetch Wrappers

## Status

Accepted

## Context

The TypeScript client needs to provide the same resilience features as the Python
client:

- Automatic retries with exponential backoff
- Rate limiting awareness (429 handling)
- Auto-pagination for GET requests
- Authentication header injection

The Python client achieves this through httpx's transport layer (a class-based
approach). TypeScript doesn't have a direct equivalent, and we need a pattern that:

1. Works with the native `fetch` API
1. Is composable and testable
1. Integrates with generated SDK code
1. Works in both Node.js and browser environments

### Options Considered

1. **Class-based transport wrapper**: Similar to Python, create classes that wrap fetch
1. **Middleware pattern**: Use a chain of middleware functions
1. **Composable fetch wrappers**: Higher-order functions that wrap fetch
1. **Proxy-based interception**: Use Proxy to intercept fetch calls

## Decision

Use **composable fetch wrappers** - higher-order functions that take a fetch function
and return a new fetch function with added behavior.

```typescript
// Each wrapper adds one capability
const fetchWithRetry = createResilientFetch({ baseFetch: fetch });
const fetchWithPagination = createPaginatedFetch(fetchWithRetry);
const fetchWithAuth = createAuthenticatedFetch(fetchWithPagination, apiKey);
```

The wrappers are composed in a specific order:

1. **Base fetch** (globalThis.fetch or custom)
1. **Retry wrapper** (handles retries with exponential backoff)
1. **Pagination wrapper** (collects all pages for GET requests)
1. **Authentication wrapper** (adds Authorization header)

### Architecture

```
User Request
     │
     ▼
┌─────────────────────┐
│ Authentication      │ ← Adds Bearer token
│ Wrapper             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Pagination          │ ← Collects all pages (GET only)
│ Wrapper             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Retry               │ ← Handles retries with backoff
│ Wrapper             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Base Fetch          │ ← globalThis.fetch or custom
│                     │
└─────────────────────┘
```

## Consequences

### Positive

- **Simple composition**: Each wrapper has a single responsibility
- **Easy testing**: Each wrapper can be tested in isolation
- **Custom fetch support**: Users can provide their own base fetch
- **Framework agnostic**: Works with any framework that supports fetch
- **Browser compatible**: Uses standard fetch API
- **Type safe**: Full TypeScript support with generics

### Negative

- **Order matters**: Wrappers must be composed in the correct order
- **No shared state**: Each request is independent (no connection pooling)
- **Debugging complexity**: Stack of wrappers can make debugging harder

### Neutral

- **Different from Python**: The pattern differs from Python's transport layer approach,
  but achieves the same goals
- **No class hierarchy**: Uses functions instead of classes, which is idiomatic for
  TypeScript/JavaScript

## Implementation Notes

### Wrapper Interface

Each wrapper follows this pattern:

```typescript
type FetchWrapper = (
  baseFetch: typeof fetch,
  options: WrapperOptions
) => typeof fetch;
```

### Example: Retry Wrapper

```typescript
export function createResilientFetch(options: ResilientFetchOptions = {}): typeof fetch {
  const config = { ...DEFAULT_RETRY_CONFIG, ...options.retry };
  const baseFetch = options.baseFetch ?? globalThis.fetch;

  return async (input, init) => {
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const response = await baseFetch(input, init);
        if (response.ok || !shouldRetry(init?.method, response.status, config)) {
          return response;
        }
        await sleep(calculateRetryDelay(attempt, config, response));
      } catch (error) {
        if (attempt === config.maxRetries) throw error;
        await sleep(calculateRetryDelay(attempt, config));
      }
    }
    throw new Error('Max retries exceeded');
  };
}
```

## Related

- [Python ADR-001: Transport-Layer Resilience](../../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)
- [Python ADR-003: Transparent Pagination](../../../katana_public_api_client/docs/adr/0003-transparent-pagination.md)
