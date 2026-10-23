/**
 * Live smoke tests: the PUBLIC SDK path (`KatanaClient` + generated SDK
 * functions) against the Katana TEST tenant.
 *
 * Run with `pnpm test:live`. The whole suite skips (it does not fail) when
 * `KATANA_TEST_API_KEY` is unset — see `testClient.ts` for the safety model
 * (no fallback to the production `KATANA_API_KEY`).
 *
 * The write round-trip is the regression guard for the 0.1.0 bug where SDK
 * POST / PATCH / DELETE requests went out as paginated GETs: a create that
 * silently becomes `GET /suppliers?page=1&limit=250` returns a list envelope,
 * not a supplier, so the round-trip fails at the first assertion.
 *
 * Write round-trips now live in contracts.live.test.ts, sharing scenarios,
 * wire validation, tenant verification and persistent cleanup with Python.
 */

import { describe, expect, it } from 'vitest';
import { getAllLocations, getAllProducts, getLocation } from '../../src/generated/sdk.gen.js';
import { unwrap, unwrapData } from '../../src/responses.js';
import { hasTestCredentials, makeTestClient } from './testClient.js';

/** A base fetch that records each outgoing request's method and URL. */
function recordingFetch(): { fetch: typeof fetch; sent: { method: string; url: URL }[] } {
  const sent: { method: string; url: URL }[] = [];
  const recording: typeof fetch = (input, init) => {
    const request = new Request(input, init);
    sent.push({ method: request.method, url: new URL(request.url) });
    return globalThis.fetch(request);
  };
  return { fetch: recording, sent };
}

describe.skipIf(!hasTestCredentials())('live: SDK against the test tenant', () => {
  it('returns a single resource un-enveloped (GET /locations/{id})', async () => {
    const katana = makeTestClient();
    const [first] = unwrapData(
      await getAllLocations({
        client: katana.sdk,
        query: { limit: 1 },
        fetch: katana.fetchWith({ autoPagination: false }),
      })
    );
    expect(first, 'the test tenant has no locations').toBeDefined();
    if (!first) return;

    const location = unwrap(await getLocation({ client: katana.sdk, path: { id: first.id } }));

    expect(location.id).toBe(first.id);
    expect(location.name).toBe(first.name);
    expect(location).not.toHaveProperty('data');
  });

  it('auto-paginates a list across multiple page requests', async () => {
    const { fetch, sent } = recordingFetch();
    const katana = makeTestClient({ fetch });

    // One item per page, capped at three items, so a tenant with >= 2
    // products must take >= 2 page requests to satisfy the call.
    const products = unwrapData(
      await getAllProducts({
        client: katana.sdk,
        query: { limit: 1 },
        fetch: katana.fetchWith({ maxItems: 3 }),
      })
    );

    expect(products.length, 'the test tenant needs >= 2 products').toBeGreaterThanOrEqual(2);
    const pages = sent
      .filter(({ url }) => url.pathname.endsWith('/products'))
      .map(({ url }) => url.searchParams.get('page'));
    expect(pages.slice(0, products.length)).toEqual(
      products.map((_, i) => String(i + 1)) // page=1, page=2, ...
    );
    expect(new Set(products.map((p) => p.id)).size).toBe(products.length);
  });
});
