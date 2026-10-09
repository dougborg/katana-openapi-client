/** Tenant-scoped, recoverable artifacts for the generated SDK live suite. */
import { randomUUID } from 'node:crypto';
import { mkdirSync, renameSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { setTimeout } from 'node:timers/promises';
import { expect } from 'vitest';
import type { KatanaClient } from '../../src/client.js';
import * as sdk from '../../src/generated/sdk.gen.js';
import { type SdkResult, unwrap } from '../../src/responses.js';
import { makeTestClient } from './testClient.js';
export type Operation = {
  path: string;
  method: string;
  sdk: string;
  query: string[];
  required_query: string[];
};
export type Sample = { path: string; method: string; status: number; body: unknown };
type Entity = { id: number };
type LedgerRow = {
  endpoint: string;
  entity_id: number;
  issue: string;
  method: string;
  created_at: string;
  base_url: string;
  factory_id: number;
  deleted_at: string | null;
  delete_error: string | null;
};
export class Session {
  constructor(
    private operations: Operation[],
    private validate: (samples: Sample[]) => void
  ) {}
  rows: LedgerRow[] = [];
  factoryId = 0;
  baseUrl = '';
  ledger = '';
  // The hook records successful creates before the generated SDK parses them.
  client: KatanaClient = makeTestClient({
    fetch: async (input, init) => {
      const request = new Request(input, init);
      const response = await globalThis.fetch(request);
      if (this.ledger && request.method === 'POST' && response.ok) {
        const body = (await response.clone().json()) as Entity;
        const endpoint = new URL(request.url).pathname.slice(new URL(this.baseUrl).pathname.length);
        expect(body.id).toEqual(expect.any(Number));
        this.rows.push({
          endpoint,
          entity_id: body.id,
          issue: '#1157',
          method: 'POST',
          created_at: new Date().toISOString(),
          base_url: this.baseUrl,
          factory_id: this.factoryId,
          deleted_at: null,
          delete_error: null,
        });
        this.save();
      }
      return response;
    },
  });

  save(): void {
    writeFileSync(`${this.ledger}.tmp`, `${this.rows.map((r) => JSON.stringify(r)).join('\n')}\n`);
    renameSync(`${this.ledger}.tmp`, this.ledger);
  }
  async startWrites(): Promise<void> {
    const factory = (await this.call('/factory')) as { factory_id: number };
    expect(factory.factory_id).toBeGreaterThan(0);
    this.factoryId = factory.factory_id;
    this.baseUrl = this.client.getBaseUrl().replace(/\/$/, '');
    const directory = process.env.KATANA_TEST_LEDGER_DIR || join(tmpdir(), 'katana-test-ledgers');
    mkdirSync(directory, { recursive: true });
    this.ledger = join(directory, `${this.factoryId}-ts-${randomUUID()}.jsonl`);
    this.save();
  }
  async call(
    path: string,
    method = 'get',
    options: Record<string, unknown> = {}
  ): Promise<unknown> {
    const op = this.operations.find((o) => o.path === path && o.method === method);
    if (!op) throw new Error(`Missing operation: ${method} ${path}`);
    const fn = (
      sdk as unknown as Record<string, (o: Record<string, unknown>) => Promise<SdkResult>>
    )[op.sdk];
    if (!fn) throw new Error(`Missing generated SDK function ${op.sdk}`);
    const query = {
      ...(op.query.includes('page') ? { page: 1 } : {}),
      ...(op.query.includes('limit') ? { limit: 1 } : {}),
      ...(options.query as object | undefined),
    };
    const result = await fn({
      client: this.client.sdk,
      fetch: this.client.fetchWith({ autoPagination: false }),
      ...options,
      query,
    });
    expect(result.request?.method).toBe(method.toUpperCase());
    const body = unwrap(result);
    this.validate([{ path, method, status: result.response?.status ?? 0, body: body ?? null }]);
    if (method === 'delete') {
      const id = (options.path as { id: number }).id;
      const row = this.rows.find(
        (r) => r.endpoint === path.replace('/{id}', '') && r.entity_id === id
      );
      if (row) {
        row.deleted_at = new Date().toISOString();
        this.save();
      }
    }
    return body;
  }
  async cleanup(): Promise<void> {
    if (!this.ledger) return;
    const factory = (await this.call('/factory')) as { factory_id: number };
    expect(factory.factory_id).toBe(this.factoryId);
    const failures: string[] = [];
    const persist = () => {
      try {
        this.save();
      } catch {
        failures.push('Ledger persistence failed during cleanup');
      }
    };
    for (const row of [...this.rows].reverse()) {
      if (row.deleted_at) continue;
      for (const delay of [0, 1000, 2000, 4000, 8000]) {
        if (delay) await setTimeout(delay);
        try {
          const op = this.operations.find(
            (o) => o.path === `${row.endpoint}/{id}` && o.method === 'delete'
          );
          if (!op) throw new Error(`Missing cleanup operation for ${row.endpoint}`);
          const fn = (
            sdk as unknown as Record<string, (o: Record<string, unknown>) => Promise<SdkResult>>
          )[op.sdk];
          const result = await fn({ client: this.client.sdk, path: { id: row.entity_id } });
          const status = result.response?.status;
          if (status === 404 || (status !== undefined && status >= 200 && status < 300)) {
            row.deleted_at = new Date().toISOString();
            row.delete_error = null;
            persist();
            break;
          }
          row.delete_error = `HTTP ${status}`;
          persist();
          if (status !== 409 && status !== 412) break;
        } catch (error) {
          row.delete_error = error instanceof Error ? error.name : 'CleanupError';
          persist();
          break;
        }
      }
      if (!row.deleted_at) failures.push(`${row.endpoint}/${row.entity_id}: ${row.delete_error}`);
    }
    expect(failures, `Recover ledger ${this.ledger} with the test-only Python cleanup CLI`).toEqual(
      []
    );
  }
}
