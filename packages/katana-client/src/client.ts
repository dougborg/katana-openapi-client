/**
 * KatanaClient - The main entry point for the Katana API client
 *
 * Provides a resilient client with automatic retries, rate limiting,
 * and pagination - mirroring the Python client's behavior.
 */

import { createClient, createConfig } from './generated/client/index.js';
import type { Client } from './generated/client/types.gen.js';
import {
  DEFAULT_PAGINATION_CONFIG,
  type PaginationConfig,
  createPaginatedFetch,
} from './transport/pagination.js';
import {
  DEFAULT_RETRY_CONFIG,
  type RetryConfig,
  createResilientFetch,
} from './transport/resilient.js';

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
   * Default: 'https://api.katanamrp.com/v1'
   */
  baseUrl?: string;

  /**
   * Retry configuration for failed requests
   */
  retry?: Partial<RetryConfig>;

  /**
   * Pagination configuration for auto-pagination
   */
  pagination?: Partial<PaginationConfig>;

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
   * Optional logger for debugging
   */
  logger?: {
    debug: (message: string, ...args: unknown[]) => void;
    info: (message: string, ...args: unknown[]) => void;
    warn: (message: string, ...args: unknown[]) => void;
    error: (message: string, ...args: unknown[]) => void;
  };
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
 * Create a no-op logger
 */
function createNoOpLogger() {
  return {
    debug: () => {},
    info: () => {},
    warn: () => {},
    error: () => {},
  };
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
  private readonly logger: NonNullable<KatanaClientOptions['logger']>;
  private readonly _sdkClient: Client;

  private constructor(apiKey: string, options: Omit<KatanaClientOptions, 'apiKey'> = {}) {
    this.apiKey = apiKey;
    this.baseUrl = options.baseUrl ?? DEFAULT_BASE_URL;
    this.logger = options.logger ?? createNoOpLogger();

    const baseFetch = options.fetch ?? globalThis.fetch;

    // Create the fetch chain: base -> resilient (retry) -> paginated -> authenticated
    const retryConfig: RetryConfig = {
      ...DEFAULT_RETRY_CONFIG,
      ...options.retry,
    };

    const paginationConfig: PaginationConfig = {
      ...DEFAULT_PAGINATION_CONFIG,
      ...options.pagination,
    };

    // First wrap with retry logic
    const fetchWithRetry = createResilientFetch({
      baseFetch,
      retry: retryConfig,
      logger: this.logger,
    });

    // Then wrap with pagination (uses the retry-enabled fetch)
    const paginatedFetch = createPaginatedFetch(fetchWithRetry, {
      pagination: paginationConfig,
      autoPagination: options.autoPagination !== false,
      logger: this.logger,
    });

    // Finally wrap with authentication - this is the SINGLE source of auth
    this.authenticatedFetch = this.createAuthenticatedFetch(paginatedFetch);

    // Create SDK client with the same authenticated fetch
    this._sdkClient = createClient(
      createConfig({
        baseUrl: this.baseUrl,
        fetch: this.authenticatedFetch,
      })
    );
  }

  /**
   * Create a fetch function that automatically adds authentication headers.
   * This is the SINGLE location where auth headers are added.
   */
  private createAuthenticatedFetch(baseFetch: typeof fetch): typeof fetch {
    const apiKey = this.apiKey;

    return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
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
   * @param init - Fetch options (method, body, headers, etc.)
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
  async fetch(path: string, init?: RequestInit): Promise<Response> {
    // Build full URL
    const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`;

    // Use the single authenticated fetch (includes retry + pagination + auth)
    return this.authenticatedFetch(url, init);
  }

  /**
   * Make a GET request
   *
   * @param path - API path
   * @param params - Optional query parameters
   * @returns Promise resolving to the Response
   */
  async get(path: string, params?: Record<string, string | number | boolean>): Promise<Response> {
    let url = path;
    if (params && Object.keys(params).length > 0) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        searchParams.set(key, String(value));
      }
      url = `${path}?${searchParams.toString()}`;
    }
    return this.fetch(url, { method: 'GET' });
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
