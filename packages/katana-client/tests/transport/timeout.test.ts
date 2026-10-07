/**
 * Tests for the per-attempt timeout layer (fake timers only).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createResilientFetch } from '../../src/transport/resilient.js';
import { createTimeoutFetch } from '../../src/transport/timeout.js';

/** A fetch that never answers on its own, but rejects with the signal's reason on abort. */
function hangingFetch(): ReturnType<typeof vi.fn> {
  return vi.fn(
    (_input: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(init.signal?.reason), { once: true });
      })
  );
}

describe('createTimeoutFetch', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('rejects with a TimeoutError once timeoutMs elapses', async () => {
    const base = hangingFetch();
    const timed = createTimeoutFetch(base as unknown as typeof fetch, 1000);

    const pending = timed('https://api.example.com/x');
    const assertion = expect(pending).rejects.toMatchObject({ name: 'TimeoutError' });

    await vi.advanceTimersByTimeAsync(999);
    await vi.advanceTimersByTimeAsync(1);
    await assertion;
  });

  it('passes the response through when it arrives in time and clears the timer', async () => {
    const base = vi.fn().mockResolvedValue(new Response('ok'));
    const timed = createTimeoutFetch(base as unknown as typeof fetch, 1000);

    const response = await timed('https://api.example.com/x');

    expect(await response.text()).toBe('ok');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('forwards a caller abort with its own reason (not a TimeoutError)', async () => {
    const base = hangingFetch();
    const timed = createTimeoutFetch(base as unknown as typeof fetch, 10_000);
    const controller = new AbortController();

    const pending = timed('https://api.example.com/x', { signal: controller.signal });
    const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });
    controller.abort();
    await assertion;
  });

  it('reads the caller signal from a Request (SDK call style)', async () => {
    const base = hangingFetch();
    const timed = createTimeoutFetch(base as unknown as typeof fetch, 10_000);
    const controller = new AbortController();

    const pending = timed(new Request('https://api.example.com/x', { signal: controller.signal }));
    const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });
    controller.abort();
    await assertion;
  });

  it('rejects a non-positive timeout', () => {
    expect(() => createTimeoutFetch(globalThis.fetch, 0)).toThrow(/timeoutMs must be positive/);
  });

  it('a timed-out attempt is retried by the resilient layer', async () => {
    const base = vi
      .fn()
      .mockImplementationOnce(hangingFetch())
      .mockResolvedValueOnce(new Response('ok'));
    const chain = createResilientFetch({
      baseFetch: createTimeoutFetch(base as unknown as typeof fetch, 1000),
      retry: { backoffJitter: 0 },
    });

    const pending = chain('https://api.example.com/x');
    await vi.advanceTimersByTimeAsync(1000); // attempt 1 times out
    expect(base).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(2000); // first backoff
    expect(base).toHaveBeenCalledTimes(2);
    expect(await (await pending).text()).toBe('ok');
  });

  it('a caller abort is NOT retried by the resilient layer', async () => {
    const base = hangingFetch();
    const chain = createResilientFetch({
      baseFetch: createTimeoutFetch(base as unknown as typeof fetch, 10_000),
    });
    const controller = new AbortController();

    const pending = chain('https://api.example.com/x', { signal: controller.signal });
    const assertion = expect(pending).rejects.toMatchObject({ name: 'AbortError' });
    controller.abort();
    await assertion;
    await vi.advanceTimersByTimeAsync(60_000);
    expect(base).toHaveBeenCalledTimes(1);
  });
});
