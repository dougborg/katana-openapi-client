# katana-openapi-client

TypeScript/JavaScript client for the
[Katana Manufacturing ERP API](https://katanamrp.com/) with automatic resilience
features.

## Features

- **Automatic Retries** - Exponential backoff with configurable retry limits
- **Rate Limiting Awareness** - Respects 429 responses and `Retry-After` headers
- **Auto-Pagination** - Automatically collects all pages for GET requests
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

  // Retry configuration
  retry: {
    maxRetries: 5,           // Default: 5
    backoffFactor: 1.0,      // Default: 1.0 (1s, 2s, 4s, 8s, 16s)
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
});
```

## Retry Behavior

The client implements the same retry strategy as the Python client:

| Status Code      | GET/PUT/DELETE | POST/PATCH |
| ---------------- | -------------- | ---------- |
| 429 (Rate Limit) | Retry          | Retry      |
| 502, 503, 504    | Retry          | No Retry   |
| Other 4xx        | No Retry       | No Retry   |
| Network Error    | Retry          | Retry      |

**Key behavior**: POST and PATCH requests are retried for rate limiting (429) because
rate limits are transient and don't indicate idempotency issues.

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

// Or globally via configuration
const client = await KatanaClient.create({
  autoPagination: false,
});
```

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
    console.error('Validation errors:', error.details);
    // [{ field: 'name', message: 'Required', code: 'missing' }]
  } else {
    console.error(`Error ${error.statusCode}: ${error.message}`);
  }
}
```

Available error classes:

- `AuthenticationError` (401)
- `RateLimitError` (429) - includes `retryAfter` seconds
- `ValidationError` (422) - includes `details` array
- `ServerError` (5xx)
- `NetworkError` - connection failures
- `KatanaError` - base class for all errors

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

**Node.js 18-20.5** (use dotenv):

```bash
npm install dotenv
```

```typescript
import 'dotenv/config';
import { KatanaClient } from 'katana-openapi-client';

const client = KatanaClient.withApiKey(process.env.KATANA_API_KEY!);
```

> **Note**: This library supports Node.js 18+ but does not bundle dotenv. If you need
> .env file loading on Node.js < 20.6, install dotenv as a direct dependency in your
> project.

## Documentation

For more detailed documentation:

- **[Client Guide](docs/guide.md)** - Comprehensive usage guide
- **[Cookbook](docs/cookbook.md)** - Common patterns and recipes
- **[Testing Guide](docs/testing.md)** - Testing strategy and patterns
- **[Architecture Decisions](docs/adr/README.md)** - Design decisions and rationale

## License

MIT
