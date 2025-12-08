# ADR-TS-003: Biome for Linting and Formatting

## Status

Accepted

## Context

The TypeScript client needs linting and formatting tools for code quality. The original
setup used ESLint with @typescript-eslint and Prettier, which required multiple
packages:

- eslint
- @typescript-eslint/eslint-plugin
- @typescript-eslint/parser
- prettier (or eslint-plugin-prettier)

This multi-package setup has several issues:

1. **Configuration complexity**: Multiple config files (.eslintrc, .prettierrc)
1. **Performance**: ESLint is relatively slow
1. **Dependency bloat**: Many transitive dependencies
1. **Version conflicts**: Keeping packages in sync

### Options Considered

1. **ESLint + Prettier**: Standard but complex
1. **Biome**: Single tool for linting + formatting, written in Rust
1. **Rome (deprecated)**: Predecessor to Biome
1. **deno lint + deno fmt**: Deno-specific, not ideal for npm packages

## Decision

Use **Biome** as the single tool for linting and formatting.

### Reasons

1. **20x faster**: Biome is written in Rust, significantly faster than ESLint
1. **Single tool**: Replaces both ESLint and Prettier
1. **Zero config**: Works out of the box with sensible defaults
1. **Modern rules**: Includes rules from ESLint, TypeScript-ESLint, and Prettier
1. **Active development**: Growing community, regular releases
1. **Single dependency**: Replaces 4+ packages with 1

### Migration

Before (4+ packages):

```json
{
  "devDependencies": {
    "eslint": "^8.x",
    "@typescript-eslint/eslint-plugin": "^7.x",
    "@typescript-eslint/parser": "^7.x",
    "prettier": "^3.x"
  }
}
```

After (1 package):

```json
{
  "devDependencies": {
    "@biomejs/biome": "^1.9.4"
  }
}
```

### Configuration

```json
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedImports": "error",
        "noUnusedVariables": "error"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "single",
      "semicolons": "always",
      "trailingCommas": "es5"
    }
  },
  "files": {
    "ignore": ["dist", "node_modules", "src/generated"]
  }
}
```

### NPM Scripts

```json
{
  "scripts": {
    "lint": "biome check src tests",
    "lint:fix": "biome check --write src tests",
    "format": "biome format --write src tests"
  }
}
```

## Consequences

### Positive

- **Faster CI**: Linting completes in seconds instead of minutes
- **Simpler config**: Single biome.json file
- **Fewer dependencies**: Reduced node_modules size
- **Consistent formatting**: Single tool = consistent output
- **Modern ES syntax**: Prefers Number.parseInt() over parseInt(), etc.

### Negative

- **Learning curve**: Different from ESLint for contributors familiar with ESLint
- **Fewer rules**: Not all ESLint plugins have equivalents
- **Newer ecosystem**: Smaller plugin ecosystem than ESLint

### Neutral

- **Breaking change**: Switching tools requires updating CI and local workflows
- **Different CLI**: Commands differ from ESLint (check vs lint)

## Code Changes

Biome's auto-fix applies modern JavaScript best practices:

```typescript
// Before (ESLint style)
const seconds = parseInt(retryAfter, 10);
if (!isNaN(seconds)) { ... }
return Math.pow(2, attempt) * factor;

// After (Biome style)
const seconds = Number.parseInt(retryAfter, 10);
if (!Number.isNaN(seconds)) { ... }
return 2 ** attempt * factor;
```

## Related

- [Biome Documentation](https://biomejs.dev/)
- [ESLint to Biome Migration](https://biomejs.dev/linter/rules-sources/)
