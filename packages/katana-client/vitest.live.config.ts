import { defineConfig } from 'vitest/config';

/**
 * Live smoke suite against the Katana TEST tenant (`pnpm test:live`).
 * Skips cleanly when `KATANA_TEST_API_KEY` is unset (see tests/live/testClient.ts).
 */
export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/live/**/*.live.test.ts'],
    // Real network calls through the proactive rate limiter (60 req/min) and
    // retry backoff — allow for a full rate-limit window plus cleanup.
    testTimeout: 180_000,
    hookTimeout: 180_000,
    // One file at a time: the tests share one API key's rate-limit budget.
    fileParallelism: false,
  },
});
