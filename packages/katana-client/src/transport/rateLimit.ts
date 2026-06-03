/**
 * Proactive rate-limit transport layer for the Katana API.
 *
 * Mirrors the Python client's `RateLimitTransport` (katana_client.py): a token
 * bucket sized for Katana's documented budget (60 req/min by default) gates
 * every request *before* it goes out, and after each response the layer reads
 * `X-Ratelimit-Remaining` / `X-Ratelimit-Reset` and adapts:
 *
 * - **Sync down**: when the server reports fewer remaining tokens than our local
 *   estimate (e.g. another client sharing the API key), drain the local bucket to
 *   match. We never sync *up* — the server is authoritative on the lower bound only.
 * - **Reset gate**: when remaining hits 0, all requests block until
 *   `X-Ratelimit-Reset` elapses, so we don't fire the burst budget into a window
 *   the server has already declared exhausted.
 *
 * Placed **innermost** in the fetch chain (closest to the network, below retry and
 * pagination) so every actual HTTP request — each retry attempt and each paginated
 * page — consumes one token, matching how Katana counts requests server-side.
 *
 * `Retry-After` waiting on 429 stays in the retry layer; this layer only updates the
 * reset gate from headers (sleeping here too would double-delay).
 *
 * Zero-dependency on purpose — the transport layer is otherwise dep-free, and the
 * adaptive header logic is bespoke regardless of any token-bucket library.
 */

/** Header names Katana uses (case-insensitive lookup via `Headers.get`). */
const HEADER_REMAINING = 'X-Ratelimit-Remaining';
/**
 * Reset deadline as a Unix epoch in **milliseconds** — Katana's convention
 * (verified against the live wire; mirrors the Python client). Note most APIs
 * use seconds: if Katana ever switches, the gate math here must change too.
 */
const HEADER_RESET = 'X-Ratelimit-Reset';

/**
 * Configuration for the proactive rate limiter.
 */
export interface RateLimitConfig {
  /** Steady-state request budget per window. Default: 60 */
  requestsPerMinute: number;
  /** Window length in milliseconds the budget refills over. Default: 60000 */
  windowMs: number;
}

/**
 * Default rate-limit configuration (60 requests / minute, per Katana's spec).
 */
export const DEFAULT_RATE_LIMIT_CONFIG: RateLimitConfig = {
  requestsPerMinute: 60,
  windowMs: 60_000,
};

/**
 * Options for creating a rate-limited fetch function.
 */
export interface RateLimitedFetchOptions {
  /** Rate-limit configuration. */
  rateLimit?: Partial<RateLimitConfig>;
  /** Optional logger for state changes. */
  logger?: {
    debug: (message: string, ...args: unknown[]) => void;
    info: (message: string, ...args: unknown[]) => void;
    warn: (message: string, ...args: unknown[]) => void;
    error: (message: string, ...args: unknown[]) => void;
  };
}

/** Sleep for a number of milliseconds (timer-based; fakeable in tests). */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Wrap a fetch function with proactive, header-adaptive rate limiting.
 *
 * @param baseFetch - The fetch function to wrap (innermost; closest to the network).
 * @param options - Rate-limit configuration and optional logger.
 * @returns A fetch function that throttles outgoing requests.
 *
 * @example
 * ```typescript
 * const limited = createRateLimitedFetch(globalThis.fetch, {
 *   rateLimit: { requestsPerMinute: 60 },
 * });
 * ```
 */
export function createRateLimitedFetch(
  baseFetch: typeof fetch,
  options: RateLimitedFetchOptions = {}
): typeof fetch {
  const config: RateLimitConfig = {
    ...DEFAULT_RATE_LIMIT_CONFIG,
    ...options.rateLimit,
  };
  // Fail fast on invalid config: a non-positive rate or window makes the refill
  // rate 0/NaN, which would make `acquireToken` spin forever or sleep for NaN ms.
  if (config.requestsPerMinute <= 0 || config.windowMs <= 0) {
    throw new Error(
      `createRateLimitedFetch: requestsPerMinute and windowMs must be positive (got requestsPerMinute=${config.requestsPerMinute}, windowMs=${config.windowMs}). To disable rate limiting, omit this layer from the fetch chain (or, via KatanaClient, set \`requestsPerMinute: null\`).`
    );
  }
  const logger = options.logger ?? {
    debug: () => {},
    info: () => {},
    warn: () => {},
    error: () => {},
  };

  const capacity = config.requestsPerMinute;
  const refillPerMs = capacity / config.windowMs;

  // ── Token bucket ─────────────────────────────────────────────────────────
  // `tokens` is the single source of truth for the local budget: it refills over
  // the window AND is clamped down to the server's `X-Ratelimit-Remaining` (never
  // up). Sync-down reads it directly — there is no separate decrement-only estimate
  // that could clamp permanently at 0 when the server never reports remaining=0.
  let tokens = capacity;
  let lastRefillMs = Date.now();

  function refill(): void {
    const now = Date.now();
    const elapsed = now - lastRefillMs;
    if (elapsed > 0) {
      tokens = Math.min(capacity, tokens + elapsed * refillPerMs);
      lastRefillMs = now;
    }
  }

  // The token check-and-debit is synchronous (no `await`), so concurrent
  // acquisitions can't double-spend — only the wait between attempts yields.
  async function acquireToken(weight = 1): Promise<void> {
    for (;;) {
      refill();
      if (tokens >= weight) {
        tokens -= weight;
        return;
      }
      const waitMs = Math.max(1, Math.ceil((weight - tokens) / refillPerMs));
      await sleep(waitMs);
    }
  }

  // ── Reset gate ───────────────────────────────────────────────────────────
  // `gate` is non-null only while a reset window is active; pending requests
  // await it. `gateDeadlineMs` tracks the latest observed reset so out-of-order
  // responses with an earlier deadline can't shorten the gate.
  let gate: Promise<void> | null = null;
  let gateResolve: (() => void) | null = null;
  let gateDeadlineMs: number | null = null;
  let gateTimer: ReturnType<typeof setTimeout> | null = null;

  function engageResetGate(deadlineMs: number): void {
    // Ignore a stale/earlier reset when a later gate is already active.
    if (gateDeadlineMs !== null && deadlineMs <= gateDeadlineMs) {
      return;
    }
    gateDeadlineMs = deadlineMs;
    if (gate === null) {
      gate = new Promise<void>((resolve) => {
        gateResolve = resolve;
      });
    }
    if (gateTimer !== null) {
      clearTimeout(gateTimer);
    }
    const waitMs = Math.max(0, deadlineMs - Date.now());
    gateTimer = setTimeout(releaseResetGate, waitMs);
    logger.info(`Rate limit reset gate engaged for ${waitMs}ms (remaining hit 0)`);
  }

  function releaseResetGate(): void {
    // Defensive: only act when a gate is actually engaged. The timer is
    // cleared on re-engage so this can't double-fire today, but guarding keeps
    // the function safe if gate management is refactored.
    if (gate === null) {
      return;
    }
    gateTimer = null;
    gateDeadlineMs = null;
    // The server's window has rolled: restore the full budget.
    tokens = capacity;
    lastRefillMs = Date.now();
    const resolve = gateResolve;
    gate = null;
    gateResolve = null;
    resolve?.();
  }

  // ── Response observation ─────────────────────────────────────────────────
  function observeResponse(response: Response): void {
    const remainingStr = response.headers.get(HEADER_REMAINING);
    const resetStr = response.headers.get(HEADER_RESET);
    // Defensive: many endpoints (auth, redirects, errors) omit these headers.
    if (remainingStr === null || resetStr === null) {
      return;
    }
    const remaining = Number.parseInt(remainingStr, 10);
    const resetEpochMs = Number.parseInt(resetStr, 10);
    if (Number.isNaN(remaining) || Number.isNaN(resetEpochMs)) {
      logger.warn(`Invalid rate-limit headers: remaining=${remainingStr} reset=${resetStr}`);
      return;
    }

    // Stale-window guard: a reset deadline already in the past describes a
    // window that has rolled — acting on its `remaining` would clamp us on
    // outdated state under the never-sync-up rule.
    if (resetEpochMs <= Date.now()) {
      return;
    }

    // Refill first so the bucket reflects time elapsed during the round-trip,
    // then compare against the server's report.
    refill();

    // Fast path: the server has at least as much budget as our local bucket.
    if (remaining > 0 && remaining >= tokens) {
      return;
    }

    // Sync down only — clamp the bucket to the server's lower remaining (never up).
    if (remaining > 0 && remaining < tokens) {
      logger.info(
        `Rate limit synced down: ${Math.floor(tokens)} -> ${remaining} tokens (remote remaining)`
      );
      tokens = remaining;
    }

    // When remaining hits 0 the gate alone blocks until the window rolls; we
    // deliberately do not also drain the bucket to zero (the gate is the override).
    if (remaining === 0) {
      engageResetGate(resetEpochMs);
    }
  }

  return async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    // Block on any active reset window before spending a token.
    if (gate !== null) {
      await gate;
    }

    await acquireToken(1);

    // A reset gate can engage between the acquire above and this check (a
    // concurrent observer seeing remaining=0). If we simply waited and proceeded,
    // the token we just debited would be wiped by `releaseResetGate`'s
    // `tokens = capacity` reset, letting this request slip into the next window
    // uncounted — under-throttling by the number of requests that raced in here.
    // Instead, refund the debit, wait for the window to roll, and re-acquire so
    // the request is charged against the NEW window's budget.
    while (gate !== null) {
      tokens = Math.min(capacity, tokens + 1);
      await gate;
      await acquireToken(1);
    }

    // `acquireToken` debited the bucket for this request, so the server's
    // `remaining` for it will line up with `tokens` rather than reading one lower.
    const response = await baseFetch(input, init);

    observeResponse(response);
    return response;
  };
}
