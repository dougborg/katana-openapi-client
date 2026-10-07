/**
 * Retry transport layer for the Katana API.
 *
 * Mirrors the Python client's `RateLimitAwareRetry` + `httpx_retries.RetryTransport`
 * policy (katana_client.py `ResilientAsyncTransport`):
 *
 * - **Retryable methods**: HEAD, GET, PUT, DELETE, OPTIONS, TRACE, POST, PATCH.
 *   Anything else (e.g. CONNECT) is sent once, never retried.
 * - **Status codes** (default 429, 502, 503, 504):
 *   - 429 is retried for **every** retryable method, POST/PATCH included —
 *     a rate-limited request was never processed, so replaying it is safe.
 *   - 5xx codes are retried only for idempotent methods (HEAD, GET, PUT,
 *     DELETE, OPTIONS, TRACE) — never POST/PATCH, which might have been
 *     applied server-side before the error.
 * - **Network errors** (fetch `TypeError`s and per-attempt timeouts) are retried
 *   for every retryable method, matching httpx-retries' default
 *   `retry_on_exceptions` (timeouts, network errors, protocol errors). A caller
 *   abort is never retried.
 * - **Delay**: `Retry-After` (delta-seconds or HTTP-date) when present and
 *   positive, otherwise exponential backoff `backoffFactor * 2^n` seconds for the
 *   n-th retry (n = 1, 2, …) with full jitter, both capped at `maxBackoffSeconds`.
 * - **Exhaustion**: after `maxRetries` retries the last response is returned
 *   as-is (or the last network error is thrown).
 */

import {
  getMethod,
  getSignal,
  getUrl,
  isRequest,
  NOOP_LOGGER,
  sanitizeUrl,
  sleep,
  type TransportLogger,
} from './shared.js';

/**
 * Configuration options for the retry mechanism
 */
export interface RetryConfig {
  /** Maximum number of retry attempts (initial request not counted). Default: 5 */
  maxRetries: number;
  /**
   * Backoff multiplier in seconds. The n-th retry (n = 1, 2, …) waits up to
   * `backoffFactor * 2^n` seconds. Default: 1.0 (up to 2s, 4s, 8s, 16s, 32s).
   * `0` disables the backoff delay (Retry-After is still honoured).
   */
  backoffFactor: number;
  /**
   * Jitter fraction in [0, 1]. The backoff is multiplied by a random factor in
   * `[1 - backoffJitter, 1]`. Default: 1 (full jitter); 0 makes delays deterministic.
   */
  backoffJitter: number;
  /** Upper bound, in seconds, for any single wait (backoff or Retry-After). Default: 120 */
  maxBackoffSeconds: number;
  /** HTTP status codes that should trigger retries. Default: [429, 502, 503, 504] */
  retryStatusCodes: number[];
  /** Whether to respect the Retry-After header. Default: true */
  respectRetryAfter: boolean;
}

/**
 * Default retry configuration (identical to the Python client's defaults).
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 5,
  backoffFactor: 1.0,
  backoffJitter: 1.0,
  maxBackoffSeconds: 120,
  retryStatusCodes: [429, 502, 503, 504],
  respectRetryAfter: true,
};

/** Methods that are safe to retry after a server error (5xx). */
const IDEMPOTENT_METHODS = new Set(['HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS', 'TRACE']);

/** Methods that enter the retry loop at all (idempotent + POST/PATCH for 429). */
const RETRYABLE_METHODS = new Set([...IDEMPOTENT_METHODS, 'POST', 'PATCH']);

/**
 * Determine if a response should be retried based on method and status code.
 *
 * - 429 Rate Limiting: retry every retryable method (including POST/PATCH)
 * - 5xx Server Errors: only retry idempotent methods
 *
 * @param method - HTTP method
 * @param statusCode - Response status code
 * @param config - Retry configuration
 * @returns Whether the request should be retried
 */
export function shouldRetry(
  method: string,
  statusCode: number,
  config: Pick<RetryConfig, 'retryStatusCodes'>
): boolean {
  const upperMethod = method.toUpperCase();
  if (!RETRYABLE_METHODS.has(upperMethod)) {
    return false;
  }
  if (!config.retryStatusCodes.includes(statusCode)) {
    return false;
  }
  if (statusCode === 429) {
    return true;
  }
  return IDEMPOTENT_METHODS.has(upperMethod);
}

/**
 * Determine if a thrown fetch error is a transient network failure worth retrying.
 *
 * - Caller aborts (the request's own signal is aborted) are never retried.
 * - `TimeoutError` (the per-attempt timeout layer) is retried.
 * - `TypeError` is what `fetch` rejects with on connection failures
 *   (DNS, refused, reset, TLS) in both Node and browsers — retried.
 * - Everything else (`AbortError`, programming errors) propagates immediately.
 *
 * @param method - HTTP method of the failed request
 * @param error - The value the fetch rejected with
 * @param signal - The caller's abort signal, if any
 */
export function isRetryableError(method: string, error: unknown, signal?: AbortSignal): boolean {
  if (!RETRYABLE_METHODS.has(method.toUpperCase()) || signal?.aborted) {
    return false;
  }
  if (error instanceof TypeError) {
    return true;
  }
  return error instanceof Error && error.name === 'TimeoutError';
}

/**
 * Parse a `Retry-After` header value into seconds.
 *
 * Accepts delta-seconds (`"120"`) or an HTTP-date
 * (`"Wed, 21 Oct 2015 07:28:00 GMT"`); a date in the past yields 0.
 *
 * @param value - Raw header value
 * @param nowMs - Current epoch milliseconds (injectable for tests)
 * @returns Seconds to wait, or `null` when the value is unparseable
 */
export function parseRetryAfter(value: string, nowMs: number = Date.now()): number | null {
  const trimmed = value.trim();
  if (/^\d+$/.test(trimmed)) {
    return Number(trimmed);
  }
  // HTTP-dates always carry month/day names; this keeps `Date.parse` (which is
  // lenient) from reading values like "-5" or "1.5" as dates.
  const dateMs = /[a-z]/i.test(trimmed) ? Date.parse(trimmed) : Number.NaN;
  if (Number.isNaN(dateMs)) {
    return null;
  }
  return Math.max(0, (dateMs - nowMs) / 1000);
}

/**
 * Calculate the delay before the next retry attempt.
 *
 * @param attempt - Zero-based retry index (0 = the first retry)
 * @param config - Retry configuration
 * @param response - Response to read `Retry-After` from (absent for network errors)
 * @param random - Uniform [0, 1) source for jitter (injectable for tests)
 * @returns Delay in milliseconds
 */
export function calculateRetryDelay(
  attempt: number,
  config: RetryConfig,
  response?: Response,
  random: () => number = Math.random
): number {
  const capSeconds = config.maxBackoffSeconds;

  if (config.respectRetryAfter && response) {
    const header = response.headers.get('Retry-After');
    if (header) {
      const seconds = parseRetryAfter(header);
      if (seconds !== null && seconds > 0) {
        return Math.min(seconds, capSeconds) * 1000;
      }
    }
  }

  if (config.backoffFactor === 0) {
    return 0;
  }
  // httpx-retries increments the attempt counter before sleeping, so the
  // first retry uses 2^1, the second 2^2, and so on.
  let seconds = config.backoffFactor * 2 ** (attempt + 1);
  if (config.backoffJitter > 0) {
    seconds *= 1 - config.backoffJitter + random() * config.backoffJitter;
  }
  return Math.min(seconds, capSeconds) * 1000;
}

/**
 * Options for creating a resilient fetch function
 */
export interface ResilientFetchOptions {
  /** Base fetch function to wrap. Default: globalThis.fetch */
  baseFetch?: typeof fetch;
  /** Retry configuration */
  retry?: Partial<RetryConfig>;
  /** Optional logger for debugging */
  logger?: TransportLogger;
}

function validateRetryConfig(config: RetryConfig): void {
  const problems: string[] = [];
  if (!Number.isInteger(config.maxRetries) || config.maxRetries < 0) {
    problems.push(`maxRetries must be a non-negative integer (got ${config.maxRetries})`);
  }
  if (!(config.backoffFactor >= 0)) {
    problems.push(`backoffFactor must be non-negative (got ${config.backoffFactor})`);
  }
  if (!(config.backoffJitter >= 0 && config.backoffJitter <= 1)) {
    problems.push(`backoffJitter must be between 0 and 1 (got ${config.backoffJitter})`);
  }
  if (!(config.maxBackoffSeconds > 0)) {
    problems.push(`maxBackoffSeconds must be positive (got ${config.maxBackoffSeconds})`);
  }
  if (problems.length > 0) {
    throw new Error(`createResilientFetch: ${problems.join('; ')}`);
  }
}

/**
 * Create a resilient fetch function that wraps the native fetch with retry logic.
 *
 * Works for both call styles: `fetch(url, init)` and `fetch(request)` (the
 * generated SDK's style). A `Request` body is cloned before each attempt so
 * POST/PATCH bodies survive a 429 replay.
 *
 * Abort-aware: if the caller's signal aborts while waiting between attempts,
 * the wait stops immediately and the promise rejects with the abort reason.
 *
 * @param options - Configuration options
 * @returns A fetch function with automatic retry capabilities
 *
 * @example
 * ```typescript
 * const resilientFetch = createResilientFetch({
 *   retry: { maxRetries: 3, backoffFactor: 1.0 }
 * });
 *
 * const response = await resilientFetch('https://api.katanamrp.com/v1/products');
 * ```
 */
export function createResilientFetch(options: ResilientFetchOptions = {}): typeof fetch {
  const config: RetryConfig = {
    ...DEFAULT_RETRY_CONFIG,
    ...options.retry,
  };
  validateRetryConfig(config);

  const baseFetch = options.baseFetch ?? globalThis.fetch;
  const logger = options.logger ?? NOOP_LOGGER;

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const method = getMethod(input, init);
    const signal = getSignal(input, init);
    const url = sanitizeUrl(getUrl(input));

    for (let attempt = 0; ; attempt++) {
      const canRetry = attempt < config.maxRetries;
      // Keep the original Request unconsumed so a later attempt can replay its body.
      const attemptInput = canRetry && isRequest(input) ? input.clone() : input;

      let response: Response;
      try {
        response = await baseFetch(attemptInput, init);
      } catch (error) {
        if (!canRetry || !isRetryableError(method, error, signal)) {
          throw error;
        }
        const delay = calculateRetryDelay(attempt, config);
        const message = error instanceof Error ? error.message : String(error);
        logger.warn(
          `${method} ${url} failed with network error: ${message}. Retrying in ${Math.round(delay)}ms (retry ${attempt + 1}/${config.maxRetries})`
        );
        await sleep(delay, signal);
        continue;
      }

      if (!canRetry || !shouldRetry(method, response.status, config)) {
        return response;
      }

      const delay = calculateRetryDelay(attempt, config, response);
      logger.info(
        `${method} ${url} returned ${response.status}. Retrying in ${Math.round(delay)}ms (retry ${attempt + 1}/${config.maxRetries})`
      );
      // Release the discarded response's connection before waiting.
      await response.body?.cancel().catch(() => {});
      await sleep(delay, signal);
    }
  };
}
