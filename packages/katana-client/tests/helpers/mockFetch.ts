/**
 * Typed mock-fetch helpers shared by the unit tests.
 *
 * `vi.fn()` without a type argument produces `Mock<Procedure>`, which is not
 * assignable to `typeof fetch` and leaves `mock.calls` effectively untyped.
 * These helpers keep every mock typed as `fetch`, and normalise the two call
 * styles the transport layers see — `fetch(url, init)` from `client.fetch()`
 * and `fetch(request)` from the generated SDK — so assertions don't have to
 * reach into `RequestInit['headers']` (a `HeadersInit | undefined`).
 */

import { type Mock, vi } from 'vitest';

/** A `vi.fn` mock with `fetch`'s exact signature. */
export type MockFetch = Mock<typeof fetch>;

/** Create a fresh, fully-typed fetch mock. */
export function createMockFetch(): MockFetch {
  return vi.fn<typeof fetch>();
}

/** The `[input, init]` arguments of the `index`-th call; throws if it never happened. */
export function fetchCall(mock: MockFetch, index = 0): Parameters<typeof fetch> {
  const call = mock.mock.calls[index];
  if (!call) {
    throw new Error(`fetch mock has no call #${index} (made ${mock.mock.calls.length})`);
  }
  return call;
}

/** The URL the `index`-th call targeted, for either call style. */
export function sentUrl(mock: MockFetch, index = 0): string {
  const [input] = fetchCall(mock, index);
  if (input instanceof Request) {
    return input.url;
  }
  return input instanceof URL ? input.href : input;
}

/**
 * The headers the `index`-th call carried, for either call style: a
 * `Request`'s own headers overlaid with any `init.headers`, mirroring how
 * `fetch` itself resolves them.
 */
export function sentHeaders(mock: MockFetch, index = 0): Headers {
  const [input, init] = fetchCall(mock, index);
  const headers = new Headers(input instanceof Request ? input.headers : undefined);
  new Headers(init?.headers).forEach((value, key) => {
    headers.set(key, value);
  });
  return headers;
}

/** The `Request` the `index`-th call passed (SDK call style); throws for `fetch(url, init)` calls. */
export function sentRequest(mock: MockFetch, index = 0): Request {
  const [input] = fetchCall(mock, index);
  if (!(input instanceof Request)) {
    throw new Error(`fetch call #${index} was not made with a Request`);
  }
  return input;
}
