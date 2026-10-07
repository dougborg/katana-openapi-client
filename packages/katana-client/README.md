# katana-openapi-client

[![npm](https://img.shields.io/npm/v/katana-openapi-client.svg)](https://www.npmjs.com/package/katana-openapi-client)

TypeScript/JavaScript client for the
[Katana Manufacturing ERP API](https://katanamrp.com/) with automatic resilience
features.

## Features

- **Automatic Retries** - Exponential backoff with jitter, `Retry-After` aware
  (delta-seconds and HTTP-date), idempotency-safe method rules
- **Proactive Rate Limiting** - Token bucket that adapts to `X-Ratelimit-*` headers
- **Timeouts & Cancellation** - Per-attempt timeout plus `AbortSignal` support
- **Auto-Pagination** - Automatically collects all pages for GET requests
- **Same behaviour for every endpoint** - Resilience lives in the fetch layer, so
  `client.fetch()` and every generated SDK function get it automatically
- **Type Safety** - Full TypeScript types generated from OpenAPI spec
- **Browser & Node.js** - Works in both environments
- **Tree-Shakeable** - Only import what you need

## Installation

```bash
npm install katana-openapi-client
# or
pnpm add katana-openapi-client
# or
yarn add katana-openapi-client
```

## Development

The package is managed by [pnpm](https://pnpm.io); the exact pnpm version is pinned by
`packageManager` in `package.json`, and pnpm 10+ switches itself to that pin
automatically, so any reasonably recent global pnpm works. From the repository root:

```bash
npm install --global pnpm
pnpm --dir packages/katana-client install --frozen-lockfile
```

Run development tasks from the repository root using the package-local scripts:

```bash
pnpm --dir packages/katana-client run generate
pnpm --dir packages/katana-client run lint
pnpm --dir packages/katana-client run typecheck
pnpm --dir packages/katana-client test
pnpm --dir packages/katana-client run build
```

## Quick Start

```typescript
import { KatanaClient } from 'katana-openapi-client';

// Create client with API key
const client = await KatanaClient.create({
  apiKey: 'your-api-key',
});

// Or use environment variable (KATANA_API_KEY)
const client = await KatanaClient.create();

// Or provide API key directly
const client = KatanaClient.withApiKey('your-api-key');

// Make requests - auto-pagination collects all pages
const response = await client.get('/products');
const { data } = await response.json();
console.log(`Found ${data.length} products`);
```

## Types-Only Import

If you only need TypeScript types without any runtime code:

```typescript
import type { Product, SalesOrder, Variant } from 'katana-openapi-client/types';

function processProduct(product: Product) {
  // ...
}
```

## Configuration

```typescript
const client = await KatanaClient.create({
  // API key (or set KATANA_API_KEY env var)
  apiKey: 'your-api-key',

  // Custom base URL (default: https://api.katanamrp.com/v1)
  baseUrl: 'https://api.katanamrp.com/v1',

  // Per-attempt timeout in ms (default: 30000; null disables)
  timeoutMs: 30_000,

  // Proactive rate limit (default: 60 req/min; null disables)
  requestsPerMinute: 60,

  // Retry configuration
  retry: {
    maxRetries: 5,           // Default: 5
    backoffFactor: 1.0,      // Default: 1.0 -> waits up to 2s, 4s, 8s, 16s, 32s
    backoffJitter: 1.0,      // Default: 1.0 (full jitter; 0 = deterministic)
    maxBackoffSeconds: 120,  // Default: 120 (caps backoff and Retry-After)
    respectRetryAfter: true, // Default: true
  },

  // Pagination configuration
  pagination: {
    maxPages: 100,           // Default: 100
    maxItems: undefined,     // Limit total items (optional)
    defaultPageSize: 250,    // Default: 250
  },

  // Disable auto-pagination globally
  autoPagination: false,

  // Optional logger (e.g. console): retry, rate-limit and pagination events,
  // plus an error entry for every 4xx response except 429
  logger: console,
});
```

## Retry Behavior

The client implements the same retry strategy as the Python client:

| Status / failure                    | GET/HEAD/PUT/DELETE/OPTIONS/TRACE | POST/PATCH |
| ----------------------------------- | --------------------------------- | ---------- |
| 429 (Rate Limit)                    | Retry                             | Retry      |
| 502, 503, 504                       | Retry                             | No Retry   |
| Other 4xx / 5xx                     | No Retry                          | No Retry   |
| Network error / per-attempt timeout | Retry                             | Retry      |
| Caller abort (`signal`)             | No Retry                          | No Retry   |

**Key behavior**: POST and PATCH requests are retried for rate limiting (429) because
rate limits are transient and don't indicate idempotency issues.

**Delays**: the n-th retry waits up to `backoffFactor * 2^n` seconds (full jitter), or
the server's `Retry-After` (delta-seconds or HTTP-date) when present — both capped at
`maxBackoffSeconds`. When retries are exhausted the last response is returned (or the
last network error thrown).

**Timeouts & cancellation**: each attempt is aborted after `timeoutMs` (time to response
headers) and retried. Pass `signal` to cancel: backoff and rate-limit waits stop
immediately and an aborted request is never retried.

```typescript
const controller = new AbortController();
const response = await client.fetch('/products', { signal: controller.signal });
```

## Proactive Rate Limiting

Beyond reactive 429 retries, the client **proactively paces** outgoing requests through
a token bucket (60 req/min by default) and adapts to Katana's `X-Ratelimit-*` headers:

- **Sync down** — if the server reports fewer remaining requests than expected (e.g.
  another client sharing the API key), the local budget drains to match. It never syncs
  up; the server is authoritative on the lower bound only.
- **Reset gate** — when `X-Ratelimit-Remaining` hits `0`, all requests block until
  `X-Ratelimit-Reset` elapses, so the client doesn't fire into an exhausted window.

The limiter sits innermost in the fetch chain, so each retry attempt and each paginated
page consumes one token — matching how Katana counts requests server-side.

```typescript
// Tune the budget
const client = await KatanaClient.create({ requestsPerMinute: 120 });

// Disable proactive limiting (reactive 429 retry still applies)
const client = await KatanaClient.create({ requestsPerMinute: null });
```

This mirrors the Python client's `RateLimitTransport`.

## Auto-Pagination

Auto-pagination is **ON by default** for all GET requests:

```typescript
// Collects all pages automatically
const response = await client.get('/products');
const { data, pagination } = await response.json();
console.log(`Collected ${pagination.total_items} items from ${pagination.collected_pages} pages`);
```

To disable auto-pagination:

```typescript
// Explicit page parameter disables auto-pagination
const response = await client.get('/products', { page: 2, limit: 50 });

// Or per request (third argument) / globally via configuration
const firstPage = await client.get('/products', undefined, { autoPagination: false });
const first200 = await client.get('/products', undefined, { maxItems: 200 });
const client = await KatanaClient.create({
  autoPagination: false,
});

// Per-call overrides for generated SDK functions
const { data } = await getAllProducts({
  client: client.sdk,
  fetch: client.fetchWith({ maxItems: 200 }),
});
```

Responses without pagination metadata (e.g. `GET /products/{id}`) are returned
untouched, and endpoints that return a bare JSON array keep that shape.

## Error Handling

The client returns standard `Response` objects. Use `parseError` for typed error
handling:

```typescript
import {
  KatanaClient,
  parseError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
} from 'katana-openapi-client';

const response = await client.post('/products', { name: 'Widget' });

if (!response.ok) {
  const body = await response.json();
  const error = parseError(response, body);

  if (error instanceof AuthenticationError) {
    console.error('Invalid API key');
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter}s`);
  } else if (error instanceof ValidationError) {
    // `error.message` is a human-readable, multi-line summary; `error.details`
    // is the structured Ajv error array exactly as Katana sends it.
    console.error(error.message);
    console.error(error.details);
    // [{ path: '/name', code: 'required', message: '...', info: { missingProperty: 'name' } }]
  } else {
    console.error(`Error ${error.statusCode}: ${error.message}`);
  }
}
```

Available error classes:

- `AuthenticationError` (401)
- `RateLimitError` (429) - includes `retryAfter` seconds
- `ValidationError` (422) - includes `details`, the Ajv-style validation error array
  (`{ path, code, message, info }` per item, where `code` is the failed Ajv keyword).
  `message` is a formatted, multi-line summary mirroring the Python client's wording.
- `ServerError` (5xx)
- `NetworkError` - connection failures
- `KatanaError` - base class for all errors

The catch-all path also surfaces messages from Katana's nested `{ "error": { ... } }`
envelope, including for undocumented status codes.

## HTTP Methods

```typescript
// GET (auto-paginated by default)
const products = await client.get('/products');
const productById = await client.get('/products/123');
const filtered = await client.get('/products', { category: 'widgets' });

// POST
const created = await client.post('/products', {
  name: 'New Product',
  sku: 'PROD-001',
});

// PUT
const updated = await client.put('/products/123', {
  name: 'Updated Product',
});

// PATCH
const patched = await client.patch('/products/123', {
  name: 'Patched Name',
});

// DELETE
const deleted = await client.delete('/products/123');
```

## Advanced: Generated SDK

The package exports generated SDK functions with full TypeScript types. You can use them
with the resilient client:

```typescript
import { KatanaClient, getAllProducts, createProduct } from 'katana-openapi-client';

// Create the resilient client
const katana = await KatanaClient.create();

// Use SDK functions with the resilient client
const { data, error } = await getAllProducts({ client: katana.sdk });
if (data) {
  console.log(`Found ${data.length} products`);
}

// Or use the config shorthand
const result = await getAllProducts(katana.getConfig());
```

The SDK functions provide:

- Full TypeScript types for all request/response bodies
- Auto-completion for query parameters
- Type-safe error handling

## Environment Variables

- `KATANA_API_KEY` - API key for authentication
- `KATANA_BASE_URL` - Override the base URL (optional)

### Loading from .env files

**Node.js 20.6+** (recommended):

```bash
node --env-file=.env your-script.js
```

**Node.js 20.0-20.5** (use dotenv):

```bash
npm install dotenv
```

```typescript
import 'dotenv/config';
import { KatanaClient } from 'katana-openapi-client';

const client = KatanaClient.withApiKey(process.env.KATANA_API_KEY!);
```

> **Note**: This library supports Node.js 20+ (and browsers) but does not bundle dotenv.
> If you need .env file loading on Node.js < 20.6, install dotenv as a direct dependency
> in your project.

## Documentation

For more detailed documentation:

- **[Client Guide](docs/guide.md)** - Comprehensive usage guide
- **[Cookbook](docs/cookbook.md)** - Common patterns and recipes
- **[Testing Guide](docs/testing.md)** - Testing strategy and patterns
- **[Architecture Decisions](docs/adr/README.md)** - Design decisions and rationale

## License

MIT
