/**
 * Runtime-checked narrowing for tests: asserts `value` is an instance of `cls`
 * and returns it typed as such, so tests read subclass fields without an
 * unchecked `as` cast.
 */
export function expectInstance<T>(value: unknown, cls: abstract new (...args: never[]) => T): T {
  if (!(value instanceof cls)) {
    throw new Error(`expected an instance of ${cls.name}, got ${String(value)}`);
  }
  return value;
}
