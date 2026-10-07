/**
 * Auto-pagination transport layer for Katana API
 *
 * Mirrors the Python client's `PaginationTransport` (katana_client.py):
 *
 * - ON by default for GET requests with NO `page` parameter in the URL
 * - Uses 250 items per page (Katana's max) when the caller sets no `limit`;
 *   a caller-supplied positive `limit` is used per page instead
 * - ANY explicit `page` parameter disables auto-pagination (e.g. `?page=1`)
 * - Only GET requests are paginated (POST, PUT, … pass straight through)
 * - Stops at the last page (`total_pages`), on an empty page, at `maxPages`,
 *   or once `maxItems` items are collected
 * - A response WITHOUT pagination metadata (e.g. `GET /products/{id}`) is
 *   returned untouched — only `maxItems` truncation is applied to a list body
 * - A non-200 page, or a body that isn't JSON, is returned as-is
 * - Raw-array endpoints keep their shape: the combined result is a bare array
 */

import { getMethod, getUrl, isRequest, NOOP_LOGGER, type TransportLogger } from './shared.js';

/**
 * Pagination metadata returned from Katana API (header or body).
 */
export interface PaginationInfo {
  /** Current page number */
  page?: number;
  /** Total number of pages */
  total_pages?: number;
  /** Total number of items across all pages */
  total_items?: number;
  /** Total number of records (Katana's `X-Pagination` name for the item count) */
  total_records?: number;
  /** Items per page */
  per_page?: number;
  /** Whether this is the first page */
  first_page?: boolean;
  /** Whether this is the last page */
  last_page?: boolean;
  /** Any other pagination fields the server sends */
  [key: string]: unknown;
}

/**
 * Configuration options for pagination
 */
export interface PaginationConfig {
  /** Maximum number of pages to collect. Default: 100 */
  maxPages: number;
  /** Maximum number of items to collect (undefined = unlimited) */
  maxItems?: number;
  /** Default page size when not specified. Default: 250 (Katana API max) */
  defaultPageSize: number;
}

/**
 * Default pagination configuration
 */
export const DEFAULT_PAGINATION_CONFIG: PaginationConfig = {
  maxPages: 100,
  maxItems: undefined,
  defaultPageSize: 250, // Katana API max page size
};

/**
 * Response with pagination metadata
 */
export interface PaginatedResponse<T> {
  /** Combined data from all pages */
  data: T[];
  /** Pagination metadata (present when auto-paginated) */
  pagination?: {
    total_pages: number;
    collected_pages: number;
    total_items: number;
    auto_paginated: boolean;
  };
}

/** Pagination fields that must be integers for correct comparisons. */
const NUMERIC_FIELDS = [
  'page',
  'total_pages',
  'total_items',
  'limit',
  'offset',
  'count',
  'per_page',
  'current_page',
  'total_records',
];

/** Pagination fields Katana sends as `"true"` / `"false"` strings. */
const BOOLEAN_FIELDS = ['first_page', 'last_page'];

/**
 * Normalise pagination values: numeric strings become integers (so `"5" >= "41"`
 * string comparisons can't end pagination early) and `"true"`/`"false"` become
 * booleans. Unparseable values are dropped so fallbacks apply.
 */
export function normalizePaginationValues(info: Record<string, unknown>): PaginationInfo {
  const result: Record<string, unknown> = { ...info };
  for (const field of NUMERIC_FIELDS) {
    if (!(field in result)) continue;
    const value = result[field];
    if (typeof value === 'string') {
      const parsed = /^\s*-?\d+\s*$/.test(value) ? Number.parseInt(value, 10) : Number.NaN;
      if (Number.isNaN(parsed)) {
        delete result[field];
      } else {
        result[field] = parsed;
      }
    } else if (typeof value === 'number') {
      result[field] = Math.trunc(value);
    }
  }
  for (const field of BOOLEAN_FIELDS) {
    if (!(field in result)) continue;
    const value = result[field];
    if (typeof value === 'string') {
      const lower = value.toLowerCase();
      if (lower === 'true' || lower === 'false') {
        result[field] = lower === 'true';
      } else {
        delete result[field];
      }
    } else if (typeof value !== 'boolean') {
      result[field] = Boolean(value);
    }
  }
  return result as PaginationInfo;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Extract pagination information from response headers and body.
 *
 * Priority: a non-empty `X-Pagination` JSON object header wins outright;
 * otherwise `X-Total-Pages` / `X-Current-Page` headers are merged with a body
 * `pagination` (or `meta.pagination`) object. Values are normalised.
 */
export function extractPaginationInfo(headers: Headers, body: unknown): PaginationInfo | null {
  const xPagination = headers.get('X-Pagination');
  if (xPagination) {
    try {
      const parsed: unknown = JSON.parse(xPagination);
      if (isPlainObject(parsed)) {
        const normalized = normalizePaginationValues(parsed);
        if (Object.keys(normalized).length > 0) {
          return normalized;
        }
      }
    } catch {
      // Malformed header — fall through to the other sources.
    }
  }

  const info: Record<string, unknown> = {};

  const xTotalPages = headers.get('X-Total-Pages');
  if (xTotalPages) {
    const parsed = Number.parseInt(xTotalPages, 10);
    if (!Number.isNaN(parsed)) {
      info.total_pages = parsed;
    }
  }

  const xCurrentPage = headers.get('X-Current-Page');
  if (xCurrentPage) {
    const parsed = Number.parseInt(xCurrentPage, 10);
    if (!Number.isNaN(parsed)) {
      info.page = parsed;
    }
  }

  if (isPlainObject(body)) {
    if (isPlainObject(body.pagination)) {
      Object.assign(info, body.pagination);
    } else if (isPlainObject(body.meta) && isPlainObject(body.meta.pagination)) {
      Object.assign(info, body.meta.pagination);
    }
  }

  if (Object.keys(info).length === 0) {
    return null;
  }
  return normalizePaginationValues(info);
}

/**
 * Check if a URL has an explicit page parameter
 */
export function hasExplicitPageParam(url: string | URL): boolean {
  const urlObj = typeof url === 'string' ? new URL(url, 'http://dummy') : url;
  return urlObj.searchParams.has('page');
}

/**
 * Options for paginated fetch
 */
export interface PaginatedFetchOptions {
  /** Pagination configuration */
  pagination?: Partial<PaginationConfig>;
  /** Whether auto-pagination is enabled. Default: true */
  autoPagination?: boolean;
  /** Optional logger */
  logger?: Pick<TransportLogger, 'debug' | 'info' | 'warn'>;
}

/**
 * Create a fetch function with automatic pagination support.
 *
 * Works for both `fetch(url, init)` and the generated SDK's `fetch(request)`
 * call style; each page request keeps the original method, headers and abort
 * signal.
 *
 * @param baseFetch - Base fetch function to wrap
 * @param options - Pagination options
 * @returns A fetch function with automatic pagination
 *
 * @example
 * ```typescript
 * const paginatedFetch = createPaginatedFetch(fetch, {
 *   pagination: { maxPages: 50, maxItems: 1000 }
 * });
 *
 * // Auto-paginate: collects all pages (uses limit=250 per page)
 * const response = await paginatedFetch('https://api.katanamrp.com/v1/products');
 *
 * // Disable auto-pagination with explicit page (ANY page value)
 * const page2 = await paginatedFetch('https://api.katanamrp.com/v1/products?page=2');
 * ```
 */
export function createPaginatedFetch(
  baseFetch: typeof fetch,
  options: PaginatedFetchOptions = {}
): typeof fetch {
  const config: PaginationConfig = {
    ...DEFAULT_PAGINATION_CONFIG,
    ...options.pagination,
  };

  const autoPaginationEnabled = options.autoPagination !== false;
  const logger = options.logger ?? NOOP_LOGGER;

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    if (!autoPaginationEnabled || getMethod(input, init) !== 'GET') {
      return baseFetch(input, init);
    }
    if (hasExplicitPageParam(getUrl(input))) {
      return baseFetch(input, init);
    }
    return performPagination(baseFetch, input, init, config, logger);
  };
}

/** Rebuild the response with a new JSON body, keeping status and headers. */
function jsonResponse(body: unknown, source: Response): Response {
  const headers = new Headers(source.headers);
  headers.delete('content-encoding');
  headers.delete('content-length');
  return new Response(JSON.stringify(body), { status: 200, statusText: 'OK', headers });
}

/** Apply `maxItems` truncation to a single (non-paginated) body, preserving its shape. */
function truncateSingleResponse(
  response: Response,
  body: unknown,
  maxItems: number | undefined
): Response {
  if (maxItems === undefined) {
    return response;
  }
  if (Array.isArray(body) && body.length > maxItems) {
    return jsonResponse(body.slice(0, maxItems), response);
  }
  if (isPlainObject(body) && Array.isArray(body.data) && body.data.length > maxItems) {
    return jsonResponse({ ...body, data: body.data.slice(0, maxItems) }, response);
  }
  return response;
}

/**
 * Perform automatic pagination, collecting all pages
 */
async function performPagination(
  baseFetch: typeof fetch,
  input: RequestInfo | URL,
  init: RequestInit | undefined,
  config: PaginationConfig,
  logger: Pick<TransportLogger, 'debug' | 'info' | 'warn'>
): Promise<Response> {
  const allData: unknown[] = [];
  let totalPages: number | undefined;
  let lastResponse: Response | undefined;
  let originalIsRawList = false;
  let pageNum = 1;

  const baseUrl = getUrl(input);
  logger.info(`Auto-paginating request: ${baseUrl}`);

  // Relative URLs (only possible with string input) are resolved against a
  // placeholder origin and re-emitted relative.
  let isRelativeUrl = false;
  let url: URL;
  try {
    url = new URL(baseUrl);
  } catch {
    url = new URL(baseUrl, 'http://placeholder.local');
    isRelativeUrl = true;
  }

  const originalLimit = url.searchParams.get('limit');
  const parsedLimit = originalLimit ? Number.parseInt(originalLimit, 10) : Number.NaN;
  let pageSize = config.defaultPageSize;
  if (originalLimit !== null) {
    if (!Number.isNaN(parsedLimit) && parsedLimit > 0) {
      pageSize = parsedLimit;
    } else {
      logger.warn(
        `Invalid limit parameter ${JSON.stringify(originalLimit)}, using default ${config.defaultPageSize}`
      );
    }
  }

  for (pageNum = 1; pageNum <= config.maxPages; pageNum++) {
    let limit = pageSize;
    if (config.maxItems !== undefined) {
      const remaining = config.maxItems - allData.length;
      if (remaining <= 0) {
        break;
      }
      limit = Math.min(pageSize, remaining);
    }
    url.searchParams.set('page', String(pageNum));
    url.searchParams.set('limit', String(limit));

    const pageUrl = isRelativeUrl ? `${url.pathname}${url.search}` : url.toString();
    // A Request carries method/headers/signal itself — rebuild it for the new URL.
    const pageInput: RequestInfo = isRequest(input) ? new Request(pageUrl, input) : pageUrl;

    const response = await baseFetch(pageInput, init);
    lastResponse = response;

    if (response.status !== 200) {
      return response;
    }

    // Parse a clone so the untouched original can be returned when we bail out.
    let body: unknown;
    try {
      body = await response.clone().json();
    } catch {
      logger.warn('Failed to parse paginated response as JSON');
      return response;
    }

    if (pageNum === 1) {
      originalIsRawList = Array.isArray(body);
    }

    const paginationInfo = extractPaginationInfo(response.headers, body);
    if (!paginationInfo) {
      // Not a paginated endpoint (e.g. a single resource): return it as-is.
      if (pageNum === 1) {
        logger.debug('No pagination info found, returning single-page response');
        return truncateSingleResponse(response, body, config.maxItems);
      }
      // A later page without metadata still contributes its items, then stop.
      allData.push(...extractItems(body));
      break;
    }

    const currentPage = paginationInfo.page ?? pageNum;
    if (paginationInfo.total_pages !== undefined) {
      totalPages = paginationInfo.total_pages;
    }

    const items = extractItems(body);
    allData.push(...items);

    if (config.maxItems !== undefined && allData.length >= config.maxItems) {
      allData.splice(config.maxItems);
      logger.info(`Reached maxItems limit (${config.maxItems}), stopping pagination`);
      break;
    }

    if ((totalPages && currentPage >= totalPages) || items.length === 0) {
      break;
    }

    logger.debug(
      `Collected page ${currentPage}/${totalPages ?? '?'}, items: ${items.length}, total: ${allData.length}`
    );
  }

  if (!lastResponse) {
    throw new Error('No response available after pagination');
  }

  // The loop variable overshoots by one when it runs to maxPages.
  const collectedPages = Math.min(pageNum, config.maxPages);
  logger.info(
    `Auto-pagination complete: collected ${allData.length} items from ${collectedPages} pages`
  );

  if (originalIsRawList) {
    return jsonResponse(allData, lastResponse);
  }

  const combined: PaginatedResponse<unknown> = { data: allData };
  if (totalPages) {
    combined.pagination = {
      total_pages: totalPages,
      collected_pages: collectedPages,
      total_items: allData.length,
      auto_paginated: true,
    };
  }
  return jsonResponse(combined, lastResponse);
}

/** The item array of a page body: a bare array, or the `data` array of an object. */
function extractItems(body: unknown): unknown[] {
  if (Array.isArray(body)) {
    return body;
  }
  if (isPlainObject(body) && Array.isArray(body.data)) {
    return body.data;
  }
  return [];
}
