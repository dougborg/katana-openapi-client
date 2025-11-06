# Commit Standards

This project uses **semantic-release** with **conventional commits** and **scopes** for
monorepo versioning. Proper commit formatting is critical for automated releases.

## Quick Reference

| Commit Format                       | Effect                   | Use For                            |
| ----------------------------------- | ------------------------ | ---------------------------------- |
| `feat(client):`                     | Client MINOR release     | New client features                |
| `fix(client):`                      | Client PATCH release     | Client bug fixes                   |
| `feat(mcp):`                        | MCP MINOR release        | New MCP features                   |
| `fix(mcp):`                         | MCP PATCH release        | MCP bug fixes                      |
| `feat:` or `fix:`                   | Client release (default) | Unscoped changes default to client |
| `feat(client)!:` or `fix(client)!:` | Client MAJOR release     | Breaking changes                   |
| `chore:`, `docs:`, `test:`, etc.    | No release               | Non-user-facing changes            |

## Monorepo Structure

This repository contains two packages:

1. **katana-openapi-client** - Python client library
1. **katana-mcp-server** - Model Context Protocol server

Releases are managed independently using commit scopes.

## Commit Scopes for Releases

### Client Package Releases

Triggers release of `katana-openapi-client`:

```bash
# New feature (MINOR version bump: 0.30.0 → 0.31.0)
git commit -m "feat(client): add Products domain helper class"

# Bug fix (PATCH version bump: 0.30.0 → 0.30.1)
git commit -m "fix(client): handle null values in pagination"

# Breaking change (MAJOR version bump: 0.30.0 → 1.0.0)
git commit -m "feat(client)!: redesign authentication interface"
```

### MCP Server Package Releases

Triggers release of `katana-mcp-server`:

```bash
# New feature (MINOR version bump: 0.7.0 → 0.8.0)
git commit -m "feat(mcp): add inventory management tools"

# Bug fix (PATCH version bump: 0.7.0 → 0.7.1)
git commit -m "fix(mcp): correct order status filtering"

# Breaking change (MAJOR version bump: 0.7.0 → 1.0.0)
git commit -m "feat(mcp)!: change tool parameter structure"
```

### Unscoped Releases (Default to Client)

Commits without a scope default to releasing the client:

```bash
# These are equivalent:
git commit -m "feat: add retry mechanism"
git commit -m "feat(client): add retry mechanism"

# Both trigger client release (MINOR bump)
```

## Non-Release Commit Types

These commit types **do not trigger releases**:

### Development and Tooling

```bash
chore: update development dependencies
chore: configure new linting rule
chore: update build scripts
```

### Documentation

```bash
docs: update README installation instructions
docs: add API usage examples
docs: create ADR for pagination strategy
```

### Tests

```bash
test: add coverage for edge cases
test: fix flaky integration test
test: refactor test fixtures
```

### Refactoring

```bash
refactor: simplify error handling logic
refactor: extract common utility functions
refactor: rename internal variables for clarity
```

### CI/CD

```bash
ci: add parallel test execution
ci: update GitHub Actions workflow
ci: configure Dependabot
```

### Performance

```bash
perf: optimize pagination for large datasets
perf: reduce memory usage in client
```

### Build System

```bash
build: update uv to 0.5.0
build: configure package metadata
```

## Conventional Commit Format

### Structure

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Examples

**Simple feature:**

```bash
git commit -m "feat(mcp): add purchase order creation tool"
```

**Feature with description:**

```bash
git commit -m "feat(client): add automatic pagination support

Implements transparent pagination for list endpoints that return
paginated results. Automatically follows next page links until all
results are retrieved.

Closes #42"
```

**Breaking change:**

```bash
git commit -m "feat(client)!: redesign authentication mechanism

BREAKING CHANGE: AuthenticatedClient now requires api_key parameter
instead of using environment variable. Update your code:

Before: client = AuthenticatedClient()
After: client = AuthenticatedClient(api_key='your-key')

Closes #89"
```

## Semantic Versioning

The project follows [Semantic Versioning](https://semver.org/): **MAJOR.MINOR.PATCH**

### Version Bump Rules

| Change Type         | Scope                   | Bump  | Example         |
| ------------------- | ----------------------- | ----- | --------------- |
| **Breaking change** | `feat!:` or `fix!:`     | MAJOR | 0.30.0 → 1.0.0  |
| **New feature**     | `feat:`                 | MINOR | 0.30.0 → 0.31.0 |
| **Bug fix**         | `fix:`                  | PATCH | 0.30.0 → 0.30.1 |
| **Other types**     | `chore:`, `docs:`, etc. | None  | 0.30.0 → 0.30.0 |

### Pre-1.0 Special Rules

Before version 1.0.0, breaking changes still bump MINOR (not MAJOR):

- `feat!:` in 0.x.y → MINOR bump (0.30.0 → 0.31.0)
- After 1.0.0 → MAJOR bump (1.0.0 → 2.0.0)

## Best Practices

### ✅ DO

1. **Use imperative mood** - "add feature" not "added feature"
1. **Keep subject line short** - Under 72 characters
1. **Capitalize subject** - "Add feature" not "add feature"
1. **No period at end** - "Add feature" not "Add feature."
1. **Use body for context** - Explain "why" not "what"
1. **Reference issues** - Include "Closes #123" in footer
1. **Be specific** - "fix(mcp): handle null product names" vs "fix(mcp): fix bug"

### ❌ DON'T

1. **Don't mix concerns** - One logical change per commit
1. **Don't use vague messages** - Avoid "fix stuff" or "update code"
1. **Don't forget scope** - Be explicit about package (`client` or `mcp`)
1. **Don't break conventions** - Follow the format strictly
1. **Don't commit broken code** - Run validation before committing

## Multi-Package Changes

If a change affects both packages, create separate commits:

```bash
# Change affecting client
git commit -m "feat(client): add new pagination parameter"

# Change affecting MCP server
git commit -m "feat(mcp): use new pagination parameter"
```

This ensures:

- Both packages get proper releases
- Clear changelog entries
- Independent versioning

## Commit Message Examples

### Good Examples ✅

```bash
# Client feature
feat(client): add ResilientAsyncTransport for automatic retries

# MCP bug fix
fix(mcp): handle empty inventory list responses correctly

# Breaking change with detailed body
feat(client)!: remove deprecated sync methods

BREAKING CHANGE: Synchronous client methods have been removed.
Use async methods with asyncio.run() instead.

See migration guide in docs/MIGRATION.md

# Documentation
docs: add progressive disclosure guide for agents

# Chore with context
chore: update pre-commit hooks to latest versions
```

### Bad Examples ❌

```bash
# Too vague
fix: fixed bug

# Wrong mood
feat: added new feature

# Missing scope for release
feat: pagination support  # Should be feat(client):

# Period at end
feat(mcp): add tool.

# Not capitalized
feat(client): add helper

# Multiple concerns
feat(client): add pagination and fix auth bug  # Should be 2 commits
```

## Validation

### Pre-Commit Validation

The project uses semantic-release to validate commit messages automatically in CI.

### Manual Validation

Check your commit message locally:

```bash
# View last commit message
git log -1 --pretty=%B

# Check if it follows conventional commits
# Should match: type(scope): subject
```

### Amending Commit Messages

If you made a mistake:

```bash
# Fix the last commit message
git commit --amend -m "feat(client): correct commit message"

# Force push if already pushed (use with caution)
git push --force-with-lease
```

## Release Process

### Automated Releases

When commits are merged to `main`:

1. **semantic-release analyzes commits** since last release
1. **Determines version bump** based on commit types
1. **Generates CHANGELOG.md** from commit messages
1. **Creates git tag** with new version
1. **Publishes packages** to PyPI (if configured)
1. **Creates GitHub release** with notes

### Monitoring Releases

```bash
# View recent releases
gh release list

# View release notes
gh release view v0.31.0

# View all tags
git tag -l
```

## Related Documentation

- **[MONOREPO_SEMANTIC_RELEASE.md](../../../docs/MONOREPO_SEMANTIC_RELEASE.md)** -
  Complete monorepo release guide
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Official
  specification
- **[Semantic Versioning](https://semver.org/)** - Versioning specification

## Summary

**Remember:**

- 🎯 Use `feat(client):` or `feat(mcp):` for releases
- 🚫 Use `chore:`, `docs:`, `test:` for non-releases
- 💥 Add `!` for breaking changes: `feat(client)!:`
- 📝 Write clear, descriptive commit messages
- ✅ Run `uv run poe check` before committing

Proper commit formatting enables automated releases and clear changelogs!
