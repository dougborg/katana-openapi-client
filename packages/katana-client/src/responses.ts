/**
 * Response helpers for the generated SDK functions.
 *
 * Every generated SDK function (with the default `responseStyle: 'fields'` and
 * `throwOnError: false`) resolves to `{ data, error, request, response }`:
 * exactly one of `data` / `error` is set, and `response` is absent when the
 * request never got one (a network failure, a timeout, a caller abort).
 *
 * These helpers turn that shape into "the data, or a typed `KatanaError`",
 * mirroring the Python client's `unwrap` / `unwrap_data` / `is_success` /
 * `is_error` / `get_error_message` (`katana_public_api_client/utils.py`).
 * Error classification reuses {@link parseError}, so a failed SDK call raises
 * the same `AuthenticationError` / `ValidationError` / `RateLimitError` /
 * `ServerError` / `KatanaError` that `parseError` produces for raw responses.
 *
 * @example
 * ```typescript
 * import { getProduct, getAllProducts, KatanaClient, unwrap, unwrapData } from 'katana-openapi-client';
 *
 * const katana = await KatanaClient.create();
 * const product = unwrap(await getProduct({ client: katana.sdk, path: { id: 1 } })); // Product
 * const products = unwrapData(await getAllProducts({ client: katana.sdk }));          // Product[]
 * ```
 */

import { KatanaError, NetworkError, parseError } from './errors.js';

/**
 * The result shape of a generated SDK call (`responseStyle: 'fields'`,
 * `throwOnError: false` — the defaults). Structurally identical to the
 * generated `RequestResult`'s resolved value, so any SDK result is accepted.
 */
export type SdkResult<TData = unknown, TError = unknown> = (
  | { data: TData; error: undefined }
  | { data: undefined; error: TError }
) & {
  /** Absent when the request object itself could not be built. */
  request?: Request;
  /** Absent when no response arrived (network error, timeout, abort). */
  response?: Response;
};

/** The data type of a successful {@link SdkResult} (e.g. `Product` for `getProduct`). */
export type SuccessData<TResult extends SdkResult> = Exclude<TResult['data'], undefined>;

/** The item type of a list payload: Katana's `{ data: [...] }` envelope, or a bare array. */
export type ListItem<TPayload> = TPayload extends readonly (infer TItem)[]
  ? TItem
  : TPayload extends { data?: (infer TItem)[] }
    ? TItem
    : never;

/**
 * Resolves to `unknown` (no extra constraint) when `TResult` is a list
 * endpoint's result and to `never` otherwise, so passing a single-resource
 * result to {@link unwrapData} is a compile error. It checks for the `data`
 * key rather than assignability to `{ data?: T[] }`, because every object
 * type without a `data` key (e.g. `Product`) is assignable to that.
 */
export type ListResultGuard<TResult extends SdkResult> =
  SuccessData<TResult> extends readonly unknown[]
    ? unknown
    : 'data' extends keyof SuccessData<TResult>
      ? unknown
      : never;

const NOT_A_LIST = 'Expected a list response ({ data: [...] } or a bare array)';

/**
 * True when the call succeeded (a 2xx response with no error).
 *
 * Narrows the result so `result.data` is the success type.
 */
export function isSuccess<TResult extends SdkResult>(
  result: TResult
): result is Extract<TResult, { error: undefined }> {
  return result.error === undefined && (result.response === undefined || result.response.ok);
}

/** True when the call failed — an error response, or no response at all. */
export function isError<TResult extends SdkResult>(
  result: TResult
): result is Exclude<TResult, { error: undefined }> {
  return !isSuccess(result);
}

/**
 * The typed error for a failed call, or `undefined` for a successful one.
 *
 * - With a response: classified by status via {@link parseError}
 *   (401 → `AuthenticationError`, 422 → `ValidationError`, 429 →
 *   `RateLimitError`, 5xx → `ServerError`, anything else → `KatanaError`),
 *   with the SDK's parsed error body as `body`.
 * - Without a response (connection failure, timeout, abort): a `NetworkError`
 *   carrying the original error as `cause`. A `KatanaError` thrown by a
 *   custom fetch layer is returned unchanged.
 */
export function getError(result: SdkResult): KatanaError | undefined {
  if (isSuccess(result)) {
    return undefined;
  }
  const { error, response } = result;
  if (response) {
    return parseError(response, error);
  }
  if (error instanceof KatanaError) {
    return error;
  }
  if (error instanceof Error) {
    return new NetworkError(`Request failed without a response: ${error.message}`, {
      cause: error,
    });
  }
  return new NetworkError(`Request failed without a response: ${String(error)}`);
}

/**
 * Human-readable message for a failed call, or `undefined` on success.
 *
 * Unwraps Katana's nested `{ "error": { ... } }` envelope; for a 422 it
 * includes one formatted line per validation detail.
 */
export function getErrorMessage(result: SdkResult): string | undefined {
  return getError(result)?.message;
}

/**
 * Return a successful call's data, or throw the typed {@link KatanaError}.
 *
 * The return type is inferred from the SDK function, so
 * `unwrap(await getProduct(...))` is a `Product`. A no-content success
 * (204 — most DELETEs) returns `undefined`, matching the Python client's
 * `unwrap()` returning `None`; such endpoints are typed `void` by the SDK.
 *
 * @throws AuthenticationError on 401
 * @throws ValidationError on 422 (with structured `details`)
 * @throws RateLimitError on 429 (after the transport's retries are exhausted)
 * @throws ServerError on 5xx
 * @throws NetworkError when no response arrived
 * @throws KatanaError for any other error status
 */
export function unwrap<TResult extends SdkResult>(result: TResult): SuccessData<TResult> {
  const error = getError(result);
  if (error) {
    throw error;
  }
  if (result.response?.status === 204) {
    // The SDK substitutes `{}` for a 204's empty body; surface "no content"
    // as `undefined` instead. Every 204 in the Katana spec is declared `void`,
    // which `undefined` inhabits, so for those endpoints this cast is exact.
    return undefined as SuccessData<TResult>;
  }
  // No error means the SDK took its success branch, where `data` is the
  // parsed body (never `undefined`): exactly `SuccessData<TResult>`.
  return result.data as SuccessData<TResult>;
}

/**
 * Return a list call's items, or throw the typed {@link KatanaError}.
 *
 * Unwraps Katana's `{ "data": [...] }` list envelope. A list endpoint that
 * answers with a bare JSON array (`GET /bin_locations`, via
 * `getAllStorageBins`) is returned as-is. A missing `data` key yields `[]`.
 * Only list endpoints type-check: `unwrapData(await getProduct(...))` is a
 * compile error — use {@link unwrap} for single resources (including the
 * bare-model `GET /user_info`).
 *
 * @throws The same errors as {@link unwrap}
 * @throws TypeError if a successful payload is neither an array nor a `{ data: [...] }` envelope
 */
export function unwrapData<TResult extends SdkResult>(
  result: TResult & ListResultGuard<TResult>
): ListItem<SuccessData<TResult>>[] {
  const payload: unknown = unwrap(result);
  const items = Array.isArray(payload) ? payload : envelopeItems(payload);
  // The guard admits only list endpoints, whose payload is an array of
  // `ListItem`s or a `{ data?: ListItem[] }` envelope; the runtime checks
  // confirm `items` is that array.
  return items as ListItem<SuccessData<TResult>>[];
}

/** The items of a `{ data: [...] }` envelope (`[]` when `data` is absent). */
function envelopeItems(payload: unknown): unknown[] {
  if (typeof payload !== 'object' || payload === null) {
    throw new TypeError(NOT_A_LIST);
  }
  if (!('data' in payload) || payload.data === undefined) {
    return [];
  }
  if (!Array.isArray(payload.data)) {
    throw new TypeError(NOT_A_LIST);
  }
  return payload.data;
}
