# Cookbook: Common Patterns

This cookbook provides ready-to-use code patterns for common tasks with the TypeScript
Katana client.

## Table of Contents

- [Getting Products](#getting-products)
- [Managing Inventory](#managing-inventory)
- [Working with Sales Orders](#working-with-sales-orders)
- [Purchase Orders](#purchase-orders)
- [Manufacturing Orders](#manufacturing-orders)
- [Error Handling Patterns](#error-handling-patterns)
- [Performance Optimization](#performance-optimization)
- [Testing Patterns](#testing-patterns)

## Getting Products

### List All Products

```typescript
import { KatanaClient } from 'katana-openapi-client';

const client = await KatanaClient.create();

// Auto-pagination collects all products
const response = await client.get('/products');
const { data: products, pagination } = await response.json();

console.log(`Found ${products.length} products`);
console.log(`Collected from ${pagination.collected_pages} pages`);
```

### Filter Products

```typescript
// Get only sellable products
const response = await client.get('/products', {
  is_sellable: true,
  is_producible: true,
});
const { data: products } = await response.json();
```

### Get Product by ID

```typescript
const response = await client.get('/products/123');
if (response.ok) {
  const product = await response.json();
  console.log(`Product: ${product.name}`);
} else {
  console.error(`Product not found: ${response.status}`);
}
```

### Create a New Product

```typescript
const response = await client.post('/products', {
  name: 'Widget Pro',
  sku: 'WGT-PRO-001',
  is_sellable: true,
  is_producible: true,
  sales_price: 29.99,
});

if (response.ok) {
  const product = await response.json();
  console.log(`Created product: ${product.id}`);
} else {
  const error = await response.json();
  console.error('Failed to create product:', error);
}
```

### Update a Product

```typescript
const response = await client.patch('/products/123', {
  name: 'Widget Pro v2',
  sales_price: 34.99,
});

if (response.ok) {
  console.log('Product updated');
}
```

## Managing Inventory

### Check Stock Levels

```typescript
const response = await client.get('/stock');
const { data: stockItems } = await response.json();

// Find low stock items
const lowStock = stockItems.filter((item: any) =>
  item.in_stock < item.reorder_point
);

console.log(`${lowStock.length} items below reorder point`);
```

### Search for Variant by SKU

```typescript
const response = await client.get('/variants', {
  search: 'WGT-PRO-001',
});
const { data: variants } = await response.json();

const variant = variants.find((v: any) => v.sku === 'WGT-PRO-001');
if (variant) {
  console.log(`Found variant ID: ${variant.id}`);
}
```

### Get Stock for Specific Variant

```typescript
const variantId = 123;
const response = await client.get(`/variants/${variantId}/stock`);
const stock = await response.json();

console.log(`In stock: ${stock.in_stock}`);
console.log(`Committed: ${stock.committed}`);
console.log(`Expected: ${stock.expected}`);
console.log(`Available: ${stock.available}`);
```

## Working with Sales Orders

### List Recent Sales Orders

```typescript
// Get orders from the last 30 days
const thirtyDaysAgo = new Date();
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

const response = await client.get('/sales_orders', {
  created_at_min: thirtyDaysAgo.toISOString(),
});
const { data: orders } = await response.json();

console.log(`${orders.length} orders in the last 30 days`);
```

### Get Order Details

```typescript
const orderId = 456;
const response = await client.get(`/sales_orders/${orderId}`);
const order = await response.json();

console.log(`Order: ${order.order_no}`);
console.log(`Customer: ${order.customer?.name}`);
console.log(`Total: ${order.total_price}`);
console.log(`Items: ${order.sales_order_rows?.length}`);
```

### Create a Sales Order

```typescript
const response = await client.post('/sales_orders', {
  customer_id: 789,
  delivery_deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
  sales_order_rows: [
    {
      variant_id: 123,
      quantity: 10,
      unit_price: 29.99,
    },
  ],
});

if (response.ok) {
  const order = await response.json();
  console.log(`Created order: ${order.order_no}`);
}
```

### Update Order Status

```typescript
const response = await client.patch(`/sales_orders/${orderId}`, {
  status: 'DONE',
});
```

## Purchase Orders

### List Pending Purchase Orders

```typescript
const response = await client.get('/purchase_orders', {
  status: 'NOT_RECEIVED',
});
const { data: orders } = await response.json();

console.log(`${orders.length} pending purchase orders`);
```

### Create Purchase Order

```typescript
const response = await client.post('/purchase_orders', {
  supplier_id: 101,
  location_id: 1,
  purchase_order_rows: [
    {
      variant_id: 456,
      quantity: 100,
      purchase_price: 15.00,
    },
  ],
});

if (response.ok) {
  const po = await response.json();
  console.log(`Created PO: ${po.order_no}`);
}
```

### Receive Items

```typescript
const poId = 789;
const response = await client.post(`/purchase_orders/${poId}/receive`, {
  items: [
    {
      purchase_order_row_id: 123,
      quantity: 100,
    },
  ],
});
```

## Manufacturing Orders

### List Active Manufacturing Orders

```typescript
const response = await client.get('/manufacturing_orders', {
  status: 'IN_PROGRESS',
});
const { data: orders } = await response.json();

for (const order of orders) {
  console.log(`MO ${order.id}: ${order.product_variant?.sku} - ${order.status}`);
}
```

### Create Manufacturing Order

```typescript
const response = await client.post('/manufacturing_orders', {
  variant_id: 123,
  planned_quantity: 50,
  location_id: 1,
  production_deadline: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
});

if (response.ok) {
  const mo = await response.json();
  console.log(`Created MO: ${mo.id}`);
}
```

### Complete Manufacturing Order

```typescript
const moId = 456;
const response = await client.patch(`/manufacturing_orders/${moId}`, {
  status: 'DONE',
  actual_quantity: 48,
});
```

## Error Handling Patterns

### Comprehensive Error Handler

```typescript
import {
  parseError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError,
} from 'katana-openapi-client';

async function handleApiCall<T>(
  operation: () => Promise<Response>,
  resourceName: string
): Promise<T | null> {
  try {
    const response = await operation();

    if (response.ok) {
      return await response.json();
    }

    const body = await response.json().catch(() => null);
    const error = parseError(response, body);

    if (error instanceof AuthenticationError) {
      console.error('Authentication failed. Check your API key.');
      throw error;
    }

    if (error instanceof RateLimitError) {
      console.error(`Rate limited. Retry after ${error.retryAfter ?? 60}s`);
      // The client handles retries automatically, but you may want to log this
      throw error;
    }

    if (error instanceof ValidationError) {
      console.error(`Validation failed for ${resourceName}:`);
      for (const detail of error.details) {
        console.error(`  - ${detail.field}: ${detail.message}`);
      }
      throw error;
    }

    if (error instanceof ServerError) {
      console.error(`Server error (${error.statusCode}). Try again later.`);
      throw error;
    }

    console.error(`API error: ${error.message}`);
    throw error;
  } catch (error) {
    if (error instanceof NetworkError) {
      console.error('Network error. Check your connection.');
    }
    throw error;
  }
}

// Usage
const product = await handleApiCall(
  () => client.get('/products/123'),
  'product'
);
```

### Retry with Custom Logic

```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts = 3,
  delayMs = 1000
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      console.error(`Attempt ${attempt} failed: ${lastError.message}`);

      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, delayMs * attempt));
      }
    }
  }

  throw lastError;
}

// Usage for operations the client doesn't auto-retry
const result = await withRetry(
  async () => {
    const response = await client.post('/custom_endpoint', data);
    if (!response.ok) throw new Error(`Failed: ${response.status}`);
    return response.json();
  },
  3,
  2000
);
```

## Performance Optimization

### Batch Processing

```typescript
async function processBatch<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  batchSize = 5,
  delayMs = 100
): Promise<R[]> {
  const results: R[] = [];

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);

    const batchResults = await Promise.all(
      batch.map(item => processor(item))
    );
    results.push(...batchResults);

    // Delay between batches to respect rate limits
    if (i + batchSize < items.length) {
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }

  return results;
}

// Usage: Update multiple products
const productUpdates = [
  { id: 1, name: 'Updated 1' },
  { id: 2, name: 'Updated 2' },
  // ...
];

await processBatch(
  productUpdates,
  async (update) => {
    const response = await client.patch(`/products/${update.id}`, update);
    return response.json();
  },
  5,
  200
);
```

### Parallel Requests with Limit

```typescript
import pLimit from 'p-limit';

// Limit concurrent requests
const limit = pLimit(5);

const productIds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

const products = await Promise.all(
  productIds.map(id =>
    limit(async () => {
      const response = await client.get(`/products/${id}`);
      return response.json();
    })
  )
);
```

### Caching Layer

```typescript
class CachedClient {
  private cache = new Map<string, { data: any; expires: number }>();
  private client: KatanaClient;
  private ttlMs: number;

  constructor(client: KatanaClient, ttlMs = 60000) {
    this.client = client;
    this.ttlMs = ttlMs;
  }

  async get(path: string): Promise<any> {
    const cached = this.cache.get(path);

    if (cached && cached.expires > Date.now()) {
      return cached.data;
    }

    const response = await this.client.get(path);
    const data = await response.json();

    this.cache.set(path, {
      data,
      expires: Date.now() + this.ttlMs,
    });

    return data;
  }

  invalidate(path?: string) {
    if (path) {
      this.cache.delete(path);
    } else {
      this.cache.clear();
    }
  }
}

// Usage
const cachedClient = new CachedClient(client, 5 * 60 * 1000); // 5 min cache
const products = await cachedClient.get('/products');
```

## Testing Patterns

### Mocking the Client

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { KatanaClient } from 'katana-openapi-client';

describe('ProductService', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let client: KatanaClient;

  beforeEach(() => {
    mockFetch = vi.fn();
    client = KatanaClient.withApiKey('test-key', {
      fetch: mockFetch,
      autoPagination: false, // Disable for predictable tests
    });
  });

  it('should fetch products', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ data: [{ id: 1, name: 'Test' }] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );

    const response = await client.get('/products');
    const { data } = await response.json();

    expect(data).toHaveLength(1);
    expect(data[0].name).toBe('Test');
  });

  it('should handle errors', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Not Found' }), { status: 404 })
    );

    const response = await client.get('/products/999');
    expect(response.status).toBe(404);
  });
});
```

### Testing with Fake Timers

```typescript
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('Retry behavior', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should retry on rate limit', async () => {
    const mockFetch = vi.fn()
      .mockResolvedValueOnce(new Response(null, { status: 429 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ data: [] }), { status: 200 })
      );

    const client = KatanaClient.withApiKey('test-key', {
      fetch: mockFetch,
      retry: { maxRetries: 1 },
    });

    const responsePromise = client.get('/products');

    // Advance timer for retry delay
    await vi.advanceTimersByTimeAsync(1000);

    const response = await responsePromise;
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
```

### Integration Test Pattern

```typescript
import { describe, it, expect } from 'vitest';
import { KatanaClient } from 'katana-openapi-client';

describe('Integration Tests', () => {
  // Skip if no API key
  const apiKey = process.env.KATANA_API_KEY;
  const runIntegration = apiKey ? it : it.skip;

  runIntegration('should fetch real products', async () => {
    const client = KatanaClient.withApiKey(apiKey!, {
      pagination: { maxItems: 5 }, // Limit for test
    });

    const response = await client.get('/products');
    expect(response.ok).toBe(true);

    const { data } = await response.json();
    expect(Array.isArray(data)).toBe(true);
  });
});
```

## Next Steps

- **[Guide](guide.md)** - Comprehensive client guide
- **[Testing Guide](testing.md)** - Testing strategy and patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records
