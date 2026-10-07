import { defineConfig } from '@hey-api/openapi-ts';

// Run from this directory by the client's `pnpm run generate`, which then formats
// the output with the client's Biome (ADR 0003). Paths are relative to here.
export default defineConfig({
  input: '../../../docs/katana-openapi.yaml',
  output: {
    path: '../src/generated',
  },
  plugins: [
    '@hey-api/typescript', // Type generation
    '@hey-api/client-fetch', // HTTP client (Fetch API)
    '@hey-api/sdk', // SDK generation
  ],
});
