/**
 * Katana OpenAPI Client for TypeScript/JavaScript
 *
 * A resilient client for the Katana Manufacturing ERP API with:
 * - Automatic retries with exponential backoff + jitter (Retry-After aware)
 * - Proactive, header-adaptive rate limiting (X-Ratelimit-*)
 * - Per-attempt timeouts and abort-signal support
 * - Automatic pagination
 * - Typed error handling
 *
 * @example
 * ```typescript
 * import { KatanaClient } from 'katana-openapi-client';
 *
 * const client = await KatanaClient.create({ apiKey: 'your-api-key' });
 * const response = await client.get('/products');
 * const data = await response.json();
 * ```
 *
 * @example Types-only import
 * ```typescript
 * import type { Product, SalesOrder } from 'katana-openapi-client/types';
 * ```
 */

// Re-export the main client
export { KatanaClient, type KatanaClientOptions, type KatanaRequestOptions } from './client.js';

// Re-export error types and utilities.
// `ValidationErrorDetail` (the Ajv-style union) comes from the generated types
// via `export * from './types.js'` below — not re-declared here.
export {
  AuthenticationError,
  KatanaError,
  NetworkError,
  parseError,
  RateLimitError,
  ServerError,
  ValidationError,
} from './errors.js';
// Re-export the Client type for advanced usage
export type { Client } from './generated/client/types.gen.js';
// Re-export generated SDK functions for direct API access
export * from './generated/sdk.gen.js';
// Response helpers for generated SDK results (parity with the Python client's utils)
export {
  getError,
  getErrorMessage,
  isError,
  isSuccess,
  type ListItem,
  type ListResultGuard,
  type SdkResult,
  type SuccessData,
  unwrap,
  unwrapData,
} from './responses.js';
// Re-export transport utilities for advanced usage (custom fetch chains)
export { createErrorLoggingFetch } from './transport/errorLogging.js';
export {
  createPaginatedFetch,
  DEFAULT_PAGINATION_CONFIG,
  type PaginatedResponse,
  type PaginationConfig,
  type PaginationInfo,
} from './transport/pagination.js';
export {
  createRateLimitedFetch,
  DEFAULT_RATE_LIMIT_CONFIG,
  type RateLimitConfig,
  type RateLimitedFetchOptions,
} from './transport/rateLimit.js';
export {
  calculateRetryDelay,
  createResilientFetch,
  DEFAULT_RETRY_CONFIG,
  isRetryableError,
  parseRetryAfter,
  type ResilientFetchOptions,
  type RetryConfig,
  shouldRetry,
} from './transport/resilient.js';
export type { TransportLogger } from './transport/shared.js';
export { createTimeoutFetch, DEFAULT_TIMEOUT_MS } from './transport/timeout.js';

// Re-export all generated types for convenience
export * from './types.js';
