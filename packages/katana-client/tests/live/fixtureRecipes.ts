/** Resolve the shared detail-fixture dependencies through generated SDK calls. */
import type { Session } from './contractSession.js';
import { sdtTag } from './testClient.js';

export type DetailFixtures = {
  resources: Record<
    string,
    {
      path: string;
      method?: string;
      body?: unknown;
      select?: string;
      after?: string[];
      tag?: string;
      verify?: { path: string; id: string }[];
    }
  >;
  cases: { name: string; reads: { path: string; id: string }[] }[];
};

export class FixtureRecipes {
  private values = new Map<string, unknown>();
  constructor(
    private definitions: DetailFixtures['resources'],
    private session: Session,
    private name: string
  ) {}

  private select(value: unknown, path: string[]): unknown {
    let result = value;
    for (const key of path) {
      if (result === null || typeof result !== 'object' || !(key in result)) {
        throw new Error(`Missing fixture response field: ${path.join('.')}`);
      }
      result = (result as Record<string, unknown>)[key];
    }
    return result;
  }

  async resolve(value: unknown, tag = ''): Promise<unknown> {
    if (Array.isArray(value)) {
      const result = [];
      for (const item of value) result.push(await this.resolve(item, tag));
      return result;
    }
    if (value !== null && typeof value === 'object') {
      const result: Record<string, unknown> = {};
      for (const [key, item] of Object.entries(value)) result[key] = await this.resolve(item, tag);
      return result;
    }
    if (typeof value !== 'string' || !value.startsWith('$')) return value;
    if (value === '$tag') return tag;
    const [name, ...keys] = value.slice(1).split('.');
    if (!this.values.has(name)) {
      const definition = this.definitions[name];
      if (!definition) throw new Error(`Unknown fixture dependency: ${name}`);
      const ownTag = sdtTag(definition.tag ?? `TS-${this.name}-${name}`);
      for (const dependency of definition.after ?? []) await this.resolve(`$${dependency}`, ownTag);
      const body = await this.resolve(definition.body, ownTag);
      const result = await this.session.call(
        definition.path,
        definition.method ?? 'post',
        body === undefined ? {} : { body }
      );
      for (const check of definition.verify ?? []) {
        await this.session.call(check.path, 'get', {
          path: { id: this.select(result, check.id.split('.')) },
        });
      }
      this.values.set(
        name,
        definition.select ? this.select(result, definition.select.split('.')) : result
      );
    }
    return this.select(this.values.get(name), keys);
  }
}
