# ADR-TS-002: Hey API Code Generation

## Status

Accepted

## Context

We need to generate TypeScript types and SDK functions from the Katana OpenAPI
specification. This ensures type safety and keeps the client in sync with the API.

### Options Considered

1. **openapi-typescript** - Generates only types, no runtime code
1. **openapi-generator** - Official OpenAPI generator, heavy and complex
1. **@hey-api/openapi-ts** - Modern, lightweight, generates types + SDK
1. **Orval** - React Query focused, heavy framework opinions
1. **Manual types** - Write types by hand (not scalable)

### Requirements

- Generate TypeScript types from OpenAPI spec
- Generate SDK functions for API calls
- Integrate with custom resilient client
- Minimal runtime dependencies
- Tree-shakeable output
- Active maintenance

## Decision

Use **@hey-api/openapi-ts** for code generation.

### Reasons

1. **Generates both types and SDK**: Unlike openapi-typescript which only generates
   types, @hey-api/openapi-ts generates usable SDK functions
1. **Custom client support**: Allows providing a custom client, enabling our resilient
   fetch wrapper
1. **Modern and maintained**: Active development, good TypeScript support
1. **Minimal footprint**: Small runtime dependency (@hey-api/client-fetch is now
   bundled)
1. **Tree-shakeable**: Only imported functions are included in bundles

### Configuration

```typescript
// openapi-ts.config.ts
export default {
  client: '@hey-api/client-fetch',
  input: '../../docs/katana-openapi.yaml',
  output: 'src/generated',
  services: {
    asClass: false,
  },
  types: {
    enums: 'javascript',
  },
};
```

### Generated Structure

```
src/generated/
├── client/           # Base client utilities
│   ├── index.ts
│   └── types.gen.ts
├── sdk.gen.ts        # Generated SDK functions
└── types.gen.ts      # Generated TypeScript types
```

### Integration Pattern

```typescript
import { createClient, createConfig } from './generated/client/index.js';
import type { Client } from './generated/client/types.gen.js';

// Create client with our resilient fetch
const client = createClient(
  createConfig({
    baseUrl: 'https://api.katanamrp.com/v1',
    fetch: authenticatedFetch, // Our custom fetch with retry/pagination
  })
);

// Use with generated SDK functions
import { getAllProducts } from './generated/sdk.gen.js';
const { data, error } = await getAllProducts({ client });
```

## Consequences

### Positive

- **Full type safety**: All API calls are type-checked
- **Auto-completion**: IDE support for all endpoints and parameters
- **Sync with spec**: Regenerate to pick up API changes
- **Custom fetch support**: Our resilient transport works seamlessly
- **No vendor lock-in**: Generated code is plain TypeScript

### Negative

- **Generated code in repo**: Need to commit generated files or regenerate in CI
- **Learning curve**: Different from manually written SDKs
- **Version coupling**: Need to test SDK updates carefully

### Neutral

- **Separate from resilience**: SDK handles types/calls, our wrappers handle resilience
- **Regeneration workflow**: Need clear process for updating generated code

## Implementation Notes

### Regeneration

```bash
pnpm run generate
```

### Build Output

Generated SDK functions are re-exported from the main package:

```typescript
// src/index.ts
export * from './generated/sdk.gen.js';
export * from './generated/types.gen.js';
```

### Version Update Process

1. Update OpenAPI spec
1. Run `pnpm run generate`
1. Run tests to verify compatibility
1. Commit generated changes

## Related

- [Python ADR-002: OpenAPI Code Generation](../../../katana_public_api_client/docs/adr/0002-openapi-code-generation.md)
