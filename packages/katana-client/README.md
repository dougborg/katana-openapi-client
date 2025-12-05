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

```typescript
import {
  KatanaClient,
  KatanaError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError,
} from 'katana-openapi-client';

try {
  const response = await client.post('/products', { name: 'Widget' });
  if (!response.ok) {
    const error = await response.json();
    console.error('API error:', error);
  }
} catch (error) {
  if (error instanceof NetworkError) {
    console.error('Network error - check your connection');
  }
}
```

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

The package also exports the generated SDK functions for direct API access:

```typescript
import { getProducts, createProduct } from 'katana-openapi-client';

// Note: These use the default client configuration
// For custom configuration, use KatanaClient instead
```

## Environment Variables

- `KATANA_API_KEY` - API key for authentication
- `KATANA_BASE_URL` - Override the base URL (optional)

## License

MIT
