/**
 * Katana OpenAPI Client for TypeScript/JavaScript
 *
 * A resilient client for the Katana Manufacturing ERP API with:
 * - Automatic retries with exponential backoff
 * - Rate limiting awareness (429 handling)
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
export { KatanaClient, type KatanaClientOptions } from './client.js';

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
export {
  createPaginatedFetch,
  DEFAULT_PAGINATION_CONFIG,
  type PaginatedResponse,
  type PaginationConfig,
} from './transport/pagination.js';
export {
  createRateLimitedFetch,
  DEFAULT_RATE_LIMIT_CONFIG,
  type RateLimitConfig,
  type RateLimitedFetchOptions,
} from './transport/rateLimit.js';
// Re-export transport utilities for advanced usage
export {
  createResilientFetch,
  DEFAULT_RETRY_CONFIG,
  type RetryConfig,
} from './transport/resilient.js';

// Re-export all generated types for convenience
export * from './types.js';
