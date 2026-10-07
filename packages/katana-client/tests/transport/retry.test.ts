/**
 * Tests for the resilient retry transport.
 *
 * Mirrors the Python client's RateLimitAwareRetry + httpx-retries policy
 * (tests/test_rate_limit_retry.py). All waits run on vitest fake timers — the
 * real clock is never consulted.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  calculateRetryDelay,
  createResilientFetch,
  DEFAULT_RETRY_CONFIG,
  isRetryableError,
  parseRetryAfter,
  type RetryConfig,
  shouldRetry,
} from '../../src/transport/resilient.js';

/** Deterministic config: no jitter, so backoff is exactly factor * 2^n seconds. */
const NO_JITTER: RetryConfig = { ...DEFAULT_RETRY_CONFIG, backoffJitter: 0 };

function status(code: number, headers?: Record<string, string>): Response {
  return new Response(code === 204 ? null : '{}', { status: code, headers });
}

describe('DEFAULT_RETRY_CONFIG', () => {
  it('matches the Python client defaults', () => {
    expect(DEFAULT_RETRY_CONFIG).toEqual({
      maxRetries: 5,
      backoffFactor: 1.0,
      backoffJitter: 1.0,
      maxBackoffSeconds: 120,
      retryStatusCodes: [429, 502, 503, 504],
      respectRetryAfter: true,
    });
  });
});

describe('shouldRetry', () => {
  const config = DEFAULT_RETRY_CONFIG;

  it.each(['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE', 'POST', 'PATCH'])(
    'retries %s on 429',
    (method) => {
      expect(shouldRetry(method, 429, config)).toBe(true);
    }
  );

  it.each(['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'])(
    'retries idempotent %s on 502/503/504',
    (method) => {
      for (const code of [502, 503, 504]) {
        expect(shouldRetry(method, code, config)).toBe(true);
      }
    }
  );

  it.each(['POST', 'PATCH'])('does NOT retry non-idempotent %s on 502/503/504', (method) => {
    for (const code of [502, 503, 504]) {
      expect(shouldRetry(method, code, config)).toBe(false);
    }
  });

  it('never retries methods outside the allowed set (e.g. CONNECT), even on 429', () => {
    expect(shouldRetry('CONNECT', 429, config)).toBe(false);
  });

  it.each([400, 401, 403, 404, 422, 500])('does not retry %i', (code) => {
    expect(shouldRetry('GET', code, config)).toBe(false);
  });

  it('is case-insensitive on the method', () => {
    expect(shouldRetry('get', 502, config)).toBe(true);
    expect(shouldRetry('Post', 502, config)).toBe(false);
  });

  it('honours a custom status list', () => {
    expect(shouldRetry('GET', 500, { retryStatusCodes: [500] })).toBe(true);
    expect(shouldRetry('GET', 429, { retryStatusCodes: [500] })).toBe(false);
  });
});

describe('isRetryableError', () => {
  it('retries fetch network failures (TypeError) for every retryable method', () => {
    expect(isRetryableError('GET', new TypeError('fetch failed'))).toBe(true);
    expect(isRetryableError('POST', new TypeError('fetch failed'))).toBe(true);
  });

  it('retries per-attempt timeouts', () => {
    expect(isRetryableError('GET', new DOMException('timed out', 'TimeoutError'))).toBe(true);
  });

  it('does not retry aborts, arbitrary errors, or CONNECT', () => {
    expect(isRetryableError('GET', new DOMException('aborted', 'AbortError'))).toBe(false);
    expect(isRetryableError('GET', new Error('boom'))).toBe(false);
    expect(isRetryableError('CONNECT', new TypeError('fetch failed'))).toBe(false);
  });

  it('never retries once the caller signal is aborted', () => {
    const controller = new AbortController();
    controller.abort();
    expect(isRetryableError('GET', new TypeError('fetch failed'), controller.signal)).toBe(false);
  });
});

describe('parseRetryAfter', () => {
  const now = Date.parse('2026-01-01T00:00:00Z');

  it('parses delta-seconds', () => {
    expect(parseRetryAfter('30', now)).toBe(30);
    expect(parseRetryAfter(' 0 ', now)).toBe(0);
  });

  it('parses an HTTP-date relative to now', () => {
    expect(parseRetryAfter('Thu, 01 Jan 2026 00:00:45 GMT', now)).toBe(45);
  });

  it('clamps a past HTTP-date to 0', () => {
    expect(parseRetryAfter('Wed, 31 Dec 2025 23:59:00 GMT', now)).toBe(0);
  });

  it('rejects garbage, negative and fractional values', () => {
    expect(parseRetryAfter('soon', now)).toBeNull();
    expect(parseRetryAfter('-5', now)).toBeNull();
    expect(parseRetryAfter('1.5', now)).toBeNull();
  });
});

describe('calculateRetryDelay', () => {
  describe('exponential backoff (backoffFactor * 2^n for the n-th retry)', () => {
    it.each([
      [0, 2000],
      [1, 4000],
      [2, 8000],
      [3, 16000],
      [4, 32000],
    ])('retry index %i waits %ims without jitter', (attempt, expected) => {
      expect(calculateRetryDelay(attempt, NO_JITTER)).toBe(expected);
    });

    it('applies full jitter: a random fraction of the backoff', () => {
      const config = { ...DEFAULT_RETRY_CONFIG, backoffJitter: 1 };
      expect(calculateRetryDelay(1, config, undefined, () => 0)).toBe(0);
      expect(calculateRetryDelay(1, config, undefined, () => 0.25)).toBe(1000);
      expect(calculateRetryDelay(1, config, undefined, () => 0.5)).toBe(2000);
    });

    it('applies partial jitter within [1 - jitter, 1] of the backoff', () => {
      const config = { ...DEFAULT_RETRY_CONFIG, backoffJitter: 0.5 };
      expect(calculateRetryDelay(0, config, undefined, () => 0)).toBe(1000);
      expect(calculateRetryDelay(0, config, undefined, () => 0.999999)).toBeCloseTo(2000, 0);
    });

    it('caps the backoff at maxBackoffSeconds', () => {
      expect(calculateRetryDelay(10, NO_JITTER)).toBe(120_000);
      expect(calculateRetryDelay(3, { ...NO_JITTER, maxBackoffSeconds: 5 })).toBe(5000);
    });

    it('scales with backoffFactor and returns 0 when it is 0', () => {
      expect(calculateRetryDelay(0, { ...NO_JITTER, backoffFactor: 0.5 })).toBe(1000);
      expect(calculateRetryDelay(2, { ...NO_JITTER, backoffFactor: 0 })).toBe(0);
    });
  });

  describe('Retry-After', () => {
    it('uses delta-seconds over backoff', () => {
      expect(calculateRetryDelay(0, NO_JITTER, status(429, { 'Retry-After': '30' }))).toBe(30_000);
    });

    it('uses an HTTP-date', () => {
      vi.useFakeTimers();
      vi.setSystemTime(Date.parse('2026-01-01T00:00:00Z'));
      const response = status(503, { 'Retry-After': 'Thu, 01 Jan 2026 00:00:10 GMT' });
      expect(calculateRetryDelay(0, NO_JITTER, response)).toBe(10_000);
      vi.useRealTimers();
    });

    it('is capped at maxBackoffSeconds', () => {
      expect(calculateRetryDelay(0, NO_JITTER, status(429, { 'Retry-After': '3600' }))).toBe(
        120_000
      );
    });

    it('falls back to backoff for an invalid or zero Retry-After', () => {
      expect(calculateRetryDelay(0, NO_JITTER, status(429, { 'Retry-After': 'soon' }))).toBe(2000);
      expect(calculateRetryDelay(0, NO_JITTER, status(429, { 'Retry-After': '0' }))).toBe(2000);
    });

    it('is ignored when respectRetryAfter is false', () => {
      const config = { ...NO_JITTER, respectRetryAfter: false };
      expect(calculateRetryDelay(0, config, status(429, { 'Retry-After': '30' }))).toBe(2000);
    });
  });
});

describe('createResilientFetch', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  function resilient(retry: Partial<RetryConfig> = {}): typeof fetch {
    return createResilientFetch({
      baseFetch: mockFetch as unknown as typeof fetch,
      retry: { backoffJitter: 0, ...retry },
    });
  }

  it('returns a successful response immediately', async () => {
    mockFetch.mockResolvedValueOnce(status(200));
    const response = await resilient()('https://api.example.com/test');
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('returns a non-retryable error response immediately', async () => {
    mockFetch.mockResolvedValueOnce(status(404));
    const response = await resilient()('https://api.example.com/test');
    expect(response.status).toBe(404);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('waits the backoff delay before retrying a 429', async () => {
    mockFetch.mockResolvedValueOnce(status(429)).mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test');

    await vi.advanceTimersByTimeAsync(1999);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    expect((await pending).status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('waits exactly Retry-After seconds (delta form) before retrying', async () => {
    mockFetch
      .mockResolvedValueOnce(status(429, { 'Retry-After': '7' }))
      .mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test', { method: 'POST', body: '{}' });

    await vi.advanceTimersByTimeAsync(6999);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    expect((await pending).status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('waits until the Retry-After HTTP-date before retrying', async () => {
    vi.setSystemTime(Date.parse('2026-01-01T00:00:00Z'));
    mockFetch
      .mockResolvedValueOnce(status(503, { 'Retry-After': 'Thu, 01 Jan 2026 00:00:05 GMT' }))
      .mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test');

    await vi.advanceTimersByTimeAsync(4999);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    expect((await pending).status).toBe(200);
  });

  it('uses growing backoff between successive retries', async () => {
    mockFetch.mockResolvedValue(status(502));
    const pending = resilient({ maxRetries: 3 })('https://api.example.com/test');

    // Waits: 2s, 4s, 8s.
    await vi.advanceTimersByTimeAsync(2000);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(3999);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(1);
    expect(mockFetch).toHaveBeenCalledTimes(3);
    await vi.advanceTimersByTimeAsync(8000);
    expect(mockFetch).toHaveBeenCalledTimes(4);

    expect((await pending).status).toBe(502);
  });

  it('returns the final response once retries are exhausted', async () => {
    mockFetch.mockResolvedValue(status(429));
    const pending = resilient({ maxRetries: 2 })('https://api.example.com/test');

    await vi.advanceTimersByTimeAsync(2000 + 4000);

    const response = await pending;
    expect(response.status).toBe(429);
    expect(mockFetch).toHaveBeenCalledTimes(3); // initial + 2 retries
  });

  it('does not retry at all when maxRetries is 0', async () => {
    mockFetch.mockResolvedValue(status(503));
    const response = await resilient({ maxRetries: 0 })('https://api.example.com/test');
    expect(response.status).toBe(503);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it.each(['POST', 'PATCH'])('retries %s on 429', async (method) => {
    mockFetch.mockResolvedValueOnce(status(429)).mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test', { method, body: '{}' });
    await vi.advanceTimersByTimeAsync(2000);
    expect((await pending).status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it.each(['POST', 'PATCH'])('does NOT retry %s on 503', async (method) => {
    mockFetch.mockResolvedValue(status(503));
    const response = await resilient()('https://api.example.com/test', { method, body: '{}' });
    expect(response.status).toBe(503);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('reads the method from a Request when no init is given (SDK call style)', async () => {
    mockFetch.mockResolvedValue(status(503));
    const request = new Request('https://api.example.com/test', { method: 'POST', body: '{}' });
    const response = await resilient()(request);
    expect(response.status).toBe(503);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('replays a Request body on every attempt', async () => {
    mockFetch.mockResolvedValueOnce(status(429)).mockResolvedValueOnce(status(200));
    const request = new Request('https://api.example.com/test', {
      method: 'POST',
      body: JSON.stringify({ name: 'Widget' }),
    });
    const pending = resilient()(request);
    await vi.advanceTimersByTimeAsync(2000);
    await pending;

    const bodies = await Promise.all(
      mockFetch.mock.calls.map(([input]) => (input as Request).text())
    );
    expect(bodies).toEqual(['{"name":"Widget"}', '{"name":"Widget"}']);
  });

  it('retries network errors (TypeError) with backoff', async () => {
    mockFetch
      .mockRejectedValueOnce(new TypeError('fetch failed'))
      .mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test');

    await vi.advanceTimersByTimeAsync(1999);
    expect(mockFetch).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);

    expect((await pending).status).toBe(200);
  });

  it('retries network errors for POST too (matches httpx-retries)', async () => {
    mockFetch
      .mockRejectedValueOnce(new TypeError('fetch failed'))
      .mockResolvedValueOnce(status(200));
    const pending = resilient()('https://api.example.com/test', { method: 'POST', body: '{}' });
    await vi.advanceTimersByTimeAsync(2000);
    expect((await pending).status).toBe(200);
  });

  it('throws the last network error once retries are exhausted', async () => {
    mockFetch.mockRejectedValue(new TypeError('fetch failed'));
    const pending = resilient({ maxRetries: 2 })('https://api.example.com/test');
    const assertion = expect(pending).rejects.toThrow('fetch failed');

    await vi.advanceTimersByTimeAsync(2000 + 4000);

    await assertion;
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('does not retry non-network errors', async () => {
    mockFetch.mockRejectedValue(new Error('programming error'));
    await expect(resilient()('https://api.example.com/test')).rejects.toThrow('programming error');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('stops waiting and rejects when the caller aborts during backoff', async () => {
    mockFetch.mockResolvedValue(status(503));
    const controller = new AbortController();
    const pending = resilient()('https://api.example.com/test', { signal: controller.signal });
    const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });

    await vi.advanceTimersByTimeAsync(500);
    controller.abort();

    await assertion;
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('does not retry a fetch rejected because the caller aborted', async () => {
    const controller = new AbortController();
    mockFetch.mockImplementation(() => {
      controller.abort();
      return Promise.reject(new TypeError('aborted mid-flight'));
    });
    await expect(
      resilient()('https://api.example.com/test', { signal: controller.signal })
    ).rejects.toThrow('aborted mid-flight');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('rejects invalid configuration', () => {
    expect(() => resilient({ maxRetries: -1 })).toThrow(/maxRetries/);
    expect(() => resilient({ backoffJitter: 2 })).toThrow(/backoffJitter/);
    expect(() => resilient({ maxBackoffSeconds: 0 })).toThrow(/maxBackoffSeconds/);
    expect(() => resilient({ backoffFactor: -1 })).toThrow(/backoffFactor/);
  });
});
