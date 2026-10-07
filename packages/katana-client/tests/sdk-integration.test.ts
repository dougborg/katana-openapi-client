/**
 * Tests for SDK integration with KatanaClient
 *
 * The generated SDK calls `fetch(request)` with a fully-built `Request` and no
 * `init`, so every transport layer must read method / headers / body / signal
 * from the Request itself. These tests pin that contract end to end.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { KatanaClient } from '../src/client.js';
import { createProduct, getAllProducts, getProduct } from '../src/generated/sdk.gen.js';
import { createMockFetch, type MockFetch } from './helpers/mockFetch.js';

type FetchArgs = Parameters<typeof fetch>;

/** Reconstruct the effective Request a mocked fetch received. */
function requestOf(call: FetchArgs): Request {
  return new Request(call[0], call[1]);
}

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

const WIDGET = { name: 'Widget', variants: [{ sku: 'W-1' }] };

describe('SDK Integration', () => {
  let mockFetch: MockFetch;
  const TEST_API_KEY = 'test-api-key-12345';

  const calls = (): FetchArgs[] => mockFetch.mock.calls;

  beforeEach(() => {
    mockFetch = createMockFetch();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  /** Client without proactive limiting / timeouts so tests stay synchronous-ish. */
  function client(options: Parameters<typeof KatanaClient.withApiKey>[1] = {}): KatanaClient {
    return KatanaClient.withApiKey(TEST_API_KEY, {
      fetch: mockFetch,
      requestsPerMinute: null,
      timeoutMs: null,
      ...options,
    });
  }

  describe('SDK with KatanaClient', () => {
    it('should pass authentication through SDK calls', async () => {
      mockFetch.mockResolvedValueOnce(json({ data: [] }));

      await getAllProducts({ client: client({ autoPagination: false }).sdk });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(requestOf(calls()[0]).headers.get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
    });

    it('should apply retry logic through SDK calls', async () => {
      vi.useFakeTimers();
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 429 }));
      mockFetch.mockResolvedValueOnce(json({ data: [] }));

      const katana = client({
        autoPagination: false,
        retry: { maxRetries: 1, backoffJitter: 0 },
      });
      const resultPromise = getAllProducts({ client: katana.sdk });

      // First retry waits backoffFactor * 2^1 = 2s (no jitter).
      await vi.advanceTimersByTimeAsync(1999);
      expect(mockFetch).toHaveBeenCalledTimes(1);
      await vi.advanceTimersByTimeAsync(1);

      const result = await resultPromise;
      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(result.response?.status).toBe(200);
    });

    it('should apply auto-pagination through SDK calls', async () => {
      mockFetch
        .mockResolvedValueOnce(
          json({ data: [{ id: 1 }, { id: 2 }], pagination: { page: 1, total_pages: 2 } })
        )
        .mockResolvedValueOnce(
          json({ data: [{ id: 3 }], pagination: { page: 2, total_pages: 2 } })
        );

      const result = await getAllProducts({ client: client().sdk });

      expect(mockFetch).toHaveBeenCalledTimes(2);
      expect(requestOf(calls()[0]).url).toContain('page=1');
      expect(requestOf(calls()[1]).url).toContain('page=2');
      // Auth survives the per-page Request rebuild.
      expect(requestOf(calls()[1]).headers.get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
      expect(result.data?.data).toHaveLength(3);
    });

    it('should work with getConfig() helper', async () => {
      mockFetch.mockResolvedValueOnce(json({ data: [] }));

      await getAllProducts(client({ autoPagination: false }).getConfig());

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(requestOf(calls()[0]).headers.get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
    });

    it('applies per-call pagination overrides via fetchWith()', async () => {
      mockFetch.mockResolvedValueOnce(
        json({ data: [{ id: 1 }, { id: 2 }], pagination: { page: 1, total_pages: 5 } })
      );

      const katana = client();
      const result = await getAllProducts({
        client: katana.sdk,
        fetch: katana.fetchWith({ maxItems: 2 }),
      });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(requestOf(calls()[0]).url).toContain('limit=2');
      expect(result.data?.data).toHaveLength(2);
    });
  });

  describe('SDK request fidelity (Request-style fetch calls)', () => {
    it('sends SDK POSTs as POST with their JSON body and Content-Type, unpaginated', async () => {
      mockFetch.mockResolvedValueOnce(json({ id: 7, name: 'Widget' }));

      const result = await createProduct({ client: client().sdk, body: WIDGET });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const request = requestOf(calls()[0]);
      expect(request.method).toBe('POST');
      expect(request.url).not.toContain('page=');
      expect(request.headers.get('Content-Type')).toBe('application/json');
      expect(request.headers.get('Authorization')).toBe(`Bearer ${TEST_API_KEY}`);
      expect(await request.json()).toEqual(WIDGET);
      expect(result.data).toEqual({ id: 7, name: 'Widget' });
    });

    it('does NOT retry an SDK POST on 503 (non-idempotent)', async () => {
      mockFetch.mockResolvedValue(json({ message: 'unavailable' }, 503));

      const result = await createProduct({ client: client().sdk, body: WIDGET });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.response?.status).toBe(503);
    });

    it('retries an SDK POST on 429 and replays the same body', async () => {
      vi.useFakeTimers();
      mockFetch
        .mockResolvedValueOnce(new Response(null, { status: 429, headers: { 'Retry-After': '1' } }))
        .mockResolvedValueOnce(json({ id: 7, name: 'Widget' }));

      const pending = createProduct({ client: client().sdk, body: WIDGET });
      await vi.advanceTimersByTimeAsync(1000);
      const result = await pending;

      expect(mockFetch).toHaveBeenCalledTimes(2);
      for (const call of calls()) {
        const request = requestOf(call);
        expect(request.method).toBe('POST');
        expect(await request.json()).toEqual(WIDGET);
      }
      expect(result.response?.status).toBe(200);
    });

    it('returns a single-resource GET body intact (no pagination envelope)', async () => {
      mockFetch.mockResolvedValueOnce(json({ id: 1, name: 'Widget' }));

      const result = await getProduct({ client: client().sdk, path: { id: 1 } });

      expect(result.data).toEqual({ id: 1, name: 'Widget' });
    });
  });

  describe('SDK error handling', () => {
    it('should return error response from SDK', async () => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Not Found', code: 'not_found' }, 404));

      const result = await getAllProducts({ client: client({ autoPagination: false }).sdk });

      expect(result.error).toBeDefined();
      expect(result.response?.status).toBe(404);
    });

    it('returns a non-retryable 500 response to the SDK unchanged', async () => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Server Error' }, 500));

      const result = await getAllProducts({ client: client({ autoPagination: false }).sdk });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(result.response?.status).toBe(500);
    });
  });

  describe('SDK with custom base URL', () => {
    it('should use custom base URL from client', async () => {
      mockFetch.mockResolvedValueOnce(json({ data: [] }));

      const customUrl = 'https://custom.api.example.com/v2';
      await getAllProducts({ client: client({ baseUrl: customUrl, autoPagination: false }).sdk });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      expect(requestOf(calls()[0]).url).toContain(customUrl);
    });
  });
});
