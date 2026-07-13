import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../../docs/katana-openapi.yaml',
  output: {
    path: 'src/generated',
    // Format generated output with Biome, this package's single lint/format
    // tool (ADR 0003). biome.json un-ignores src/generated and an override
    // disables the linter there, so generated code is formatted but not linted.
    postProcess: ['biome:format'],
  },
  plugins: [
    '@hey-api/typescript', // Type generation
    '@hey-api/client-fetch', // HTTP client (Fetch API)
    '@hey-api/sdk', // SDK generation
  ],
});
