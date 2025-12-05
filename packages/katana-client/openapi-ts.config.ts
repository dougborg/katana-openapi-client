import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../../docs/katana-openapi.yaml',
  output: {
    path: 'src/generated',
    format: 'prettier',
  },
  plugins: [
    '@hey-api/typescript', // Type generation
    '@hey-api/client-fetch', // HTTP client (Fetch API)
    '@hey-api/sdk', // SDK generation
  ],
});
