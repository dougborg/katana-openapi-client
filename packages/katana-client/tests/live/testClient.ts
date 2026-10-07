/**
 * Test-tenant client for the live smoke suite — the TypeScript counterpart of
 * the Python client's `make_test_client()` (`katana_public_api_client/testing.py`).
 *
 * SAFETY: this reads ONLY `KATANA_TEST_API_KEY` (required) and
 * `KATANA_TEST_BASE_URL` (optional). It never falls back to `KATANA_API_KEY`:
 * the test tenant shares the production base URL and is distinguished only by
 * its key, so a silent fallback would point write tests at production.
 *
 * Values come from the real environment first, then from the nearest `.env`
 * file walking up from this directory (the repo-root `.env`). Only
 * `KATANA_TEST_*` keys are read from that file and `process.env` is never
 * mutated, so loading it can't leak a production `KATANA_API_KEY` into code
 * that falls back to the environment (e.g. `KatanaClient.create()`).
 */

import { randomUUID } from 'node:crypto';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseEnv } from 'node:util';
import { KatanaClient, type KatanaClientOptions } from '../../src/client.js';

const DEFAULT_TEST_BASE_URL = 'https://api.katanamrp.com/v1';
const TEST_ENV_KEYS = ['KATANA_TEST_API_KEY', 'KATANA_TEST_BASE_URL'] as const;
type TestEnvKey = (typeof TEST_ENV_KEYS)[number];

/** Raised when `KATANA_TEST_API_KEY` is unset; suites skip on this rather than fail. */
export class MissingTestCredentialsError extends Error {
  constructor() {
    super(
      'KATANA_TEST_API_KEY is not set. makeTestClient() will NOT fall back to ' +
        'KATANA_API_KEY — that would let test code hit the production tenant. Set ' +
        'KATANA_TEST_API_KEY in your environment or the repo-root .env.'
    );
    this.name = 'MissingTestCredentialsError';
  }
}

/** The nearest `.env` at or above `start`, if any. */
function findDotEnv(start: string): string | undefined {
  let dir = start;
  for (;;) {
    const candidate = join(dir, '.env');
    if (existsSync(candidate)) {
      return candidate;
    }
    const parent = dirname(dir);
    if (parent === dir) {
      return undefined;
    }
    dir = parent;
  }
}

/** Only the `KATANA_TEST_*` entries of the nearest `.env` (read once). */
const dotEnvTestValues: Partial<Record<TestEnvKey, string>> = (() => {
  const path = findDotEnv(dirname(fileURLToPath(import.meta.url)));
  if (!path) {
    return {};
  }
  const parsed = parseEnv(readFileSync(path, 'utf8'));
  const values: Partial<Record<TestEnvKey, string>> = {};
  for (const key of TEST_ENV_KEYS) {
    const value = parsed[key];
    if (value) {
      values[key] = value;
    }
  }
  return values;
})();

function readTestEnv(key: TestEnvKey): string | undefined {
  return process.env[key] || dotEnvTestValues[key];
}

/** True when a test-tenant key is configured (the live suites skip otherwise). */
export function hasTestCredentials(): boolean {
  return Boolean(readTestEnv('KATANA_TEST_API_KEY'));
}

/**
 * Build a `KatanaClient` bound to the test tenant. Extra options (fetch,
 * pagination, logger, ...) pass through; the key and base URL cannot be
 * overridden.
 *
 * @throws MissingTestCredentialsError when `KATANA_TEST_API_KEY` is unset
 */
export function makeTestClient(
  options: Omit<KatanaClientOptions, 'apiKey' | 'baseUrl'> = {}
): KatanaClient {
  const apiKey = readTestEnv('KATANA_TEST_API_KEY');
  if (!apiKey) {
    throw new MissingTestCredentialsError();
  }
  // Explicit baseUrl so a production `KATANA_BASE_URL` can't redirect the suite.
  const baseUrl = readTestEnv('KATANA_TEST_BASE_URL') || DEFAULT_TEST_BASE_URL;
  return KatanaClient.withApiKey(apiKey, { ...options, baseUrl });
}

const RUN_ID = randomUUID().replace(/-/g, '').slice(0, 8);

/**
 * A discoverable, run-unique name for a test-created entity:
 * `SDT-<YYYY-MM-DD>-<run>-<name>`, the same shape as the Python suite's
 * `live_artifacts.tag()`, so orphans from either runtime are easy to find.
 */
export function sdtTag(name: string): string {
  const date = new Date().toISOString().slice(0, 10);
  return `SDT-${date}-${RUN_ID}-${name}`;
}
