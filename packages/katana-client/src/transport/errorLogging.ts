/**
 * Client-error logging layer.
 *
 * Mirrors the Python client's `ErrorLoggingTransport`: every 4xx response is
 * logged at `error` level with the method, a sanitised URL (sensitive query
 * values redacted) and the parsed Katana error message — for 422s that is the
 * formatted, multi-line Ajv validation summary from `parseError`.
 *
 * 429s are skipped here: the retry layer already logs each rate-limit retry,
 * and a 429 is transient rather than a client mistake.
 *
 * The body is read from a clone, so the caller still receives an unread response.
 */

import { parseError } from '../errors.js';
import { getMethod, getUrl, sanitizeUrl, type TransportLogger } from './shared.js';

/**
 * Wrap a fetch function so 4xx responses are logged through `logger.error`.
 *
 * @param baseFetch - The fetch function to wrap.
 * @param logger - Receives one `error` call per logged response.
 * @returns A fetch function with client-error logging.
 */
export function createErrorLoggingFetch(
  baseFetch: typeof fetch,
  logger: Pick<TransportLogger, 'error'>
): typeof fetch {
  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const response = await baseFetch(input, init);
    if (response.status >= 400 && response.status < 500 && response.status !== 429) {
      const method = getMethod(input, init);
      const url = sanitizeUrl(getUrl(input));
      let body: unknown;
      try {
        body = await response.clone().json();
      } catch {
        body = undefined;
      }
      const error = parseError(response, body);
      logger.error(`Client error ${response.status} for ${method} ${url}: ${error.message}`);
    }
    return response;
  };
}
