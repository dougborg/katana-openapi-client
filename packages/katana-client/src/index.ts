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

// Re-export error types and utilities
export {
  KatanaError,
  AuthenticationError,
  RateLimitError,
  ValidationError,
  ServerError,
  NetworkError,
  parseError,
  type ValidationErrorDetail,
} from './errors.js';

// Re-export transport utilities for advanced usage
export {
  createResilientFetch,
  type RetryConfig,
  DEFAULT_RETRY_CONFIG,
} from './transport/resilient.js';

export {
  createPaginatedFetch,
  type PaginationConfig,
  DEFAULT_PAGINATION_CONFIG,
  type PaginatedResponse,
} from './transport/pagination.js';

// Re-export generated SDK functions for direct API access
export * from './generated/sdk.gen.js';

// Re-export the Client type for advanced usage
export type { Client } from './generated/client/types.gen.js';

// Re-export all generated types for convenience
export * from './types.js';
