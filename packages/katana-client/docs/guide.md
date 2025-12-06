# KatanaClient Guide (TypeScript)

The **KatanaClient** is the TypeScript/JavaScript client for the Katana Manufacturing
ERP API. It provides automatic resilience (retries, rate limiting, error handling) with
a simple fetch-based interface.

## Key Features

- **Automatic Resilience**: Transport-layer retries and rate limiting
- **Zero Configuration**: Works out of the box with environment variables
- **Complete Type Safety**: Full TypeScript types from OpenAPI spec
- **Smart Pagination**: Built-in auto-pagination with safety limits
- **Browser & Node.js**: Works in both environments
- **Tree-Shakeable**: Only import what you need

## Quick Start

### Installation

```bash
npm install katana-openapi-client
# or
pnpm add katana-openapi-client
# or
yarn add katana-openapi-client
```

### Basic Usage

```typescript
import { KatanaClient } from 'katana-openapi-client';

// Create client with API key
const client = KatanaClient.withApiKey('your-api-key');

// Make a request - auto-pagination collects all pages
const response = await client.get('/products');
const { data, pagination } = await response.json();
console.log(`Found ${data.length} products across ${pagination.collected_pages} pages`);
```

### Using Environment Variables

```typescript
// Automatically loads from KATANA_API_KEY environment variable
const client = await KatanaClient.create();

// Or use Node.js 20.6+ native .env support
// node --env-file=.env your-script.js
```

## Authentication

The client supports multiple authentication methods (in priority order):

1. **Direct parameter**: Pass `apiKey` to constructor
1. **Environment variable**: Set `KATANA_API_KEY`

### Using API Key Directly

```typescript
// Synchronous creation with explicit API key
const client = KatanaClient.withApiKey('your-api-key');

// Async creation (also checks environment)
const client = await KatanaClient.create({ apiKey: 'your-api-key' });
```

### Using Environment Variables

```bash
# Set environment variable
export KATANA_API_KEY=your-api-key-here

# Or use .env file with Node.js 20.6+
node --env-file=.env your-script.js
```

```typescript
// Automatically picks up from environment
const client = await KatanaClient.create();
```

### Node.js 18-20.5 (dotenv)

For older Node.js versions, use dotenv:

```bash
npm install dotenv
```

```typescript
import 'dotenv/config';
import { KatanaClient } from 'katana-openapi-client';

const client = KatanaClient.withApiKey(process.env.KATANA_API_KEY!);
```

## Automatic Resilience

Every API call through `KatanaClient` automatically includes retry logic:

### Smart Retries

| Status Code      | GET/PUT/DELETE | POST/PATCH |
| ---------------- | -------------- | ---------- |
| 429 (Rate Limit) | Retry          | Retry      |
| 502, 503, 504    | Retry          | No Retry   |
| Other 4xx        | No Retry       | No Retry   |
| Network Error    | Retry          | Retry      |

**Key behavior**: POST and PATCH requests are retried for rate limiting (429) because
rate limits are transient and don't indicate idempotency issues.

### Retry Configuration

```typescript
const client = KatanaClient.withApiKey('your-api-key', {
  retry: {
    maxRetries: 5, // Default: 5
    backoffFactor: 1.0, // Default: 1.0 (1s, 2s, 4s, 8s, 16s)
    respectRetryAfter: true, // Default: true
  },
});
```

### Exponential Backoff

Retry delays follow exponential backoff:

- Attempt 0: 1 second
- Attempt 1: 2 seconds
- Attempt 2: 4 seconds
- Attempt 3: 8 seconds
- Attempt 4: 16 seconds

The client also respects the `Retry-After` header when present.

## Auto-Pagination

Auto-pagination is **ON by default** for all GET requests. All pages are automatically
collected into a single response.

### Automatic Collection (Default)

```typescript
const client = KatanaClient.withApiKey('your-api-key');

// Get ALL products across all pages automatically
const response = await client.get('/products');
const { data, pagination } = await response.json();

console.log(`Total products: ${data.length}`);
console.log(`Collected from ${pagination.collected_pages} pages`);
```

### Single Page Request

To get a specific page, add an explicit `page` parameter. **Note:** ANY explicit page
value (including `page=1`) disables auto-pagination:

```typescript
// Get ONLY page 2 (auto-pagination disabled)
const response = await client.get('/products', { page: 2, limit: 50 });
const { data } = await response.json();
// Returns just the items on page 2

// page=1 ALSO disables auto-pagination
const firstPage = await client.get('/products', { page: 1, limit: 50 });
// Returns only the first page, not all pages
```

### Limiting Results

```typescript
const client = KatanaClient.withApiKey('your-api-key', {
  pagination: {
    maxPages: 100, // Default: 100
    maxItems: 1000, // Limit total items (optional)
    defaultPageSize: 250, // Default: 250 (Katana API max)
  },
});
```

### Disabling Auto-Pagination

```typescript
// Disable globally
const client = KatanaClient.withApiKey('your-api-key', {
  autoPagination: false,
});

// Or per-request with explicit page parameter
const response = await client.get('/products', { page: 1 });
```

### Pagination Behavior Summary

| Parameter               | Scope  | Effect                                            |
| ----------------------- | ------ | ------------------------------------------------- |
| `limit: 50`             | Query  | Page size (50 items per request)                  |
| `page: 2`               | Query  | Get specific page only (disables auto-pagination) |
| `pagination.maxPages`   | Client | Max pages to fetch                                |
| `pagination.maxItems`   | Client | Max total items to collect                        |
| `autoPagination: false` | Client | Disable auto-pagination globally                  |

## HTTP Methods

### GET Requests

```typescript
// Simple GET (auto-paginated)
const products = await client.get('/products');

// GET with query parameters
const filtered = await client.get('/products', {
  category: 'widgets',
  is_sellable: true
});

// GET specific resource
const product = await client.get('/products/123');
```

### POST Requests

```typescript
const response = await client.post('/products', {
  name: 'New Product',
  sku: 'PROD-001',
  is_sellable: true,
});
const created = await response.json();
```

### PUT Requests

```typescript
const response = await client.put('/products/123', {
  name: 'Updated Product',
  sku: 'PROD-001',
});
```

### PATCH Requests

```typescript
const response = await client.patch('/products/123', {
  name: 'Patched Name',
});
```

### DELETE Requests

```typescript
const response = await client.delete('/products/123');
```

### Raw Fetch

For full control, use the `fetch` method directly:

```typescript
const response = await client.fetch('/products', {
  method: 'POST',
  body: JSON.stringify({ name: 'Product' }),
  headers: {
    'X-Custom-Header': 'value',
  },
});
```

## Error Handling

The client provides typed error classes for common API errors:

```typescript
import {
  KatanaClient,
  parseError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError,
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
  } else if (error instanceof ServerError) {
    console.error(`Server error: ${error.statusCode}`);
  } else {
    console.error(`Error ${error.statusCode}: ${error.message}`);
  }
}
```

### Error Classes

| Class                 | Status | Description                |
| --------------------- | ------ | -------------------------- |
| `AuthenticationError` | 401    | Invalid or missing API key |
| `RateLimitError`      | 429    | Rate limit exceeded        |
| `ValidationError`     | 422    | Request validation failed  |
| `ServerError`         | 5xx    | Server-side error          |
| `NetworkError`        | N/A    | Connection failure         |
| `KatanaError`         | Other  | Base class for all errors  |

## Generated SDK Functions

The package exports generated SDK functions with full TypeScript types:

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

### SDK Benefits

- Full TypeScript types for all request/response bodies
- Auto-completion for query parameters
- Type-safe error handling
- Generated from OpenAPI specification

## Configuration Reference

### Complete Options

```typescript
interface KatanaClientOptions {
  // API key for authentication
  apiKey?: string;

  // Base URL (default: 'https://api.katanamrp.com/v1')
  baseUrl?: string;

  // Retry configuration
  retry?: {
    maxRetries?: number;        // Default: 5
    backoffFactor?: number;     // Default: 1.0
    retryStatusCodes?: number[]; // Default: [429, 502, 503, 504]
    respectRetryAfter?: boolean; // Default: true
  };

  // Pagination configuration
  pagination?: {
    maxPages?: number;     // Default: 100
    maxItems?: number;     // Default: undefined (unlimited)
    defaultPageSize?: number; // Default: 250
  };

  // Enable/disable auto-pagination (default: true)
  autoPagination?: boolean;

  // Custom fetch function
  fetch?: typeof fetch;

  // Logger for debugging
  logger?: {
    debug: (message: string, ...args: unknown[]) => void;
    info: (message: string, ...args: unknown[]) => void;
    warn: (message: string, ...args: unknown[]) => void;
    error: (message: string, ...args: unknown[]) => void;
  };
}
```

### Example Configuration

```typescript
const client = await KatanaClient.create({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.katanamrp.com/v1',
  retry: {
    maxRetries: 3,
    backoffFactor: 0.5,
  },
  pagination: {
    maxPages: 50,
    maxItems: 500,
  },
  logger: console,
});
```

## Best Practices

### 1. Use Environment Variables

```typescript
// ✅ Good: API key from environment
const client = await KatanaClient.create();

// ❌ Bad: Hardcoded API key
const client = KatanaClient.withApiKey('sk-12345...');
```

### 2. Reuse Client Instances

```typescript
// ✅ Good: One client for multiple operations
const client = await KatanaClient.create();
const products = await client.get('/products');
const orders = await client.get('/sales_orders');

// ❌ Bad: New client for each request
const products = await (await KatanaClient.create()).get('/products');
const orders = await (await KatanaClient.create()).get('/sales_orders');
```

### 3. Handle Errors Appropriately

```typescript
// ✅ Good: Check response status
const response = await client.post('/products', data);
if (!response.ok) {
  const body = await response.json();
  const error = parseError(response, body);
  // Handle error appropriately
}

// ❌ Bad: Assume success
const { data } = await (await client.post('/products', data)).json();
```

### 4. Let Auto-Pagination Handle Large Datasets

```typescript
// ✅ Good: Auto-pagination with safety limits
const client = KatanaClient.withApiKey(apiKey, {
  pagination: { maxItems: 10000 },
});
const response = await client.get('/products');

// ❌ Bad: Manual pagination without limits
let page = 1;
while (true) {
  // Could run forever!
  const response = await client.get('/products', { page });
  page++;
}
```

### 5. Configure Appropriate Timeouts

```typescript
// ✅ Good: Reasonable retry configuration
const client = KatanaClient.withApiKey(apiKey, {
  retry: { maxRetries: 3, backoffFactor: 1.0 },
});

// ❌ Bad: Too many retries with long backoff
const client = KatanaClient.withApiKey(apiKey, {
  retry: { maxRetries: 10, backoffFactor: 5.0 }, // Could take 30+ minutes!
});
```

## Next Steps

- **[Cookbook](cookbook.md)** - Common usage patterns and recipes
- **[Testing Guide](testing.md)** - Testing strategy and patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records
