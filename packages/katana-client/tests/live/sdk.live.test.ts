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
 * Write tests follow the Python suite's SDT contract
 * (`tests/integration/README.md`): every created entity carries an
 * `SDT-<date>-<run>-<name>` tag and is deleted in a `finally`.
 */

import { describe, expect, it } from 'vitest';
import {
  createSupplier,
  deleteSupplier,
  getAllLocations,
  getAllProducts,
  getAllSuppliers,
  getLocation,
  updateSupplier,
} from '../../src/generated/sdk.gen.js';
import { unwrap, unwrapData } from '../../src/responses.js';
import { hasTestCredentials, makeTestClient, sdtTag } from './testClient.js';

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

/** The most recent element, if any. */
function last<T>(items: T[]): T | undefined {
  return items[items.length - 1];
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

  it('round-trips a supplier: create, read back, PATCH, DELETE', async () => {
    const { fetch, sent } = recordingFetch();
    const katana = makeTestClient({ fetch });
    const name = sdtTag('TS-SUPPLIER');
    let createdId: number | undefined;
    let deleted = false;

    try {
      // Create — must go out as a single POST, not a paginated GET.
      const created = unwrap(
        await createSupplier({
          client: katana.sdk,
          body: { name, comment: 'katana-openapi-client TS live smoke test' },
        })
      );
      createdId = created.id;
      expect(last(sent)?.method).toBe('POST');
      expect(last(sent)?.url.searchParams.has('page')).toBe(false);
      expect(created.id).toEqual(expect.any(Number));
      expect(created.name).toBe(name);

      // Read back through the list endpoint's `ids` filter.
      const [readBack] = unwrapData(
        await getAllSuppliers({ client: katana.sdk, query: { ids: [created.id] } })
      );
      expect(readBack?.id).toBe(created.id);
      expect(readBack?.name).toBe(name);

      // PATCH.
      const renamed = `${name}-PATCHED`;
      const updated = unwrap(
        await updateSupplier({
          client: katana.sdk,
          path: { id: created.id },
          body: { name: renamed },
        })
      );
      expect(last(sent)?.method).toBe('PATCH');
      expect(updated.id).toBe(created.id);
      expect(updated.name).toBe(renamed);

      // DELETE — a 204, which `unwrap` surfaces as `undefined`.
      const removed = unwrap(
        await deleteSupplier({ client: katana.sdk, path: { id: created.id } })
      );
      deleted = true;
      expect(last(sent)?.method).toBe('DELETE');
      expect(removed).toBeUndefined();

      const afterDelete = unwrapData(
        await getAllSuppliers({ client: katana.sdk, query: { ids: [created.id] } })
      );
      expect(afterDelete).toEqual([]);
    } finally {
      if (createdId !== undefined && !deleted) {
        // A soft assertion reports a failed cleanup without masking the
        // error that got us here.
        const cleanup = await deleteSupplier({ client: katana.sdk, path: { id: createdId } });
        expect
          .soft(cleanup.error, `cleanup failed: supplier ${createdId} (${name}) left on the tenant`)
          .toBeUndefined();
      }
    }
  });
});
