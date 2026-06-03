/**
 * Tests for the proactive rate-limit transport.
 *
 * Mirrors the Python client's test_rate_limit_transport.py. Uses vitest fake
 * timers throughout — the token bucket reads Date.now() and schedules timers,
 * so the real wall clock is never consulted (per the repo's fake-time rule).
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRateLimitedFetch } from '../../src/transport/rateLimit.js';

/** Build a 200 Response, optionally carrying rate-limit headers. */
function ok(headers?: Record<string, string>): Response {
  return new Response('{}', { status: 200, headers });
}

const silentLogger = {
  debug: () => {},
  info: () => {},
  warn: () => {},
  error: () => {},
};

describe('createRateLimitedFetch', () => {
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('allows a burst up to the bucket capacity immediately', async () => {
    mockFetch.mockResolvedValue(ok());
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
    });

    for (let i = 0; i < 5; i++) {
      await limited('https://api/x');
    }
    expect(mockFetch).toHaveBeenCalledTimes(5);
  });

  it('paces requests beyond the burst capacity as tokens refill', async () => {
    mockFetch.mockResolvedValue(ok());
    // capacity 2, refill 2 tokens / 1000ms => 1 token per 500ms.
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 2, windowMs: 1_000 },
    });

    const pending = [limited('https://api/x'), limited('https://api/x'), limited('https://api/x')];

    // First two consume the burst immediately; the third waits for a refill.
    await vi.advanceTimersByTimeAsync(0);
    expect(mockFetch).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(500);
    expect(mockFetch).toHaveBeenCalledTimes(3);

    await Promise.all(pending);
  });

  it('engages the reset gate on remaining=0 and releases after the reset window', async () => {
    const reset = Date.now() + 200;
    mockFetch
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '0', 'X-Ratelimit-Reset': String(reset) })
      )
      .mockResolvedValue(ok());
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
      logger: silentLogger,
    });

    await limited('https://api/x'); // observes remaining=0 -> gate engaged
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const blocked = limited('https://api/x');
    await vi.advanceTimersByTimeAsync(0);
    expect(mockFetch).toHaveBeenCalledTimes(1); // still gated

    await vi.advanceTimersByTimeAsync(200); // window rolls -> gate releases
    await blocked;
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it('extends the reset gate when a later in-flight response reports a further reset', async () => {
    const earlier = Date.now() + 200;
    const later = Date.now() + 500;
    mockFetch
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '0', 'X-Ratelimit-Reset': String(earlier) })
      )
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '0', 'X-Ratelimit-Reset': String(later) })
      )
      .mockResolvedValue(ok());
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
      logger: silentLogger,
    });

    // Two concurrent requests both pass the gate and observe remaining=0; the
    // second carries a later reset, which must extend (not shorten) the gate.
    await Promise.all([limited('https://api/x'), limited('https://api/x')]);
    expect(mockFetch).toHaveBeenCalledTimes(2);

    const blocked = limited('https://api/x');
    await vi.advanceTimersByTimeAsync(200); // earlier deadline passes...
    expect(mockFetch).toHaveBeenCalledTimes(2); // ...but the gate held to the later one

    await vi.advanceTimersByTimeAsync(300); // total 500 -> later deadline
    await blocked;
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('syncs the budget down when the server reports fewer remaining', async () => {
    const reset = Date.now() + 60_000;
    mockFetch
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '1', 'X-Ratelimit-Reset': String(reset) })
      )
      .mockResolvedValue(ok());
    // capacity 10, refill 10 tokens / 1000ms => 1 token per 100ms.
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 10, windowMs: 1_000 },
      logger: silentLogger,
    });

    // First request acquires (10->9); observing remaining=1 drains down to ~1 token.
    await limited('https://api/x');
    expect(mockFetch).toHaveBeenCalledTimes(1);

    const pending = [limited('https://api/x'), limited('https://api/x')];
    await vi.advanceTimersByTimeAsync(0);
    // Only ~1 token remained, so the second request fires and the third must wait.
    expect(mockFetch).toHaveBeenCalledTimes(2);

    await vi.advanceTimersByTimeAsync(100); // refill one token
    expect(mockFetch).toHaveBeenCalledTimes(3);

    await Promise.all(pending);
  });

  it('re-charges a token for a request gated after it acquired (no cross-window under-throttle)', async () => {
    // capacity 1, 1 token/sec. R1 takes the token and engages the gate (late
    // reset). R2 finds no token, sleeps in acquire, then acquires a refilled token
    // *while the gate is still engaged* -> it gets gated post-acquire and must
    // refund + re-acquire so it's charged against the new window (not let through free).
    mockFetch
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '0', 'X-Ratelimit-Reset': String(Date.now() + 2_000) })
      )
      .mockResolvedValue(ok());
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 1, windowMs: 1_000 },
      logger: silentLogger,
    });

    const r1 = limited('https://api/x'); // takes the only token, returns remaining=0
    const r2 = limited('https://api/x'); // no token -> sleeps in acquireToken
    await vi.advanceTimersByTimeAsync(1_000); // r2 acquires a refilled token, gate still engaged -> gated
    await r1;
    expect(mockFetch).toHaveBeenCalledTimes(1); // only r1 has been sent; r2 is gated

    await vi.advanceTimersByTimeAsync(1_000); // total 2000 -> gate releases; r2 re-acquires and sends
    await r2;
    expect(mockFetch).toHaveBeenCalledTimes(2);

    // r2 was charged against the new window, so the bucket is empty: a third
    // request must wait for a refill (without the re-charge it would fire now).
    const r3 = limited('https://api/x');
    await vi.advanceTimersByTimeAsync(0);
    expect(mockFetch).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(1_000);
    await r3;
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('throws on non-positive rate-limit config', () => {
    expect(() =>
      createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
        rateLimit: { requestsPerMinute: 0, windowMs: 60_000 },
      })
    ).toThrow(/must be positive/);
    expect(() =>
      createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
        rateLimit: { requestsPerMinute: 60, windowMs: 0 },
      })
    ).toThrow(/must be positive/);
  });

  it('keeps syncing down after the bucket cycles (estimate never clamps at 0)', async () => {
    // Regression for the prior decrement-only estimate: header-less traffic +
    // a refill must NOT prevent a later low `remaining` from syncing down.
    const okH = (remaining: number) =>
      ok({
        'X-Ratelimit-Remaining': String(remaining),
        'X-Ratelimit-Reset': String(Date.now() + 120_000),
      });
    mockFetch
      .mockResolvedValueOnce(okH(2)) // syncs bucket down to 2
      .mockResolvedValueOnce(ok()) // header-less drains toward 0
      .mockResolvedValueOnce(ok())
      .mockResolvedValueOnce(okH(5)) // after a full refill: must sync down again
      .mockResolvedValue(ok());
    // 60/min => 1 token/sec, so the in-test awaits don't refill meaningfully.
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
      logger: silentLogger,
    });

    await limited('https://api/x'); // -> tokens 2
    await limited('https://api/x'); // -> ~1
    await limited('https://api/x'); // -> ~0
    await vi.advanceTimersByTimeAsync(60_000); // window rolls: bucket refills to 60
    await limited('https://api/x'); // observes remaining=5 -> bucket clamped to 5
    expect(mockFetch).toHaveBeenCalledTimes(4);

    // Bucket now holds ~5 tokens: five more fire immediately, a sixth is paced.
    const burst = Array.from({ length: 6 }, () => limited('https://api/x'));
    await vi.advanceTimersByTimeAsync(0);
    expect(mockFetch).toHaveBeenCalledTimes(9); // 4 + 5 immediate; 6th gated on a token
    await vi.advanceTimersByTimeAsync(1_000);
    await Promise.all(burst);
    expect(mockFetch).toHaveBeenCalledTimes(10);
  });

  it('is a no-op when rate-limit headers are absent', async () => {
    mockFetch.mockResolvedValue(ok()); // no rate-limit headers
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
    });

    for (let i = 0; i < 5; i++) {
      await limited('https://api/x');
    }
    expect(mockFetch).toHaveBeenCalledTimes(5);
  });

  it('treats malformed rate-limit headers as a no-op and warns', async () => {
    const warn = vi.fn();
    mockFetch.mockResolvedValue(ok({ 'X-Ratelimit-Remaining': 'abc', 'X-Ratelimit-Reset': 'xyz' }));
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
      logger: { ...silentLogger, warn },
    });

    await limited('https://api/x');
    await limited('https://api/x');
    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(warn).toHaveBeenCalled();
  });

  it('ignores a reset window whose deadline is already in the past', async () => {
    const stale = Date.now() - 1_000;
    mockFetch
      .mockResolvedValueOnce(
        ok({ 'X-Ratelimit-Remaining': '0', 'X-Ratelimit-Reset': String(stale) })
      )
      .mockResolvedValue(ok());
    const limited = createRateLimitedFetch(mockFetch as unknown as typeof fetch, {
      rateLimit: { requestsPerMinute: 60, windowMs: 60_000 },
      logger: silentLogger,
    });

    await limited('https://api/x'); // remaining=0 but reset is stale -> no gate
    const next = limited('https://api/x');
    await vi.advanceTimersByTimeAsync(0);
    await next;
    expect(mockFetch).toHaveBeenCalledTimes(2); // not blocked
  });
});
