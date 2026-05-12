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

The repository contains three packages — only the two Python ones release through
semantic-release with the scopes below:

1. **`katana_public_api_client/`** → scope `(client)`, releases as
   `katana-openapi-client` on PyPI.
1. **`katana_mcp_server/`** → scope `(mcp)`, releases as `katana-mcp-server` on PyPI.
1. **`packages/katana-client/`** → TypeScript client, released independently via npm (no
   semantic-release scope; managed via its own `package.json` versioning).

Releases for the two Python packages are managed independently using commit scopes.

## Commit Scopes for Releases

### Client Package Releases

Triggers release of `katana-openapi-client`:

```bash
# New feature → MINOR bump
git commit -m "feat(client): add Products domain helper class"

# Bug fix → PATCH bump
git commit -m "fix(client): handle null values in pagination"

# Breaking change → MAJOR bump (post-1.0; see Pre-1.0 Special Rules below)
git commit -m "feat(client)!: redesign authentication interface"
```

### MCP Server Package Releases

Triggers release of `katana-mcp-server`:

```bash
# New feature → MINOR bump
git commit -m "feat(mcp): add inventory management tools"

# Bug fix → PATCH bump
git commit -m "fix(mcp): correct order status filtering"

# Breaking change → MAJOR bump (post-1.0)
git commit -m "feat(mcp)!: change tool parameter structure"
```

For the canonical current versions of each package, see the shields.io badges in the
top-level [README.md](../../../../README.md) — never hand-quote a version in a guide.

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

| Change Type         | Scope                   | Bump  |
| ------------------- | ----------------------- | ----- |
| **Breaking change** | `feat!:` or `fix!:`     | MAJOR |
| **New feature**     | `feat:`                 | MINOR |
| **Bug fix**         | `fix:`                  | PATCH |
| **Other types**     | `chore:`, `docs:`, etc. | None  |

### Pre-1.0 Special Rules

Both Python packages are pre-1.0. Before 1.0.0, breaking changes still bump MINOR (not
MAJOR):

- `feat!:` while `0.x.y` → MINOR bump
- `feat!:` after `1.0.0` → MAJOR bump

This means `feat(client)!:` on a 0.x.y client behaves like a normal `feat:` from a
version-number perspective. The breaking-change signal then has to come from the
**changelog entry** (the `BREAKING CHANGE:` footer is what surfaces it). See "Schema and
Generator Changes" below for the rule that requires the marker even on small
spec/generator edits.

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

## Schema and Generator Changes

Edits to the OpenAPI spec (`docs/katana-openapi.yaml`) or to the generator scripts
(`scripts/generate_pydantic_models.py`, `scripts/regenerate_client.py`) can ripple into
the **public client surface** in ways that break consumers — even when each individual
change reads as a "fix" or "chore". Those ripples must be captured in the commit message
so the auto-generated changelog flags them.

### What counts as a breaking schema change

Use `feat(client)!:` (or `fix(client)!:`) **with a `BREAKING CHANGE:` footer** whenever
a spec or generator edit causes any of the following in the regenerated client output:

- A previously-exported class **disappears** (e.g., a `StrEnum` was deduped into a
  structurally identical sibling).
- A field **type narrows** in a way that makes previously-valid values raise (e.g.,
  `type: string` → `$ref` to a `StrEnum`).
- A field is **renamed** or **removed** on a response or request schema.
- An endpoint path is **removed**.
- A required field becomes **optional** (changes parse semantics) or vice versa.

The footer must list the affected name(s) so a consumer searching the changelog for the
broken import or attribute can find the change. Example shape:

```
fix(client)!: dedupe collapses OldName

<body explaining the trigger>

BREAKING CHANGE: ``katana_public_api_client.models_pydantic.OldName``
no longer exists; import ``NewName`` instead. Both enums had identical
values; the rewrite is mechanical.
```

### What does NOT need the breaking-change marker

- Adding a new endpoint or field (purely additive).
- Adding a value to an existing enum (parse stays tolerant; old values still work).
- Generated-file diff is byte-identical (e.g., a docstring tweak in the generator that
  doesn't change emitted code).
- Internal-only refactors that don't change the surface (consolidating generator config,
  renaming private helpers, etc.).

### Why this matters pre-1.0

The packages are pre-1.0, so breaking changes bump MINOR (per "Pre-1.0 Special Rules"
above) — *not* MAJOR. That's a smaller version-number signal than a 1.x → 2.x bump, so
the **changelog entry** carries the discoverability for affected consumers. Without the
breaking-change footer, the change shows up as a normal `fix:` line and consumers hit an
`ImportError` (or `ValueError`, etc.) without a breadcrumb to follow.

When in doubt, run `uv run poe regenerate-client && uv run poe generate-pydantic` and
inspect `git diff katana_public_api_client/`. If the diff removes any top-level class,
removes any `__all__` entry, or changes a field's type annotation in a non-additive way,
use `!` and `BREAKING CHANGE:`. Read
[`katana_public_api_client/docs/spec-authoring.md`](../../../../katana_public_api_client/docs/spec-authoring.md)
before editing `docs/katana-openapi.yaml` — it covers the OpenAPI 3.1 conventions,
`ListResponse` schema requirements, use-site descriptions, the regen-in-same-PR rule,
and the upstream-drift audit workflow.

## Lockfile Drift

When `uv.lock` shows up modified but you didn't touch dependencies (e.g., a
sibling-package release on `main` bumped a workspace version), `git add uv.lock` and
bundle it into your current commit.

**Don't `git checkout -- uv.lock` to drop it**: pre-commit's auto-stash/restore fights
with the lockfile being regenerated mid-hook (pytest's `uv run` re-syncs it), producing
confusing "files were modified by this hook" failures where nothing was actually wrong
with the staged content. The lockfile must stay in sync with `pyproject.toml` at every
commit anyway, so bundling is always the right call.

## First-Push Safety

When a local branch was created via `git checkout -b <name> origin/main`, its upstream
is set to `origin/main`. A subsequent `git push -u origin <name>` then resolves to its
tracked upstream and **pushes the local tip straight to `main`** — bypassing PR review
and triggering semantic-release.

**Always use the explicit destination ref for first-time pushes:**

```bash
# Wrong — pushes to whatever the local branch tracks (may be main)
git push -u origin chore/foo

# Right — explicit destination, creates the remote branch
git push -u origin HEAD:refs/heads/chore/foo
```

A `pre-push` hook enforces this; **do not bypass with `--no-verify`**.

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

- **[CLAUDE.md](../../../../CLAUDE.md)** — session-level guidance, Known Pitfalls
  (lockfile drift, first-push safety, rebase-before-PR rule).
- **[Spec Authoring Guide](../../../../katana_public_api_client/docs/spec-authoring.md)**
  — OpenAPI 3.1 conventions, `ListResponse` schema, use-site descriptions, the
  regen-in-same-PR rule.
- **[Release Process Guide](../devops/RELEASE_PROCESS.md)** — semantic-release
  configuration and operational details.
- **[Conventional Commits](https://www.conventionalcommits.org/)** — official
  specification.
- **[Semantic Versioning](https://semver.org/)** — versioning specification.

## Summary

**Remember:**

- 🎯 Use `feat(client):` or `feat(mcp):` for releases
- 🚫 Use `chore:`, `docs:`, `test:` for non-releases
- 💥 Add `!` for breaking changes: `feat(client)!:`
- 📝 Write clear, descriptive commit messages
- ✅ Run `uv run poe check` before committing

Proper commit formatting enables automated releases and clear changelogs!
