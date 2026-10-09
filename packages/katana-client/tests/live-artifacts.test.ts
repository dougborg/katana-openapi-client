import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { type Operation, Session } from './live/contractSession.js';

const operations: Operation[] = [
  { path: '/factory', method: 'get', sdk: 'getFactory', query: [], required_query: [] },
  { path: '/customers', method: 'post', sdk: 'createCustomer', query: [], required_query: [] },
  {
    path: '/customers/{id}',
    method: 'delete',
    sdk: 'deleteCustomer',
    query: [],
    required_query: [],
  },
];
let directory: string;
let factoryId: number;
let deleteStatus: number;
let nextId: number;
let deleted: string[];

beforeEach(() => {
  directory = mkdtempSync(join(tmpdir(), 'katana-session-unit-'));
  factoryId = 123;
  deleteStatus = 204;
  nextId = 1;
  deleted = [];
  vi.stubEnv('KATANA_TEST_API_KEY', 'unit-test-key');
  vi.stubEnv('KATANA_TEST_BASE_URL', 'https://katana.test/v1');
  vi.stubEnv('KATANA_TEST_LEDGER_DIR', directory);
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const request = new Request(input, init);
      if (request.method === 'DELETE') {
        deleted.push(new URL(request.url).pathname);
        return new Response(null, { status: deleteStatus });
      }
      const body =
        request.method === 'POST'
          ? { id: nextId++, name: 'SDT-CUSTOMER' }
          : { factory_id: factoryId };
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    })
  );
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  rmSync(directory, { recursive: true, force: true });
});

describe('live artifact failure paths', () => {
  it('records a successful create before validation fails, then cleans it', async () => {
    const session = new Session(operations, (samples) => {
      if (samples[0].method === 'post') throw new Error('wire drift');
    });
    await session.startWrites();
    await expect(
      session.call('/customers', 'post', { body: { name: 'SDT-CUSTOMER' } })
    ).rejects.toThrow('wire drift');
    expect(session.rows[0].deleted_at).toBeNull();
    expect(JSON.parse(readFileSync(session.ledger, 'utf8')).factory_id).toBe(123);
    await session.cleanup();
    expect(deleted).toEqual(['/v1/customers/1']);
    expect(JSON.parse(readFileSync(session.ledger, 'utf8')).deleted_at).not.toBeNull();
  });

  it('still cleans a created resource if its first ledger write fails', async () => {
    const session = new Session(operations, () => {});
    await session.startWrites();
    vi.spyOn(session, 'save').mockImplementationOnce(() => {
      throw new Error('disk full');
    });
    await expect(
      session.call('/customers', 'post', { body: { name: 'SDT-CUSTOMER' } })
    ).rejects.toThrow();
    await session.cleanup();
    expect(deleted).toEqual(['/v1/customers/1']);
    expect(session.rows[0].deleted_at).not.toBeNull();
  });

  it('refuses cleanup when the factory changes', async () => {
    const session = new Session(operations, () => {});
    await session.startWrites();
    await session.call('/customers', 'post', { body: { name: 'SDT-CUSTOMER' } });
    factoryId = 456;
    await expect(session.cleanup()).rejects.toThrow();
    expect(deleted).toEqual([]);
  });

  it('attempts every artifact in reverse order and retains failed cleanup', async () => {
    const session = new Session(operations, () => {});
    await session.startWrites();
    await session.call('/customers', 'post', { body: { name: 'SDT-FIRST' } });
    await session.call('/customers', 'post', { body: { name: 'SDT-SECOND' } });
    deleteStatus = 422;
    await expect(session.cleanup()).rejects.toThrow();
    expect(deleted).toEqual(['/v1/customers/2', '/v1/customers/1']);
    const rows = readFileSync(session.ledger, 'utf8')
      .trim()
      .split('\n')
      .map((r) => JSON.parse(r));
    expect(rows.every((r) => r.deleted_at === null && r.delete_error === 'HTTP 422')).toBe(true);
  });
});
