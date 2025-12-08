/**
 * Resilient transport layer for Katana API
 *
 * Provides automatic retry with exponential backoff, rate limiting awareness,
 * and proper handling of different HTTP methods.
 *
 * Mirrors Python client's RateLimitAwareRetry pattern from katana_client.py
 */

/**
 * Configuration options for the retry mechanism
 */
export interface RetryConfig {
  /** Maximum number of retry attempts. Default: 5 */
  maxRetries: number;
  /** Base delay multiplier in seconds. Default: 1.0 (gives 1s, 2s, 4s, 8s, 16s) */
  backoffFactor: number;
  /** HTTP status codes that should trigger retries */
  retryStatusCodes: number[];
  /** Whether to respect the Retry-After header. Default: true */
  respectRetryAfter: boolean;
}

/**
 * Default retry configuration
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 5,
  backoffFactor: 1.0, // Exponential backoff: 1, 2, 4, 8, 16 seconds
  retryStatusCodes: [429, 502, 503, 504],
  respectRetryAfter: true,
};

/**
 * HTTP methods that are safe to retry for server errors (5xx)
 * Non-idempotent methods like POST/PATCH are NOT retried for server errors,
 * but ARE retried for 429 rate limiting.
 */
const IDEMPOTENT_METHODS = new Set(['GET', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE']);

/**
 * Determine if a request should be retried based on method and status code.
 *
 * Key behavior (mirrors Python RateLimitAwareRetry):
 * - 429 Rate Limiting: Retry ALL methods (including POST/PATCH)
 * - 5xx Server Errors: Only retry idempotent methods
 *
 * @param method - HTTP method
 * @param statusCode - Response status code
 * @param config - Retry configuration
 * @returns Whether the request should be retried
 */
export function shouldRetry(method: string, statusCode: number, config: RetryConfig): boolean {
  // Check if status code is in the retry list
  if (!config.retryStatusCodes.includes(statusCode)) {
    return false;
  }

  const upperMethod = method.toUpperCase();

  // 429: Retry all methods (rate limiting is safe to retry regardless of method)
  if (statusCode === 429) {
    return true;
  }

  // Other retryable errors (5xx): Only retry idempotent methods
  return IDEMPOTENT_METHODS.has(upperMethod);
}

/**
 * Calculate the delay before the next retry attempt.
 *
 * @param attempt - Current retry attempt number (0-indexed)
 * @param config - Retry configuration
 * @param response - Optional response to check for Retry-After header
 * @returns Delay in milliseconds
 */
export function calculateRetryDelay(
  attempt: number,
  config: RetryConfig,
  response?: Response
): number {
  // Check for Retry-After header
  if (config.respectRetryAfter && response) {
    const retryAfter = response.headers.get('Retry-After');
    if (retryAfter) {
      // Retry-After can be a number of seconds or a date
      const seconds = Number.parseInt(retryAfter, 10);
      if (!Number.isNaN(seconds)) {
        return seconds * 1000;
      }
      // Try parsing as a date
      const retryDate = Date.parse(retryAfter);
      if (!Number.isNaN(retryDate)) {
        const delayMs = retryDate - Date.now();
        if (delayMs > 0) {
          return delayMs;
        }
      }
    }
  }

  // Exponential backoff: 2^attempt * backoffFactor
  // attempt 0: 1s, attempt 1: 2s, attempt 2: 4s, attempt 3: 8s, attempt 4: 16s
  return 2 ** attempt * config.backoffFactor * 1000;
}

/**
 * Sleep for a specified number of milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
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
  logger?: {
    debug: (message: string, ...args: unknown[]) => void;
    info: (message: string, ...args: unknown[]) => void;
    warn: (message: string, ...args: unknown[]) => void;
    error: (message: string, ...args: unknown[]) => void;
  };
}

/**
 * Create a resilient fetch function that wraps the native fetch with retry logic.
 *
 * This function implements the same retry strategy as the Python client:
 * - Retries 429 (rate limit) for ALL HTTP methods
 * - Retries 5xx errors only for idempotent methods (GET, PUT, DELETE, etc.)
 * - Uses exponential backoff with Retry-After header support
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

  const baseFetch = options.baseFetch ?? globalThis.fetch;

  const logger = options.logger ?? {
    debug: () => {},
    info: () => {},
    warn: () => {},
    error: () => {},
  };

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const method = init?.method ?? 'GET';
    const url =
      typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;

    let lastResponse: Response | undefined;
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        const response = await baseFetch(input, init);

        // Success - return immediately
        if (response.ok) {
          return response;
        }

        lastResponse = response;

        // Check if we should retry
        if (attempt < config.maxRetries && shouldRetry(method, response.status, config)) {
          const delay = calculateRetryDelay(attempt, config, response);
          logger.info(
            `Request to ${url} returned ${response.status}. Retrying in ${delay}ms (attempt ${attempt + 1}/${config.maxRetries})`
          );
          await sleep(delay);
          continue;
        }

        // No retry - return the response as-is
        return response;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // Network errors are always retryable
        if (attempt < config.maxRetries) {
          const delay = calculateRetryDelay(attempt, config);
          logger.warn(
            `Request to ${url} failed with network error: ${lastError.message}. Retrying in ${delay}ms (attempt ${attempt + 1}/${config.maxRetries})`
          );
          await sleep(delay);
          continue;
        }

        // Max retries exceeded
        throw lastError;
      }
    }

    // If we have a response, return it (even if it was an error response)
    if (lastResponse) {
      return lastResponse;
    }

    // Should never get here, but throw the last error if we do
    throw lastError ?? new Error('Max retries exceeded');
  };
}
