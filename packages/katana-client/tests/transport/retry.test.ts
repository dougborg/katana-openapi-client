/**
 * Tests for the resilient retry transport
 *
 * These tests mirror the Python client's test_rate_limit_retry.py
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  DEFAULT_RETRY_CONFIG,
  calculateRetryDelay,
  createResilientFetch,
  shouldRetry,
} from '../../src/transport/resilient.js';

describe('shouldRetry', () => {
  const config = DEFAULT_RETRY_CONFIG;

  describe('429 Rate Limiting', () => {
    it('should retry GET requests on 429', () => {
      expect(shouldRetry('GET', 429, config)).toBe(true);
    });

    it('should retry POST requests on 429', () => {
      expect(shouldRetry('POST', 429, config)).toBe(true);
    });

    it('should retry PATCH requests on 429', () => {
      expect(shouldRetry('PATCH', 429, config)).toBe(true);
    });

    it('should retry PUT requests on 429', () => {
      expect(shouldRetry('PUT', 429, config)).toBe(true);
    });

    it('should retry DELETE requests on 429', () => {
      expect(shouldRetry('DELETE', 429, config)).toBe(true);
    });
  });

  describe('5xx Server Errors', () => {
    it('should retry GET requests on 502', () => {
      expect(shouldRetry('GET', 502, config)).toBe(true);
    });

    it('should retry GET requests on 503', () => {
      expect(shouldRetry('GET', 503, config)).toBe(true);
    });

    it('should retry GET requests on 504', () => {
      expect(shouldRetry('GET', 504, config)).toBe(true);
    });

    it('should NOT retry POST requests on 502', () => {
      expect(shouldRetry('POST', 502, config)).toBe(false);
    });

    it('should NOT retry PATCH requests on 503', () => {
      expect(shouldRetry('PATCH', 503, config)).toBe(false);
    });

    it('should retry PUT requests on 504 (idempotent)', () => {
      expect(shouldRetry('PUT', 504, config)).toBe(true);
    });

    it('should retry DELETE requests on 502 (idempotent)', () => {
      expect(shouldRetry('DELETE', 502, config)).toBe(true);
    });
  });

  describe('Non-retryable Status Codes', () => {
    it('should NOT retry on 400 Bad Request', () => {
      expect(shouldRetry('GET', 400, config)).toBe(false);
    });

    it('should NOT retry on 401 Unauthorized', () => {
      expect(shouldRetry('GET', 401, config)).toBe(false);
    });

    it('should NOT retry on 404 Not Found', () => {
      expect(shouldRetry('GET', 404, config)).toBe(false);
    });

    it('should NOT retry on 422 Validation Error', () => {
      expect(shouldRetry('POST', 422, config)).toBe(false);
    });

    it('should NOT retry on 500 Internal Server Error', () => {
      expect(shouldRetry('GET', 500, config)).toBe(false);
    });
  });

  describe('Case Insensitivity', () => {
    it('should handle lowercase methods', () => {
      expect(shouldRetry('get', 429, config)).toBe(true);
      expect(shouldRetry('post', 429, config)).toBe(true);
    });

    it('should handle mixed case methods', () => {
      expect(shouldRetry('Get', 429, config)).toBe(true);
      expect(shouldRetry('Post', 429, config)).toBe(true);
    });
  });
});

describe('calculateRetryDelay', () => {
  const config = { ...DEFAULT_RETRY_CONFIG, backoffFactor: 1.0 };

  describe('Exponential Backoff', () => {
    it('should return 1s for attempt 0', () => {
      expect(calculateRetryDelay(0, config)).toBe(1000);
    });

    it('should return 2s for attempt 1', () => {
      expect(calculateRetryDelay(1, config)).toBe(2000);
    });

    it('should return 4s for attempt 2', () => {
      expect(calculateRetryDelay(2, config)).toBe(4000);
    });

    it('should return 8s for attempt 3', () => {
      expect(calculateRetryDelay(3, config)).toBe(8000);
    });

    it('should return 16s for attempt 4', () => {
      expect(calculateRetryDelay(4, config)).toBe(16000);
    });
  });

  describe('Retry-After Header', () => {
    it('should respect Retry-After header in seconds', () => {
      const headers = new Headers({ 'Retry-After': '30' });
      const response = new Response(null, { status: 429, headers });
      expect(calculateRetryDelay(0, config, response)).toBe(30000);
    });

    it('should fall back to exponential backoff for invalid Retry-After', () => {
      const headers = new Headers({ 'Retry-After': 'invalid' });
      const response = new Response(null, { status: 429, headers });
      expect(calculateRetryDelay(0, config, response)).toBe(1000);
    });

    it('should ignore Retry-After when respectRetryAfter is false', () => {
      const configNoRetryAfter = { ...config, respectRetryAfter: false };
      const headers = new Headers({ 'Retry-After': '30' });
      const response = new Response(null, { status: 429, headers });
      expect(calculateRetryDelay(0, configNoRetryAfter, response)).toBe(1000);
    });
  });

  describe('Backoff Factor', () => {
    it('should apply custom backoff factor', () => {
      const customConfig = { ...config, backoffFactor: 0.5 };
      expect(calculateRetryDelay(0, customConfig)).toBe(500);
      expect(calculateRetryDelay(1, customConfig)).toBe(1000);
      expect(calculateRetryDelay(2, customConfig)).toBe(2000);
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

  it('should return successful response immediately', async () => {
    const successResponse = new Response(JSON.stringify({ data: 'test' }), { status: 200 });
    mockFetch.mockResolvedValueOnce(successResponse);

    const resilientFetch = createResilientFetch({ baseFetch: mockFetch });
    const response = await resilientFetch('https://api.example.com/test');

    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should return non-retryable error response immediately', async () => {
    const errorResponse = new Response(JSON.stringify({ error: 'Not Found' }), { status: 404 });
    mockFetch.mockResolvedValueOnce(errorResponse);

    const resilientFetch = createResilientFetch({ baseFetch: mockFetch });
    const response = await resilientFetch('https://api.example.com/test');

    expect(response.status).toBe(404);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('should retry on 429 and succeed', async () => {
    const rateLimitResponse = new Response(null, { status: 429 });
    const successResponse = new Response(JSON.stringify({ data: 'test' }), { status: 200 });

    mockFetch.mockResolvedValueOnce(rateLimitResponse).mockResolvedValueOnce(successResponse);

    const resilientFetch = createResilientFetch({
      baseFetch: mockFetch,
      retry: { maxRetries: 3 },
    });

    const responsePromise = resilientFetch('https://api.example.com/test');

    // Advance timers for retry delay
    await vi.advanceTimersByTimeAsync(1000);

    const response = await responsePromise;
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should return last error after max retries', async () => {
    const rateLimitResponse = new Response(null, { status: 429 });
    mockFetch.mockResolvedValue(rateLimitResponse);

    const resilientFetch = createResilientFetch({
      baseFetch: mockFetch,
      retry: { maxRetries: 2 },
    });

    const responsePromise = resilientFetch('https://api.example.com/test');

    // Advance through all retries
    await vi.advanceTimersByTimeAsync(1000); // First retry
    await vi.advanceTimersByTimeAsync(2000); // Second retry

    const response = await responsePromise;
    expect(response.status).toBe(429);
    expect(mockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries
  });

  it('should retry network errors', async () => {
    const networkError = new Error('Network error');
    const successResponse = new Response(JSON.stringify({ data: 'test' }), { status: 200 });

    mockFetch.mockRejectedValueOnce(networkError).mockResolvedValueOnce(successResponse);

    const resilientFetch = createResilientFetch({
      baseFetch: mockFetch,
      retry: { maxRetries: 3 },
    });

    const responsePromise = resilientFetch('https://api.example.com/test');

    // Advance timers for retry delay
    await vi.advanceTimersByTimeAsync(1000);

    const response = await responsePromise;
    expect(response.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('should throw after max retries on persistent network error', async () => {
    // This test uses real timers with minimal delays to avoid fake timer + rejection issues
    vi.useRealTimers();

    const networkError = new Error('Network error');
    const realMockFetch = vi.fn().mockRejectedValue(networkError);

    const resilientFetch = createResilientFetch({
      baseFetch: realMockFetch,
      retry: {
        maxRetries: 2,
        backoffFactor: 0.001, // 1ms, 2ms, 4ms delays
      },
    });

    await expect(resilientFetch('https://api.example.com/test')).rejects.toThrow('Network error');
    expect(realMockFetch).toHaveBeenCalledTimes(3); // Initial + 2 retries

    // Restore fake timers for subsequent tests
    vi.useFakeTimers();
  });
});
