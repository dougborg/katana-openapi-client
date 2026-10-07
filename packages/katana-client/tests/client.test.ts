/**
 * Tests for KatanaClient
 *
 * Tests the main client class and its integration with
 * retry and pagination transport layers.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KatanaClient } from '../src/client.js';
import { createMockFetch, fetchCall, type MockFetch, sentHeaders } from './helpers/mockFetch.js';

describe('KatanaClient', () => {
  let mockFetch: MockFetch;
  const TEST_API_KEY = 'test-api-key-12345';
  const BASE_URL = 'https://api.katanamrp.com/v1';

  beforeEach(() => {
    mockFetch = createMockFetch();
  });

  describe('withApiKey', () => {
    it('should create client with explicit API key', () => {
      vi.stubEnv('KATANA_BASE_URL', '');
      const client = KatanaClient.withApiKey(TEST_API_KEY);
      vi.unstubAllEnvs();
      expect(client).toBeInstanceOf(KatanaClient);
      expect(client.getBaseUrl()).toBe(BASE_URL);
    });

    it('should use custom base URL', () => {
      const customUrl = 'https://custom.api.example.com';
      const client = KatanaClient.withApiKey(TEST_API_KEY, { baseUrl: customUrl });
      expect(client.getBaseUrl()).toBe(customUrl);
    });
  });

  describe('create', () => {
    it('should throw descriptive error when no API key is available', async () => {
      // Temporarily remove env var if present
      const originalEnv = process.env.KATANA_API_KEY;
      delete process.env.KATANA_API_KEY;

      try {
        await expect(KatanaClient.create()).rejects.toThrow(
          /API key required.*apiKey option.*KATANA_API_KEY.*--env-file/
        );
      } finally {
        // Restore env var
        if (originalEnv) {
          process.env.KATANA_API_KEY = originalEnv;
        }
      }
    });

    it('should create client with API key from environment variable', async () => {
      const originalEnv = process.env.KATANA_API_KEY;
      process.env.KATANA_API_KEY = 'env-api-key';

      try {
        const client = await KatanaClient.create();
        expect(client).toBeInstanceOf(KatanaClient);
      } finally {
        if (originalEnv) {
          process.env.KATANA_API_KEY = originalEnv;
        } else {
          delete process.env.KATANA_API_KEY;
        }
      }
    });
  });

  describe('fetch method', () => {
    it('should add Authorization header to requests', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      // Disable auto-pagination to test basic fetch behavior
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.fetch('/products');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url] = fetchCall(mockFetch);
      expect(url).toBe(`${BASE_URL}/products`);
      expect(sentHeaders(mockFetch).get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
    });

    it('should handle full URLs', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      // Disable auto-pagination to test basic fetch behavior
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.fetch('https://other.api.com/endpoint');

      const [url] = fetchCall(mockFetch);
      expect(url).toBe('https://other.api.com/endpoint');
    });

    it('should add Content-Type header for POST requests with body', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 201 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.fetch('/products', {
        method: 'POST',
        body: JSON.stringify({ name: 'Test Product' }),
      });
      expect(sentHeaders(mockFetch).get('Content-Type')).toBe('application/json');
    });
  });

  describe('rate limiting (requestsPerMinute)', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });
    afterEach(() => {
      vi.useRealTimers();
    });

    it('paces requests when a low budget is configured', async () => {
      mockFetch.mockResolvedValue(new Response(JSON.stringify({ data: [] }), { status: 200 }));
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
        requestsPerMinute: 1, // capacity 1: second request is paced a full window
      });

      const pending = [client.fetch('/products'), client.fetch('/products')];
      await vi.advanceTimersByTimeAsync(0);
      expect(mockFetch).toHaveBeenCalledTimes(1);

      await vi.advanceTimersByTimeAsync(60_000);
      expect(mockFetch).toHaveBeenCalledTimes(2);
      await Promise.all(pending);
    });

    it('disables proactive limiting when requestsPerMinute is null', async () => {
      mockFetch.mockResolvedValue(new Response(JSON.stringify({ data: [] }), { status: 200 }));
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
        requestsPerMinute: null,
      });

      const pending = [client.fetch('/products'), client.fetch('/products')];
      await vi.advanceTimersByTimeAsync(0);
      expect(mockFetch).toHaveBeenCalledTimes(2); // no token bucket -> no pacing
      await Promise.all(pending);
    });
  });

  describe('HTTP method shortcuts', () => {
    it('should make GET requests', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.get('/products');

      const [url, options] = fetchCall(mockFetch);
      expect(url).toContain('/products');
      expect(options?.method).toBe('GET');
    });

    it('should make GET requests with query params', async () => {
      const response = new Response(JSON.stringify({ data: [] }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.get('/products', { category: 'widgets', active: true });

      const [url] = fetchCall(mockFetch);
      expect(url).toContain('category=widgets');
      expect(url).toContain('active=true');
    });

    it('should make POST requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 201 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.post('/products', { name: 'New Product', sku: 'SKU-001' });

      const [, options] = fetchCall(mockFetch);
      expect(options?.method).toBe('POST');
      expect(options?.body).toBe(JSON.stringify({ name: 'New Product', sku: 'SKU-001' }));
    });

    it('should make PUT requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.put('/products/1', { name: 'Updated Product' });

      const [, options] = fetchCall(mockFetch);
      expect(options?.method).toBe('PUT');
    });

    it('should make PATCH requests', async () => {
      const response = new Response(JSON.stringify({ id: 1 }), { status: 200 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.patch('/products/1', { name: 'Patched Product' });

      const [, options] = fetchCall(mockFetch);
      expect(options?.method).toBe('PATCH');
    });

    it('should make DELETE requests', async () => {
      const response = new Response(null, { status: 204 });
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      await client.delete('/products/1');

      const [, options] = fetchCall(mockFetch);
      expect(options?.method).toBe('DELETE');
    });
  });

  describe('sdk property', () => {
    it('should return SDK client', () => {
      const client = KatanaClient.withApiKey(TEST_API_KEY);
      expect(client.sdk).toBeDefined();
      expect(typeof client.sdk.request).toBe('function');
    });
  });

  describe('getConfig', () => {
    it('should return config object with client', () => {
      const client = KatanaClient.withApiKey(TEST_API_KEY);
      const config = client.getConfig();
      expect(config).toHaveProperty('client');
      expect(config.client).toBe(client.sdk);
    });
  });

  describe('configuration options', () => {
    it('should apply custom retry configuration', async () => {
      // Mock fetch that returns 429 to test retry
      const rateLimitResponse = new Response(null, { status: 429 });
      const successResponse = new Response(JSON.stringify({ data: [] }), { status: 200 });

      mockFetch.mockResolvedValueOnce(rateLimitResponse).mockResolvedValueOnce(successResponse);

      // Use real timers with minimal delay for this test
      vi.useFakeTimers();

      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        retry: { maxRetries: 1, backoffFactor: 0.001 },
      });

      const responsePromise = client.fetch('/products', { method: 'POST' });

      // Advance timer to trigger retry
      await vi.advanceTimersByTimeAsync(10);

      const response = await responsePromise;
      expect(response.status).toBe(200);
      expect(mockFetch).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
    });

    it('should disable auto-pagination when configured', async () => {
      const response = new Response(
        JSON.stringify({
          data: [{ id: 1 }],
          pagination: { page: 1, total_pages: 5 },
        }),
        { status: 200 }
      );
      mockFetch.mockResolvedValueOnce(response);

      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        autoPagination: false,
      });
      await client.get('/products');

      // Should only make one request (no pagination)
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should apply custom pagination configuration', async () => {
      // Create responses for 3 pages
      const createPageResponse = (page: number) =>
        new Response(
          JSON.stringify({
            data: [{ id: page }],
            pagination: { page, total_pages: 10, per_page: 1 },
          }),
          { status: 200 }
        );

      mockFetch.mockImplementation(() => {
        const callCount = mockFetch.mock.calls.length;
        return Promise.resolve(createPageResponse(callCount));
      });

      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        pagination: { maxPages: 2 },
      });
      await client.get('/products');

      // Should stop at maxPages=2
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('resilience parity options', () => {
    afterEach(() => {
      vi.useRealTimers();
      vi.unstubAllEnvs();
    });

    function json(body: unknown, status = 200): Response {
      return new Response(JSON.stringify(body), { status });
    }

    it('reads the base URL from KATANA_BASE_URL when no baseUrl option is given', () => {
      vi.stubEnv('KATANA_BASE_URL', 'https://env.example.com/v1');
      expect(KatanaClient.withApiKey(TEST_API_KEY).getBaseUrl()).toBe('https://env.example.com/v1');
      expect(
        KatanaClient.withApiKey(TEST_API_KEY, {
          baseUrl: 'https://explicit.example.com',
        }).getBaseUrl()
      ).toBe('https://explicit.example.com');
    });

    it('times out a hung attempt after 30s by default and retries it', async () => {
      vi.useFakeTimers();
      mockFetch
        .mockImplementationOnce(
          (_input: RequestInfo | URL, init?: RequestInit) =>
            new Promise((_resolve, reject) => {
              init?.signal?.addEventListener('abort', () => reject(init.signal?.reason));
            })
        )
        .mockResolvedValueOnce(json({ id: 1 }));
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        requestsPerMinute: null,
        retry: { backoffJitter: 0 },
      });

      const pending = client.fetch('/products/1');
      await vi.advanceTimersByTimeAsync(29_999);
      expect(mockFetch).toHaveBeenCalledTimes(1);
      await vi.advanceTimersByTimeAsync(1 + 2_000); // timeout, then first backoff

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(await (await pending).json()).toEqual({ id: 1 });
    });

    it('sends no timeout signal when timeoutMs is null', async () => {
      mockFetch.mockResolvedValueOnce(json({ id: 1 }));
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        requestsPerMinute: null,
        timeoutMs: null,
      });
      await client.fetch('/products/1');
      expect(fetchCall(mockFetch)[1]?.signal).toBeUndefined();
    });

    it('aborts a request through the whole chain when the caller aborts', async () => {
      vi.useFakeTimers();
      mockFetch.mockResolvedValue(json({ message: 'down' }, 503));
      const client = KatanaClient.withApiKey(TEST_API_KEY, { fetch: mockFetch });
      const controller = new AbortController();

      const pending = client.fetch('/products/1', { signal: controller.signal });
      const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });
      await vi.advanceTimersByTimeAsync(100); // first attempt done, now backing off
      controller.abort();

      await assertion;
      await vi.advanceTimersByTimeAsync(300_000);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('supports per-request pagination overrides on fetch() and get()', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve(json({ data: [{ id: 1 }, { id: 2 }], pagination: { total_pages: 9 } }))
      );
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        requestsPerMinute: null,
      });

      await client.fetch('/products', undefined, { autoPagination: false });
      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(mockFetch.mock.calls[0][0]).not.toContain('page=');

      const limited = await client.get('/products', undefined, { maxItems: 3 });
      expect((await limited.json()).data).toHaveLength(3);
      expect(mockFetch).toHaveBeenCalledTimes(3); // 2 + 1 items over two pages
    });

    it('logs 4xx responses through the configured logger', async () => {
      const logger = { debug: vi.fn(), info: vi.fn(), warn: vi.fn(), error: vi.fn() };
      mockFetch.mockResolvedValueOnce(json({ message: 'Product not found' }, 404));
      const client = KatanaClient.withApiKey(TEST_API_KEY, {
        fetch: mockFetch,
        requestsPerMinute: null,
        logger,
      });

      const response = await client.get('/products/9');

      expect(response.status).toBe(404);
      expect(logger.error).toHaveBeenCalledWith(
        expect.stringContaining('Client error 404 for GET https://api.katanamrp.com/v1/products/9')
      );
    });
  });
});
