/**
 * Regression guard for GHSA-hhx9-57xq-r5rw.
 *
 * `buildClientParams` is a runtime template that @hey-api/openapi-ts copies
 * verbatim into every generated SDK (src/generated/core/params.gen.ts), so the
 * published client carries it. Vulnerable templates wrote unknown `$<slot>_`
 * keys straight into a plain object, so `"$query___proto__"` replaced the
 * prototype chain of the returned `params.query`. Fixed templates create slot
 * records with a null prototype, which turns `__proto__` into an ordinary own
 * key.
 *
 * The generator is pinned to a `0.0.0-next-*` nightly, which semver-sorts below
 * the advisory's patched version (0.97.3) no matter how new it is, so the
 * dependency-review gate cannot judge it by version. This test judges the
 * generated code directly; the GHSA is allow-listed in security.yml on the
 * strength of it. If a regeneration ever reintroduces the bug, this fails.
 */

import { describe, expect, it } from 'vitest';
import { buildClientParams, type FieldsConfig } from '../src/generated/core/params.gen.js';

describe('buildClientParams prototype safety (GHSA-hhx9-57xq-r5rw)', () => {
  const fields: FieldsConfig = [{ args: [{ in: 'query', key: 'q' }] }];

  it('does not let a $query___proto__ key substitute the prototype chain', () => {
    const injected = { isAdmin: true };

    const result = buildClientParams([{ q: 'hello', $query___proto__: injected }], fields);

    const query = result.query as Record<string, unknown>;
    expect(query.q).toBe('hello');
    expect(Object.getPrototypeOf(query)).not.toBe(injected);
    expect(query.isAdmin).toBeUndefined();
    expect(Object.hasOwn(query, '__proto__')).toBe(true);
    expect(Object.prototype).not.toHaveProperty('isAdmin');
  });

  it.each(['$body_', '$headers_', '$path_'] as const)(
    'keeps %s__proto__ an own key on the slot record',
    (prefix) => {
      const result = buildClientParams([{ q: 'hello', [`${prefix}__proto__`]: { x: 1 } }], fields);
      const slot = result[prefix.slice(1, -1) as 'body' | 'headers' | 'path'] as Record<
        string,
        unknown
      >;

      expect(Object.hasOwn(slot, '__proto__')).toBe(true);
      expect(slot.x).toBeUndefined();
    }
  );
});
