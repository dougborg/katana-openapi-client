/**
 * Per-attempt request timeout layer.
 *
 * Mirrors the Python client's `timeout=30.0` (an httpx per-request timeout):
 * each individual HTTP attempt is aborted with a `TimeoutError` if no response
 * headers arrive within `timeoutMs`. The retry layer treats that `TimeoutError`
 * as a transient network failure (httpx-retries retries `TimeoutException`),
 * while a caller-initiated abort is never retried.
 *
 * Placed innermost (directly above the base fetch) so time spent waiting on the
 * rate limiter or between retries never counts against a single attempt.
 *
 * The timer covers the wait for response headers; reading the body afterwards
 * is not bounded (pass your own `signal` if you need an overall deadline).
 */

import { getSignal } from './shared.js';

/** Default per-attempt timeout (matches the Python client's 30 s). */
export const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Wrap a fetch function so every call is aborted after `timeoutMs`.
 *
 * @param baseFetch - The fetch function to wrap.
 * @param timeoutMs - Per-attempt timeout in milliseconds (must be positive).
 * @returns A fetch function that rejects with a `TimeoutError` on timeout.
 */
export function createTimeoutFetch(baseFetch: typeof fetch, timeoutMs: number): typeof fetch {
  if (!(timeoutMs > 0)) {
    throw new Error(
      `createTimeoutFetch: timeoutMs must be positive (got ${timeoutMs}). To disable the timeout, omit this layer (or, via KatanaClient, set \`timeoutMs: null\`).`
    );
  }

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      controller.abort(new DOMException(`Request timed out after ${timeoutMs}ms`, 'TimeoutError'));
    }, timeoutMs);

    const callerSignal = getSignal(input, init);
    const signal = callerSignal ? anySignal(callerSignal, controller.signal) : controller.signal;

    try {
      return await baseFetch(input, { ...init, signal });
    } finally {
      clearTimeout(timer);
    }
  };
}

/**
 * Combine the caller's signal with the timeout signal. Uses `AbortSignal.any`
 * (Node >= 20.3, all evergreen browsers) and falls back to manual forwarding.
 * The caller's abort reason is preserved, so the retry layer can tell a caller
 * abort apart from a timeout.
 */
function anySignal(callerSignal: AbortSignal, timeoutSignal: AbortSignal): AbortSignal {
  if (typeof AbortSignal.any === 'function') {
    return AbortSignal.any([callerSignal, timeoutSignal]);
  }
  const combined = new AbortController();
  const forward = (source: AbortSignal): void => {
    if (source.aborted) {
      combined.abort(source.reason);
    } else {
      source.addEventListener('abort', () => combined.abort(source.reason), { once: true });
    }
  };
  forward(callerSignal);
  forward(timeoutSignal);
  return combined.signal;
}
