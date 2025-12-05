/**
 * Auto-pagination transport layer for Katana API
 *
 * Provides transparent automatic pagination for GET requests,
 * collecting all pages automatically by default.
 *
 * Mirrors Python client's PaginationTransport pattern from katana_client.py
 */

/**
 * Pagination metadata returned from Katana API
 */
export interface PaginationInfo {
  /** Current page number */
  page?: number;
  /** Total number of pages */
  total_pages?: number;
  /** Total number of items across all pages */
  total_items?: number;
  /** Items per page */
  per_page?: number;
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

/**
 * Extract pagination information from response headers and body
 */
export function extractPaginationInfo(
  headers: Headers,
  body: Record<string, unknown>
): PaginationInfo | null {
  const info: PaginationInfo = {};

  // Check for X-Pagination header (JSON format)
  const xPagination = headers.get('X-Pagination');
  if (xPagination) {
    try {
      const parsed = JSON.parse(xPagination);
      return parsed as PaginationInfo;
    } catch {
      // Ignore parse errors, try other methods
    }
  }

  // Check for individual headers
  const xTotalPages = headers.get('X-Total-Pages');
  if (xTotalPages) {
    const parsed = parseInt(xTotalPages, 10);
    if (!isNaN(parsed)) {
      info.total_pages = parsed;
    }
  }

  const xCurrentPage = headers.get('X-Current-Page');
  if (xCurrentPage) {
    const parsed = parseInt(xCurrentPage, 10);
    if (!isNaN(parsed)) {
      info.page = parsed;
    }
  }

  // Check for pagination in response body
  if (body.pagination && typeof body.pagination === 'object') {
    Object.assign(info, body.pagination);
  } else if (
    body.meta &&
    typeof body.meta === 'object' &&
    (body.meta as Record<string, unknown>).pagination
  ) {
    Object.assign(info, (body.meta as Record<string, unknown>).pagination);
  }

  return Object.keys(info).length > 0 ? info : null;
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
  logger?: {
    debug: (message: string, ...args: unknown[]) => void;
    info: (message: string, ...args: unknown[]) => void;
    warn: (message: string, ...args: unknown[]) => void;
  };
}

/**
 * Create a fetch function with automatic pagination support.
 *
 * Auto-pagination behavior:
 * - ON by default for all GET requests
 * - Disabled when explicit `page` parameter is in URL
 * - Disabled when autoPagination option is false
 * - Only applies to GET requests
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
 * // Auto-paginate: collects all pages
 * const response = await paginatedFetch('https://api.katanamrp.com/v1/products');
 *
 * // Disable auto-pagination with explicit page
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

  const logger = options.logger ?? {
    debug: () => {},
    info: () => {},
    warn: () => {},
  };

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const method = init?.method ?? 'GET';

    // Only paginate GET requests
    if (method.toUpperCase() !== 'GET') {
      return baseFetch(input, init);
    }

    // Get the URL
    const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;

    // Check if auto-pagination should be disabled
    const hasExplicitPage = hasExplicitPageParam(url);

    if (!autoPaginationEnabled || hasExplicitPage) {
      return baseFetch(input, init);
    }

    // Perform auto-pagination
    return performPagination(baseFetch, url, init, config, logger);
  };
}

/**
 * Perform automatic pagination, collecting all pages
 */
async function performPagination(
  baseFetch: typeof fetch,
  baseUrl: string,
  init: RequestInit | undefined,
  config: PaginationConfig,
  logger: { debug: (msg: string, ...args: unknown[]) => void; info: (msg: string, ...args: unknown[]) => void; warn: (msg: string, ...args: unknown[]) => void }
): Promise<Response> {
  const allData: unknown[] = [];
  let totalPages: number | undefined;
  let lastResponse: Response | undefined;
  let pageNum = 1;

  logger.info(`Auto-paginating request: ${baseUrl}`);

  // Determine if URL is absolute by trying to parse it
  let isRelativeUrl: boolean;
  let url: URL;
  try {
    url = new URL(baseUrl);
    isRelativeUrl = false;
  } catch {
    // Failed to parse as absolute URL - treat as relative
    url = new URL(baseUrl, 'http://placeholder.local');
    isRelativeUrl = true;
  }

  for (pageNum = 1; pageNum <= config.maxPages; pageNum++) {
    // Update page parameter
    url.searchParams.set('page', String(pageNum));

    // Adjust limit if maxItems is set and we're approaching it
    if (config.maxItems !== undefined) {
      const remaining = config.maxItems - allData.length;
      if (remaining <= 0) {
        break;
      }

      const originalLimit = url.searchParams.get('limit');
      const limitToUse = originalLimit
        ? Math.min(parseInt(originalLimit, 10), remaining)
        : Math.min(config.defaultPageSize, remaining);
      url.searchParams.set('limit', String(limitToUse));
    }

    // Build the request URL
    const requestUrl = isRelativeUrl
      ? `${url.pathname}${url.search}`
      : url.toString();

    // Make the request
    const response = await baseFetch(requestUrl, init);
    lastResponse = response;

    // Check for errors
    if (!response.ok) {
      return response;
    }

    // Parse the response
    let body: Record<string, unknown>;
    try {
      body = await response.json();
    } catch {
      logger.warn(`Failed to parse paginated response as JSON`);
      return response;
    }

    // Extract pagination info
    const paginationInfo = extractPaginationInfo(response.headers, body);

    if (paginationInfo) {
      if (paginationInfo.total_pages !== undefined) {
        totalPages = paginationInfo.total_pages;
      }

      // Extract data items
      const items = Array.isArray(body.data)
        ? body.data
        : Array.isArray(body)
          ? body
          : [];
      allData.push(...items);

      // Check maxItems limit
      if (config.maxItems !== undefined && allData.length >= config.maxItems) {
        allData.splice(config.maxItems); // Truncate to exact limit
        logger.info(`Reached maxItems limit (${config.maxItems}), stopping pagination`);
        break;
      }

      // Check if we've collected all pages
      if ((totalPages && pageNum >= totalPages) || items.length === 0) {
        break;
      }

      logger.debug(
        `Collected page ${pageNum}/${totalPages ?? '?'}, items: ${items.length}, total: ${allData.length}`
      );
    } else {
      // No pagination info - treat as single page
      const items = Array.isArray(body.data)
        ? body.data
        : Array.isArray(body)
          ? body
          : [];
      allData.push(...items);

      // Apply maxItems limit
      if (config.maxItems !== undefined && allData.length > config.maxItems) {
        allData.splice(config.maxItems);
      }
      break;
    }
  }

  if (!lastResponse) {
    throw new Error('No response available after pagination');
  }

  // Build combined response data
  const combinedData: PaginatedResponse<unknown> = { data: allData };

  if (totalPages) {
    combinedData.pagination = {
      total_pages: totalPages,
      collected_pages: pageNum,
      total_items: allData.length,
      auto_paginated: true,
    };
  }

  logger.info(`Auto-pagination complete: collected ${allData.length} items from ${pageNum} pages`);

  // Create a new Response with combined data
  // Copy headers but remove content-encoding/length
  const headers = new Headers(lastResponse.headers);
  headers.delete('content-encoding');
  headers.delete('content-length');

  return new Response(JSON.stringify(combinedData), {
    status: 200,
    statusText: 'OK',
    headers,
  });
}
