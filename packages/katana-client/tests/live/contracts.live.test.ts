/** The same spec-derived reads and eight core write scenarios as Python. */
import { execFileSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { type Operation, Session } from './contractSession.js';
import { hasTestCredentials, sdtTag } from './testClient.js';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '../../../..');
function python(command: string, input?: unknown): string {
  return execFileSync('uv', ['run', 'python', '-m', 'scripts.live_contracts', command], {
    cwd: root,
    input: input === undefined ? undefined : JSON.stringify(input),
    encoding: 'utf8',
    maxBuffer: 10 * 1024 * 1024,
  });
}
type Scenario = {
  entity: string;
  create: Record<string, unknown>;
  update: Record<string, unknown>;
  field: string;
};
const { operations, scenarios } = JSON.parse(python('catalog')) as {
  operations: Operation[];
  scenarios: Scenario[];
};
type Entity = Record<string, unknown> & { id: number; variants?: { id: number }[] };
const fast = process.env.KATANA_LIVE_FAST === '1';

function entries(body: unknown): Entity[] {
  return (Array.isArray(body) ? body : (body as { data: Entity[] }).data) as Entity[];
}
function substitute(value: unknown, context: Record<string, unknown>): unknown {
  if (typeof value === 'string') return context[value] ?? value;
  if (Array.isArray(value)) return value.map((v) => substitute(v, context));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, substitute(v, context)]));
  }
  return value;
}

describe.skipIf(!hasTestCredentials())('shared live SDK contracts', () => {
  for (const op of operations.filter(
    (o) =>
      o.method === 'get' && (!fast || ['/locations', '/products', '/suppliers'].includes(o.path))
  )) {
    it(`GET ${op.path}`, async (test) => {
      const session = new Session(operations, (samples) => {
        python('validate', samples);
      });
      const options: Record<string, unknown> = {};
      if (op.path.includes('{id}')) {
        const parent = op.path.split('/{id}')[0];
        const rows = entries(await session.call(parent));
        if (!rows.length) {
          test.skip(`No test-tenant fixture for ${op.path}`);
          return;
        }
        options.path = { id: rows[0].id };
      }
      const query: Record<string, unknown> = {};
      for (const [key, collection] of Object.entries({
        variant_id: '/variants',
        location_id: '/locations',
      })) {
        if (op.required_query.includes(key)) {
          const rows = entries(await session.call(collection));
          expect(rows.length, `Test tenant needs ${collection}`).toBeGreaterThan(0);
          query[key] = rows[0].id;
        }
      }
      await session.call(op.path, 'get', { ...options, query });
    });
  }
  for (const scenario of scenarios.filter(
    (s) => !fast || ['customers', 'suppliers'].includes(s.entity)
  )) {
    it(`round-trips ${scenario.entity}`, async () => {
      const session = new Session(operations, (samples) => {
        python('validate', samples);
      });
      await session.startWrites();
      try {
        const context: Record<string, unknown> = {
          $tag: sdtTag(`TS-${scenario.entity}`),
          $updated: sdtTag(`TS-${scenario.entity}-UPDATED`),
        };
        const template = JSON.stringify(scenario.create);
        for (const [key, dependency] of Object.entries({
          $product: 'products',
          $material: 'materials',
          $customer: 'customers',
          $supplier: 'suppliers',
        })) {
          if (template.includes(key)) {
            const definition = scenarios.find((s) => s.entity === dependency);
            if (!definition) throw new Error(`Missing dependency ${dependency}`);
            const created = (await session.call(`/${dependency}`, 'post', {
              body: substitute(definition.create, {
                $tag: sdtTag(`TS-${scenario.entity}-${dependency}`),
              }),
            })) as Entity;
            context[key] = ['products', 'materials'].includes(dependency)
              ? created.variants?.[0].id
              : created.id;
            expect(context[key]).toEqual(expect.any(Number));
          }
        }
        if (template.includes('$location')) {
          const locations = entries(await session.call('/locations'));
          expect(locations.length).toBeGreaterThan(0);
          context.$location = locations[0].id;
        }
        const path = `/${scenario.entity}`;
        const created = (await session.call(path, 'post', {
          body: substitute(scenario.create, context),
        })) as Entity;
        const detail = `${path}/{id}`;
        const read = operations.some((o) => o.path === detail && o.method === 'get')
          ? ((await session.call(detail, 'get', { path: { id: created.id } })) as Entity)
          : entries(
              await session.call(path, 'get', { query: { ids: [created.id], limit: 100 } })
            ).find((r) => r.id === created.id);
        expect(read?.[scenario.field]).toBe(context.$tag);
        const updated = (await session.call(detail, 'patch', {
          path: { id: created.id },
          body: substitute(scenario.update, context),
        })) as Entity;
        expect(updated[scenario.field]).toBe(context.$updated);
        await session.call(detail, 'delete', { path: { id: created.id } });
      } finally {
        await session.cleanup();
      }
    });
  }
});
