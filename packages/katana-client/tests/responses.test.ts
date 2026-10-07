/**
 * Tests for the SDK response helpers (unwrap / unwrapData / isSuccess / ...).
 *
 * Results come from real generated SDK calls over a mocked fetch, so the
 * helpers are exercised against the exact `{ data, error, request, response }`
 * shape (and the exact types) users get.
 */

import { beforeEach, describe, expect, expectTypeOf, it } from 'vitest';
import { KatanaClient } from '../src/client.js';
import {
  AuthenticationError,
  KatanaError,
  NetworkError,
  RateLimitError,
  ServerError,
  ValidationError,
} from '../src/errors.js';
import {
  deleteSupplier,
  getAllProducts,
  getAllStorageBins,
  getProduct,
  type getUserInfo,
} from '../src/generated/sdk.gen.js';
import type { Product, StorageBinResponse } from '../src/generated/types.gen.js';
import {
  getError,
  getErrorMessage,
  isError,
  isSuccess,
  type ListResultGuard,
  type SdkResult,
  unwrap,
  unwrapData,
} from '../src/responses.js';
import { expectInstance } from './helpers/assert.js';
import { createMockFetch, type MockFetch } from './helpers/mockFetch.js';

function json(body: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

describe('response helpers', () => {
  let mockFetch: MockFetch;
  let katana: KatanaClient;

  beforeEach(() => {
    mockFetch = createMockFetch();
    // No retries / pacing / timeouts: each call maps to exactly one mocked response.
    katana = KatanaClient.withApiKey('test-key', {
      fetch: mockFetch,
      requestsPerMinute: null,
      timeoutMs: null,
      retry: { maxRetries: 0 },
    });
  });

  const fetchProduct = () => getProduct({ client: katana.sdk, path: { id: 1 } });

  describe('unwrap', () => {
    it('returns the data of a successful call, typed from the SDK function', async () => {
      mockFetch.mockResolvedValueOnce(json({ id: 1, name: 'Widget' }));

      const product = unwrap(await fetchProduct());

      expectTypeOf(product).toEqualTypeOf<Product>();
      expect(product).toEqual({ id: 1, name: 'Widget' });
    });

    it('returns undefined for a 204 no-content success', async () => {
      mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }));

      const result = await deleteSupplier({ client: katana.sdk, path: { id: 1 } });

      expectTypeOf(unwrap(result)).toEqualTypeOf<void>();
      expect(unwrap(result)).toBeUndefined();
    });

    it('throws AuthenticationError on 401', async () => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Unauthorized' }, 401));

      const result = await fetchProduct();

      expect(() => unwrap(result)).toThrow(AuthenticationError);
      expect(getError(result)?.statusCode).toBe(401);
    });

    it('throws ValidationError with structured details on 422', async () => {
      const detail = {
        path: '/name',
        code: 'required',
        message: "must have required property 'name'",
        info: { missingProperty: 'name' },
      };
      mockFetch.mockResolvedValueOnce(
        json({ error: { message: 'Invalid body', details: [detail] } }, 422)
      );

      const error = expectInstance(getError(await fetchProduct()), ValidationError);

      expect(error.details).toEqual([detail]);
      expect(error.message).toContain("Missing required field: 'name'");
    });

    it('throws RateLimitError with retryAfter on 429', async () => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Too many' }, 429, { 'Retry-After': '7' }));

      const result = await fetchProduct();

      expect(() => unwrap(result)).toThrow(RateLimitError);
      expect(expectInstance(getError(result), RateLimitError).retryAfter).toBe(7);
    });

    it.each([500, 502, 503])('throws ServerError on %i', async (status) => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Boom' }, status));

      const error = expectInstance(getError(await fetchProduct()), ServerError);

      expect(error.statusCode).toBe(status);
      expect(error.message).toBe('Boom');
    });

    it('throws a plain KatanaError for other statuses, keeping the body', async () => {
      const body = { error: { message: 'Product not found' } };
      mockFetch.mockResolvedValueOnce(json(body, 404));

      const result = await fetchProduct();
      const error = getError(result);

      expect(() => unwrap(result)).toThrow('Product not found');
      expect(error?.constructor).toBe(KatanaError);
      expect(error?.statusCode).toBe(404);
      expect(error?.body).toEqual(body);
    });

    it('handles a non-JSON error body', async () => {
      mockFetch.mockResolvedValueOnce(new Response('<html>bad gateway</html>', { status: 400 }));

      const error = getError(await fetchProduct());

      expect(error?.message).toBe('Request failed with status 400');
      expect(error?.body).toBe('<html>bad gateway</html>');
    });

    it('throws NetworkError (with cause) when no response arrived', async () => {
      const cause = new TypeError('fetch failed');
      mockFetch.mockRejectedValue(cause);

      const result = await fetchProduct();

      expect(result.response).toBeUndefined();
      expect(() => unwrap(result)).toThrow(NetworkError);
      expect(getError(result)).toHaveProperty('cause', cause);
    });
  });

  describe('unwrapData', () => {
    it('unwraps the { data: [...] } list envelope, typed by item', async () => {
      mockFetch.mockResolvedValueOnce(json({ data: [{ id: 1 }, { id: 2 }] }));

      const products = unwrapData(
        await getAllProducts({ client: katana.sdk, query: { limit: 2, page: 1 } })
      );

      expectTypeOf(products).toEqualTypeOf<Product[]>();
      expect(products).toEqual([{ id: 1 }, { id: 2 }]);
    });

    it('returns a bare-array list response (GET /bin_locations) as-is', async () => {
      mockFetch.mockResolvedValueOnce(json([{ id: 9 }]));

      const bins = unwrapData(await getAllStorageBins({ client: katana.sdk }));

      expectTypeOf(bins).toEqualTypeOf<StorageBinResponse[]>();
      expect(bins).toEqual([{ id: 9 }]);
    });

    it('returns [] when the envelope has no data key', async () => {
      mockFetch.mockResolvedValueOnce(json({}));

      expect(unwrapData(await getAllProducts({ client: katana.sdk }))).toEqual([]);
    });

    it('throws the typed error for a failed list call', async () => {
      mockFetch.mockResolvedValueOnce(json({ message: 'Unauthorized' }, 401));

      const result = await getAllProducts({ client: katana.sdk });

      expect(() => unwrapData(result)).toThrow(AuthenticationError);
    });

    it('throws TypeError when a success payload is not a list', async () => {
      mockFetch.mockResolvedValueOnce(json({ data: 'nope' }));

      const result = await getAllProducts({ client: katana.sdk });

      expect(() => unwrapData(result)).toThrow(TypeError);
    });

    it('only accepts list endpoints at the type level', () => {
      type AcceptedByUnwrapData<R extends SdkResult> = [ListResultGuard<R>] extends [never]
        ? false
        : true;
      type ResultOf<F extends (...args: never[]) => Promise<SdkResult>> = Awaited<ReturnType<F>>;

      expectTypeOf<
        AcceptedByUnwrapData<ResultOf<typeof getAllProducts<false>>>
      >().toEqualTypeOf<true>();
      expectTypeOf<
        AcceptedByUnwrapData<ResultOf<typeof getAllStorageBins<false>>>
      >().toEqualTypeOf<true>();
      // Single resources (incl. the bare-model GET /user_info) need `unwrap`.
      expectTypeOf<
        AcceptedByUnwrapData<ResultOf<typeof getProduct<false>>>
      >().toEqualTypeOf<false>();
      expectTypeOf<
        AcceptedByUnwrapData<ResultOf<typeof getUserInfo<false>>>
      >().toEqualTypeOf<false>();
    });
  });

  describe('isSuccess / isError / getErrorMessage', () => {
    it('reports success and narrows data', async () => {
      mockFetch.mockResolvedValueOnce(json({ id: 1 }));

      const result = await fetchProduct();

      expect(isSuccess(result)).toBe(true);
      expect(isError(result)).toBe(false);
      expect(getErrorMessage(result)).toBeUndefined();
      if (isSuccess(result)) {
        expectTypeOf(result.data).toEqualTypeOf<Product>();
      }
    });

    it('reports failure with the error message', async () => {
      mockFetch.mockResolvedValueOnce(json({ error: { message: 'Product not found' } }, 404));

      const result = await fetchProduct();

      expect(isSuccess(result)).toBe(false);
      expect(isError(result)).toBe(true);
      expect(getErrorMessage(result)).toBe('Product not found');
    });
  });
});
