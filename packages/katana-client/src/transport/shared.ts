/**
 * Shared helpers for the composable fetch wrappers.
 *
 * Every layer receives the standard `fetch(input, init)` pair. The generated
 * SDK calls `fetch(request)` with a fully-built `Request` and **no** `init`,
 * while `KatanaClient.fetch` passes a URL string plus an `init`. These helpers
 * read method / URL / signal from whichever of the two actually carries them,
 * so every layer behaves identically for both call styles.
 *
 * Runtime-agnostic on purpose: only WHATWG fetch / AbortSignal / timers are
 * used, so the transport works on Node >= 20 and in browsers.
 */

/** Logger interface accepted by every transport layer (console-compatible). */
export interface TransportLogger {
  debug: (message: string, ...args: unknown[]) => void;
  info: (message: string, ...args: unknown[]) => void;
  warn: (message: string, ...args: unknown[]) => void;
  error: (message: string, ...args: unknown[]) => void;
}

/** A logger that discards everything. */
export const NOOP_LOGGER: TransportLogger = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
};

/** True when `input` is a `Request` (duck-typed so polyfilled classes also match). */
export function isRequest(input: unknown): input is Request {
  return (
    typeof input === 'object' &&
    input !== null &&
    !(input instanceof URL) &&
    typeof (input as Request).url === 'string' &&
    typeof (input as Request).method === 'string' &&
    typeof (input as Request).clone === 'function'
  );
}

/** Upper-cased HTTP method; `init.method` wins over a `Request`'s own method. */
export function getMethod(input: RequestInfo | URL, init?: RequestInit): string {
  if (init?.method) {
    return init.method.toUpperCase();
  }
  return isRequest(input) ? input.method.toUpperCase() : 'GET';
}

/** The request URL as a string (may be relative when the caller passed one). */
export function getUrl(input: RequestInfo | URL): string {
  if (typeof input === 'string') {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  return input.url;
}

/** The caller's abort signal; `init.signal` wins over a `Request`'s own signal. */
export function getSignal(input: RequestInfo | URL, init?: RequestInit): AbortSignal | undefined {
  if (init?.signal) {
    return init.signal;
  }
  return isRequest(input) ? input.signal : undefined;
}

/** The reason a signal was aborted, normalised to an `Error`. */
export function abortReason(signal: AbortSignal): Error {
  const reason: unknown = signal.reason;
  if (reason instanceof Error) {
    return reason;
  }
  return new DOMException('The operation was aborted.', 'AbortError');
}

/**
 * Sleep for `ms` milliseconds, rejecting early with the abort reason if
 * `signal` aborts. Timer-based, so vitest fake timers control it.
 */
export function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) {
    return Promise.reject(abortReason(signal));
  }
  return new Promise<void>((resolve, reject) => {
    const onAbort = (): void => {
      clearTimeout(timer);
      reject(abortReason(signal as AbortSignal));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener('abort', onAbort);
      resolve();
    }, ms);
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}

/** Await `promise`, rejecting early with the abort reason if `signal` aborts. */
export function waitWithSignal<T>(promise: Promise<T>, signal?: AbortSignal): Promise<T> {
  if (!signal) {
    return promise;
  }
  if (signal.aborted) {
    return Promise.reject(abortReason(signal));
  }
  return new Promise<T>((resolve, reject) => {
    const onAbort = (): void => reject(abortReason(signal));
    signal.addEventListener('abort', onAbort, { once: true });
    promise.then(
      (value) => {
        signal.removeEventListener('abort', onAbort);
        resolve(value);
      },
      (error: unknown) => {
        signal.removeEventListener('abort', onAbort);
        reject(error);
      }
    );
  });
}

/** Substrings that mark a query parameter as sensitive (mirrors the Python client). */
const SENSITIVE_PARAMS = [
  'api_key',
  'auth',
  'authorization',
  'credential',
  'email',
  'key',
  'password',
  'secret',
  'token',
];

/** Redact sensitive query-parameter values from a URL so it is safe to log. */
export function sanitizeUrl(url: string): string {
  const queryStart = url.indexOf('?');
  if (queryStart === -1) {
    return url;
  }
  const params = new URLSearchParams(url.slice(queryStart + 1));
  const redacted = new URLSearchParams();
  for (const [key, value] of params) {
    const lower = key.toLowerCase();
    const sensitive = SENSITIVE_PARAMS.some((pattern) => lower.includes(pattern));
    redacted.append(key, sensitive ? '***' : value);
  }
  return `${url.slice(0, queryStart)}?${redacted.toString()}`;
}
