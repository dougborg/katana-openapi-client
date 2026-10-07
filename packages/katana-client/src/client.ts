/**
 * KatanaClient - The main entry point for the Katana API client
 *
 * Provides a resilient client with automatic retries, rate limiting,
 * and pagination - mirroring the Python client's behavior.
 */

import { createClient, createConfig } from './generated/client/index.js';
import type { Client } from './generated/client/types.gen.js';
import { createErrorLoggingFetch } from './transport/errorLogging.js';
import {
  createPaginatedFetch,
  DEFAULT_PAGINATION_CONFIG,
  type PaginationConfig,
} from './transport/pagination.js';
import { createRateLimitedFetch, DEFAULT_RATE_LIMIT_CONFIG } from './transport/rateLimit.js';
import {
  createResilientFetch,
  DEFAULT_RETRY_CONFIG,
  type RetryConfig,
} from './transport/resilient.js';
import { isRequest, NOOP_LOGGER, type TransportLogger } from './transport/shared.js';
import { createTimeoutFetch, DEFAULT_TIMEOUT_MS } from './transport/timeout.js';

/**
 * Per-request overrides for auto-pagination (the TypeScript equivalent of the
 * Python client's `extensions={"auto_pagination": False}` / `{"max_items": N}`).
 */
export interface KatanaRequestOptions {
  /** Set `false` to fetch only the first page for this request. */
  autoPagination?: boolean;
  /** Stop collecting once this many items are gathered (overrides `pagination.maxItems`). */
  maxItems?: number;
}

/**
 * Configuration options for KatanaClient
 */
export interface KatanaClientOptions {
  /**
   * API key for authentication. If not provided, will look for:
   * 1. KATANA_API_KEY environment variable
   * 2. .env file (Node.js only)
   * 3. ~/.netrc file (Node.js only)
   */
  apiKey?: string;

  /**
   * Base URL for the Katana API.
   * Default: `KATANA_BASE_URL` environment variable, else 'https://api.katanamrp.com/v1'
   */
  baseUrl?: string;

  /**
   * Per-attempt request timeout in milliseconds (time until response headers
   * arrive). A timed-out attempt is retried like a network error.
   * Default: 30000 (matches the Python client). Pass `null` to disable.
   */
  timeoutMs?: number | null;

  /**
   * Retry configuration for failed requests
   */
  retry?: Partial<RetryConfig>;

  /**
   * Pagination configuration for auto-pagination
   */
  pagination?: Partial<PaginationConfig>;

  /**
   * Proactive request budget per minute. The client paces outgoing requests
   * through a token bucket and adapts to Katana's `X-Ratelimit-*` headers.
   * Default: 60. Pass `null` to disable proactive rate limiting entirely
   * (reactive 429 retry still applies).
   */
  requestsPerMinute?: number | null;

  /**
   * Whether auto-pagination is enabled by default.
   * Default: true
   */
  autoPagination?: boolean;

  /**
   * Optional custom fetch function to use as the base.
   * Default: globalThis.fetch
   */
  fetch?: typeof fetch;

  /**
   * Optional logger (e.g. `console`). Receives retry / rate-limit / pagination
   * events, and an `error` entry for every 4xx response (except 429).
   */
  logger?: TransportLogger;
}

/**
 * Default base URL for Katana API
 */
const DEFAULT_BASE_URL = 'https://api.katanamrp.com/v1';

/**
 * Resolve API key from various sources
 *
 * Priority order:
 * 1. Explicit apiKey parameter
 * 2. KATANA_API_KEY environment variable
 *
 * Note: This library does not load .env files automatically.
 * Use `node --env-file=.env` (Node.js 20.6+) or load env vars yourself.
 *
 * @param explicitKey - Explicitly provided API key
 * @returns Resolved API key
 * @throws Error if no API key is found
 */
function resolveApiKey(explicitKey?: string): string {
  // 1. Explicit key takes precedence
  if (explicitKey) {
    return explicitKey;
  }

  // 2. Check environment variable (works in both Node.js and browser with bundler support)
  if (typeof process !== 'undefined' && process.env?.KATANA_API_KEY) {
    return process.env.KATANA_API_KEY;
  }

  throw new Error(
    'API key required. Provide via: apiKey option or KATANA_API_KEY environment variable. ' +
      'Use `node --env-file=.env` to load from .env file.'
  );
}

/**
 * Resolve the base URL: explicit option, then `KATANA_BASE_URL`, then the default.
 */
function resolveBaseUrl(explicitUrl?: string): string {
  if (explicitUrl) {
    return explicitUrl;
  }
  if (typeof process !== 'undefined' && process.env?.KATANA_BASE_URL) {
    return process.env.KATANA_BASE_URL;
  }
  return DEFAULT_BASE_URL;
}

/**
 * KatanaClient - The main Katana API client with automatic resilience
 *
 * Features:
 * - Automatic retries with exponential backoff
 * - Rate limiting awareness (429 handling)
 * - Auto-pagination ON by default for GET requests
 * - Typed error handling
 *
 * @example Basic usage
 * ```typescript
 * const client = new KatanaClient({ apiKey: 'your-api-key' });
 *
 * // Make a request - auto-pagination collects all pages
 * const response = await client.fetch('/products');
 * const data = await response.json();
 * console.log(data.data); // All products from all pages
 * ```
 *
 * @example Disable auto-pagination for a single request
 * ```typescript
 * // Get only page 2
 * const response = await client.fetch('/products?page=2');
 * ```
 *
 * @example Custom configuration
 * ```typescript
 * const client = new KatanaClient({
 *   apiKey: 'your-api-key',
 *   retry: { maxRetries: 3 },
 *   pagination: { maxPages: 50, maxItems: 1000 },
 * });
 * ```
 */
export class KatanaClient {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly authenticatedFetch: typeof fetch;
  private readonly logger: TransportLogger;
  private readonly _sdkClient: Client;
  /** Retry-wrapped fetch shared by every pagination variant (one rate limiter). */
  private readonly retryingFetch: typeof fetch;
  private readonly paginationConfig: PaginationConfig;
  private readonly autoPagination: boolean;

  private constructor(apiKey: string, options: Omit<KatanaClientOptions, 'apiKey'> = {}) {
    this.apiKey = apiKey;
    this.baseUrl = resolveBaseUrl(options.baseUrl);
    this.logger = options.logger ?? NOOP_LOGGER;

    const baseFetch = options.fetch ?? globalThis.fetch;

    // Fetch chain (innermost -> outermost):
    //   base -> timeout -> rate-limit -> error-logging -> retry -> paginated -> authenticated
    // Rate limiting sits below retry and pagination so every actual HTTP
    // request — each retry attempt and each paginated page — consumes a token,
    // matching how Katana counts requests server-side (mirrors the Python
    // client's transport stack). The timeout is innermost so rate-limit and
    // backoff waits never count against an attempt.
    const retryConfig: RetryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      ...options.retry,
    };

    this.paginationConfig = {
      ...DEFAULT_PAGINATION_CONFIG,
      ...options.pagination,
    };
    this.autoPagination = options.autoPagination !== false;

    const timeoutMs = options.timeoutMs === undefined ? DEFAULT_TIMEOUT_MS : options.timeoutMs;
    const timedFetch = timeoutMs === null ? baseFetch : createTimeoutFetch(baseFetch, timeoutMs);

    // Proactive rate limiting. `requestsPerMinute: null` disables the layer
    // entirely; otherwise default to 60/min.
    const rateLimitedFetch =
      options.requestsPerMinute === null
        ? timedFetch
        : createRateLimitedFetch(timedFetch, {
            rateLimit: {
              ...DEFAULT_RATE_LIMIT_CONFIG,
              requestsPerMinute:
                options.requestsPerMinute ?? DEFAULT_RATE_LIMIT_CONFIG.requestsPerMinute,
            },
            logger: this.logger,
          });

    // 4xx logging only when a logger was supplied (it reads a body clone).
    const loggedFetch = options.logger
      ? createErrorLoggingFetch(rateLimitedFetch, options.logger)
      : rateLimitedFetch;

    this.retryingFetch = createResilientFetch({
      baseFetch: loggedFetch,
      retry: retryConfig,
      logger: this.logger,
    });

    // Pagination + authentication on top - auth is the SINGLE source of the header.
    this.authenticatedFetch = this.buildFetch({});

    // Create SDK client with the same authenticated fetch
    this._sdkClient = createClient(
      createConfig({
        baseUrl: this.baseUrl,
        fetch: this.authenticatedFetch,
      })
    );
  }

  /** Build the outer (pagination + auth) layers over the shared retrying fetch. */
  private buildFetch(requestOptions: KatanaRequestOptions): typeof fetch {
    const paginatedFetch = createPaginatedFetch(this.retryingFetch, {
      pagination: {
        ...this.paginationConfig,
        ...(requestOptions.maxItems === undefined ? {} : { maxItems: requestOptions.maxItems }),
      },
      autoPagination: requestOptions.autoPagination ?? this.autoPagination,
      logger: this.logger,
    });
    return this.createAuthenticatedFetch(paginatedFetch);
  }

  /**
   * Create a fetch function that automatically adds authentication headers.
   * This is the SINGLE location where auth headers are added.
   *
   * Handles both call styles: `fetch(url, init)` and the generated SDK's
   * `fetch(request)`. For a `Request`, its own headers, method, body and
   * signal are preserved and the result is passed on as a single `Request`.
   */
  private createAuthenticatedFetch(baseFetch: typeof fetch): typeof fetch {
    const apiKey = this.apiKey;

    return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      if (isRequest(input)) {
        const headers = new Headers(input.headers);
        new Headers(init?.headers).forEach((value, key) => {
          headers.set(key, value);
        });
        headers.set('Authorization', `Bearer ${apiKey}`);
        return baseFetch(new Request(input, { ...init, headers }));
      }

      const headers = new Headers(init?.headers);
      headers.set('Authorization', `Bearer ${apiKey}`);

      // Add Content-Type for requests with body if not already set
      if (!headers.has('Content-Type') && init?.body) {
        headers.set('Content-Type', 'application/json');
      }

      return baseFetch(input, {
        ...init,
        headers,
      });
    };
  }

  /**
   * A fetch function with per-request pagination overrides, for use with the
   * generated SDK's per-call `fetch` option (shares this client's rate limiter).
   *
   * @example
   * ```typescript
   * // First 200 products only
   * const { data } = await getAllProducts({
   *   client: katana.sdk,
   *   fetch: katana.fetchWith({ maxItems: 200 }),
   * });
   * ```
   */
  fetchWith(requestOptions: KatanaRequestOptions): typeof fetch {
    return this.buildFetch(requestOptions);
  }

  /**
   * Create a new KatanaClient instance
   *
   * @param options - Client configuration options
   * @returns Promise resolving to a configured KatanaClient
   *
   * @example
   * ```typescript
   * const client = await KatanaClient.create({ apiKey: 'your-api-key' });
   * ```
   */
  static async create(options: KatanaClientOptions = {}): Promise<KatanaClient> {
    const apiKey = resolveApiKey(options.apiKey);
    return new KatanaClient(apiKey, options);
  }

  /**
   * Create a KatanaClient synchronously with an explicit API key
   *
   * This is a convenience method when you already have the API key.
   * For automatic credential resolution, use `KatanaClient.create()`.
   *
   * @param apiKey - API key for authentication
   * @param options - Additional client options
   * @returns Configured KatanaClient instance
   *
   * @example
   * ```typescript
   * const client = KatanaClient.withApiKey('your-api-key');
   * ```
   */
  static withApiKey(
    apiKey: string,
    options: Omit<KatanaClientOptions, 'apiKey'> = {}
  ): KatanaClient {
    return new KatanaClient(apiKey, options);
  }

  /**
   * Make an authenticated request to the Katana API
   *
   * This method automatically:
   * - Adds authentication headers
   * - Retries on rate limiting and server errors
   * - Collects all pages for GET requests (auto-pagination)
   *
   * @param path - API path (e.g., '/products') or full URL
   * @param init - Fetch options (method, body, headers, signal, etc.)
   * @param requestOptions - Per-request pagination overrides
   * @returns Promise resolving to the Response
   *
   * @example GET request with auto-pagination
   * ```typescript
   * const response = await client.fetch('/products');
   * const { data } = await response.json();
   * // data contains all products from all pages
   * ```
   *
   * @example POST request
   * ```typescript
   * const response = await client.fetch('/products', {
   *   method: 'POST',
   *   body: JSON.stringify({ name: 'New Product', sku: 'SKU-001' }),
   * });
   * ```
   *
   * @example Disable auto-pagination
   * ```typescript
   * // Explicit page parameter disables auto-pagination
   * const response = await client.fetch('/products?page=2&limit=50');
   * ```
   */
  async fetch(
    path: string,
    init?: RequestInit,
    requestOptions?: KatanaRequestOptions
  ): Promise<Response> {
    // Build full URL
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;

    // Use the single authenticated fetch (includes retry + pagination + auth)
    const fetchFn = requestOptions ? this.buildFetch(requestOptions) : this.authenticatedFetch;
    return fetchFn(url, init);
  }

  /**
   * Make a GET request
   *
   * @param path - API path
   * @param params - Optional query parameters
   * @param requestOptions - Per-request pagination overrides (e.g. `{ maxItems: 200 }`)
   * @returns Promise resolving to the Response
   */
  async get(
    path: string,
    params?: Record<string, string | number | boolean>,
    requestOptions?: KatanaRequestOptions
  ): Promise<Response> {
    let url = path;
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        searchParams.set(key, String(value));
      }
      url = `${path}?${searchParams.toString()}`;
    }
    return this.fetch(url, { method: 'GET' }, requestOptions);
  }

  /**
   * Make a POST request
   *
   * @param path - API path
   * @param body - Request body (will be JSON stringified)
   * @returns Promise resolving to the Response
   */
  async post(path: string, body?: unknown): Promise<Response> {
    return this.fetch(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a PUT request
   *
   * @param path - API path
   * @param body - Request body (will be JSON stringified)
   * @returns Promise resolving to the Response
   */
  async put(path: string, body?: unknown): Promise<Response> {
    return this.fetch(path, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a PATCH request
   *
   * @param path - API path
   * @param body - Request body (will be JSON stringified)
   * @returns Promise resolving to the Response
   */
  async patch(path: string, body?: unknown): Promise<Response> {
    return this.fetch(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Make a DELETE request
   *
   * @param path - API path
   * @returns Promise resolving to the Response
   */
  async delete(path: string): Promise<Response> {
    return this.fetch(path, { method: 'DELETE' });
  }

  /**
   * Get the base URL configured for this client
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Get the underlying @hey-api/client-fetch Client instance
   *
   * This client is pre-configured with:
   * - Automatic retries with exponential backoff
   * - Rate limiting awareness (429 handling)
   * - Auto-pagination for GET requests
   * - Authentication via Bearer token
   *
   * Use this to call generated SDK functions with the resilient client:
   *
   * @example
   * ```typescript
   * import { getAllProducts } from 'katana-openapi-client';
   *
   * const client = await KatanaClient.create();
   * const { data, error } = await getAllProducts({ client: client.sdk });
   * ```
   */
  get sdk(): Client {
    return this._sdkClient;
  }

  /**
   * Get a configuration object for use with generated SDK functions
   *
   * @example
   * ```typescript
   * import { getAllProducts } from 'katana-openapi-client';
   *
   * const client = await KatanaClient.create();
   * const { data, error } = await getAllProducts(client.getConfig());
   * ```
   */
  getConfig(): { client: Client } {
    return { client: this._sdkClient };
  }
}
