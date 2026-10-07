import { configDefaults, defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    // Live tests hit a real Katana tenant; they run only via `pnpm test:live`.
    exclude: [...configDefaults.exclude, 'tests/live/**'],
    coverage: {
      provider: 'v8',
      include: ['src/**/*.ts'],
      exclude: ['src/generated/**', 'src/types.ts'],
      reporter: ['text', 'json', 'html'],
    },
  },
});
