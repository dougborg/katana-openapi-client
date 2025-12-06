# Testing Guide

This guide explains the testing architecture and approach for the TypeScript Katana
client.

## Testing Philosophy

The TypeScript client follows the same testing principles as the Python client:

- **Transport-layer focus**: Test the resilient fetch wrappers
- **Unit tests for logic**: Test retry decisions, pagination logic, error parsing
- **Integration tests**: Optional tests against real API
- **Mocking at the right level**: Mock fetch, not internal methods

## Test Structure

### Core Test Files

**`tests/client.test.ts`** - KatanaClient Tests

- Client creation and configuration
- Authentication header injection
- HTTP method shortcuts (get, post, put, patch, delete)
- SDK client integration

**`tests/transport/retry.test.ts`** - Retry Transport Tests

- `shouldRetry()` function for different HTTP methods and status codes
- `calculateRetryDelay()` for exponential backoff
- `createResilientFetch()` integration tests

**`tests/transport/pagination.test.ts`** - Pagination Transport Tests

- `hasExplicitPageParam()` URL parsing
- `extractPaginationInfo()` from headers and body
- `createPaginatedFetch()` auto-pagination behavior

**`tests/errors.test.ts`** - Error Handling Tests

- Error class construction
- `parseError()` function for different status codes
- Validation error detail parsing

**`tests/sdk-integration.test.ts`** - SDK Integration Tests

- SDK functions with resilient client
- Authentication flow through SDK
- Auto-pagination through SDK

## Running Tests

### Development Workflow

```bash
# Run all tests
pnpm test

# Watch mode for development
pnpm test:watch

# Run with coverage
pnpm test:coverage
```

### From Repository Root

```bash
# Navigate to TypeScript client package
cd packages/katana-client

# Run tests
pnpm test
```

### Test Output

```text
 ✓ tests/errors.test.ts (21 tests)
 ✓ tests/transport/pagination.test.ts (18 tests)
 ✓ tests/transport/retry.test.ts (34 tests)
 ✓ tests/client.test.ts (18 tests)
 ✓ tests/sdk-integration.test.ts (7 tests)

 Test Files  5 passed (5)
      Tests  98 passed (98)
   Duration  219ms
```

## Test Categories

### Retry Logic Tests

Tests for the resilient transport layer:

```typescript
describe('shouldRetry', () => {
  describe('429 Rate Limiting', () => {
    it('should retry GET requests on 429', () => {
      expect(shouldRetry('GET', 429, config)).toBe(true);
    });

    it('should retry POST requests on 429', () => {
      expect(shouldRetry('POST', 429, config)).toBe(true);
    });
  });

  describe('5xx Server Errors', () => {
    it('should retry GET requests on 502', () => {
      expect(shouldRetry('GET', 502, config)).toBe(true);
    });

    it('should NOT retry POST requests on 502', () => {
      expect(shouldRetry('POST', 502, config)).toBe(false);
    });
  });
});
```

### Pagination Tests

Tests for auto-pagination behavior:

```typescript
describe('createPaginatedFetch', () => {
  it('should collect all pages when auto-paginating', async () => {
    mockFetch
      .mockResolvedValueOnce(page1Response)
      .mockResolvedValueOnce(page2Response)
      .mockResolvedValueOnce(page3Response);

    const paginatedFetch = createPaginatedFetch(mockFetch);
    const response = await paginatedFetch('https://api.example.com/products');

    expect(mockFetch).toHaveBeenCalledTimes(3);

    const body = await response.json();
    expect(body.data).toHaveLength(5);
    expect(body.pagination.auto_paginated).toBe(true);
  });

  it('should not paginate when explicit page param is present', async () => {
    mockFetch.mockResolvedValueOnce(response);

    const paginatedFetch = createPaginatedFetch(mockFetch);
    await paginatedFetch('https://api.example.com/products?page=2');

    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});
```

### Error Handling Tests

Tests for error classes and parsing:

```typescript
describe('parseError', () => {
  it('should return AuthenticationError for 401', () => {
    const response = new Response(null, { status: 401 });
    const error = parseError(response);
    expect(error).toBeInstanceOf(AuthenticationError);
    expect(error.statusCode).toBe(401);
  });

  it('should return RateLimitError for 429', () => {
    const headers = new Headers({ 'Retry-After': '30' });
    const response = new Response(null, { status: 429, headers });
    const error = parseError(response);
    expect(error).toBeInstanceOf(RateLimitError);
    expect((error as RateLimitError).retryAfter).toBe(30);
  });

  it('should return ValidationError for 422 with details', () => {
    const response = new Response(null, { status: 422 });
    const body = { errors: [{ field: 'name', message: 'Required' }] };
    const error = parseError(response, body);
    expect(error).toBeInstanceOf(ValidationError);
    expect((error as ValidationError).details).toHaveLength(1);
  });
});
```

## Testing Patterns

### Mocking Fetch

The client accepts a custom `fetch` function, making it easy to mock:

```typescript
import { vi } from 'vitest';
import { KatanaClient } from '../src/client.js';

describe('KatanaClient', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
  });

  it('should add Authorization header', async () => {
    mockFetch.mockResolvedValueOnce(
      new Response(JSON.stringify({ data: [] }), { status: 200 })
    );

    const client = KatanaClient.withApiKey('test-key', {
      fetch: mockFetch,
      autoPagination: false,
    });

    await client.get('/products');

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers.get('Authorization')).toBe('Bearer test-key');
  });
});
```

### Using Fake Timers

For testing retry delays:

```typescript
import { vi } from 'vitest';

describe('Retry with delays', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should retry on 429 and succeed', async () => {
    const rateLimitResponse = new Response(null, { status: 429 });
    const successResponse = new Response(JSON.stringify({ data: [] }), { status: 200 });

    mockFetch
      .mockResolvedValueOnce(rateLimitResponse)
      .mockResolvedValueOnce(successResponse);

    const client = KatanaClient.withApiKey('test-key', {
      fetch: mockFetch,
      retry: { maxRetries: 3 },
    });

    const responsePromise = client.get('/products');

    // Advance timers for retry delay
    await vi.advanceTimersByTimeAsync(1000);

    const response = await responsePromise;
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});
```

### Testing Error Conditions

```typescript
it('should throw after max retries on network error', async () => {
  vi.useRealTimers(); // Use real timers for this test

  const mockFetch = vi.fn().mockRejectedValue(new Error('Network error'));

  const resilientFetch = createResilientFetch({
    baseFetch: mockFetch,
    retry: {
      maxRetries: 2,
      backoffFactor: 0.001, // Very short delays
    },
  });

  await expect(
    resilientFetch('https://api.example.com/test')
  ).rejects.toThrow('Network error');

  expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
});
```

### Environment Variable Tests

```typescript
describe('create', () => {
  it('should throw descriptive error when no API key', async () => {
    const originalEnv = process.env.KATANA_API_KEY;
    // biome-ignore lint/performance/noDelete: Need to actually remove env var
    delete process.env.KATANA_API_KEY;

    try {
      await expect(KatanaClient.create()).rejects.toThrow(
        /API key required.*apiKey option.*KATANA_API_KEY.*--env-file/
      );
    } finally {
      if (originalEnv) {
        process.env.KATANA_API_KEY = originalEnv;
      }
    }
  });

  it('should use API key from environment', async () => {
    const originalEnv = process.env.KATANA_API_KEY;
    process.env.KATANA_API_KEY = 'env-api-key';

    try {
      const client = await KatanaClient.create();
      expect(client).toBeInstanceOf(KatanaClient);
    } finally {
      if (originalEnv) {
        process.env.KATANA_API_KEY = originalEnv;
      } else {
        // biome-ignore lint/performance/noDelete: Restore original state
        delete process.env.KATANA_API_KEY;
      }
    }
  });
});
```

## Integration Tests

Integration tests require a real API key and hit the actual Katana API.

### Running Integration Tests

```bash
# Set API key
export KATANA_API_KEY=your-api-key

# Run integration tests
pnpm test -- --grep "integration"
```

### Writing Integration Tests

```typescript
import { describe, it, expect } from 'vitest';
import { KatanaClient } from '../src/client.js';

describe('Integration Tests', () => {
  const apiKey = process.env.KATANA_API_KEY;
  const runIntegration = apiKey ? it : it.skip;

  runIntegration('should fetch products from real API', async () => {
    const client = KatanaClient.withApiKey(apiKey!, {
      pagination: { maxItems: 5 },
    });

    const response = await client.get('/products');
    expect(response.ok).toBe(true);

    const { data } = await response.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBeLessThanOrEqual(5);
  });

  runIntegration('should handle rate limiting', async () => {
    const client = KatanaClient.withApiKey(apiKey!, {
      retry: { maxRetries: 3 },
    });

    // Make multiple rapid requests to potentially trigger rate limiting
    const responses = await Promise.all([
      client.get('/products', { limit: 1 }),
      client.get('/variants', { limit: 1 }),
      client.get('/stock', { limit: 1 }),
    ]);

    // All should succeed (retries handle rate limits)
    for (const response of responses) {
      expect(response.ok).toBe(true);
    }
  });
});
```

## Code Coverage

### Running Coverage

```bash
pnpm test:coverage
```

### Coverage Report

```text
---------|---------|----------|---------|---------|
File     | % Stmts | % Branch | % Funcs | % Lines |
---------|---------|----------|---------|---------|
All files|   85.2  |   78.5   |   90.1  |   85.2  |
 client  |   82.3  |   75.0   |   88.9  |   82.3  |
 errors  |   95.0  |   90.0   |  100.0  |   95.0  |
 transport|  86.5  |   80.0   |   88.0  |   86.5  |
---------|---------|----------|---------|---------|
```

### Coverage Goals

- **Core logic**: 80%+ coverage
- **Error handling**: 90%+ coverage
- **Transport layers**: 85%+ coverage
- **Generated code**: Not included in coverage

## Best Practices

### 1. Test Behavior, Not Implementation

```typescript
// ✅ Good: Tests behavior
it('should retry on rate limit', async () => {
  // ... test that retry happens
});

// ❌ Bad: Tests internal implementation
it('should call shouldRetry with correct params', () => {
  // ... testing internal method calls
});
```

### 2. Mock at the Right Level

```typescript
// ✅ Good: Mock fetch
const mockFetch = vi.fn();
const client = KatanaClient.withApiKey('key', { fetch: mockFetch });

// ❌ Bad: Mock internal methods
vi.spyOn(client, 'createAuthenticatedFetch');
```

### 3. Use Descriptive Test Names

```typescript
// ✅ Good
it('should return AuthenticationError for 401 responses', () => {});

// ❌ Bad
it('handles 401', () => {});
```

### 4. Clean Up After Tests

```typescript
afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});
```

### 5. Test Edge Cases

```typescript
describe('Edge cases', () => {
  it('should handle empty responses', async () => {});
  it('should handle malformed JSON', async () => {});
  it('should handle network timeouts', async () => {});
  it('should handle concurrent requests', async () => {});
});
```

## Test Configuration

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      exclude: [
        'src/generated/**',
        'dist/**',
        'node_modules/**',
      ],
    },
  },
});
```

## Next Steps

- **[Guide](guide.md)** - Comprehensive client guide
- **[Cookbook](cookbook.md)** - Common usage patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records
