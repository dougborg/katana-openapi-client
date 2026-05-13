# Contributing to Katana OpenAPI Client

Thank you for your interest in contributing to the Katana OpenAPI Client! This document
provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/dougborg/katana-openapi-client.git
   cd katana-openapi-client
   ```

1. **Install uv** (if not already installed)

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

1. **Install dependencies**

   ```bash
   uv sync --all-extras
   ```

1. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your Katana API credentials for testing
   ```

## Development Workflow

### Code Quality

We maintain high code quality standards. Before submitting changes:

```bash
# Format code
uv run poe format

# Check formatting
uv run poe format-check

# Run type checking
uv run poe lint

# Run tests
uv run poe test
```

### Running Tests

```bash
# Run all tests
uv run poe test

# Run with coverage
uv run poe test-coverage

# Run specific test file
uv run poe test tests/test_katana_client.py

# Run integration tests (requires API credentials)
uv run poe test-integration
```

### Code Style

- [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting
- [pyright](https://microsoft.github.io/pyright/) for type checking — **canonical**, per
  [`pyrightconfig.json`](../pyrightconfig.json) and the LSP integration. Run via
  `uv run pyright <path>` (the LSP can be stale; the CLI is the source of truth).
- [ty](https://astral.sh/blog/ty) for type checking — secondary fast checker (Astral's
  Rust-based). Both run in CI via `uv run poe lint`; both must pass.
- [mdformat](https://mdformat.readthedocs.io/) for Markdown formatting

All formatting is automated via `uv run poe format`.

## Submitting Changes

### Pull Request Process

1. **Fork the repository** and create a feature branch

   ```bash
   git checkout -b feat/your-feature-name
   ```

   Branch names use the same **type** prefixes as conventional commits (see
   [COMMIT_STANDARDS](../.github/agents/guides/shared/COMMIT_STANDARDS.md)) — `feat/`,
   `fix/`, `docs/`, `chore/`, etc. — so the branch name signals the kind of change.
   (Note: `feat`, `fix`, etc. are the conventional-commit *type*; the *scope* is the
   package, e.g. `(client)` or `(mcp)`, applied to the commit message, not the branch
   name.)

1. **Make your changes** following the code style guidelines

1. **Add or update tests** for your changes

1. **Update documentation** if needed

1. **Run the full test suite**

   ```bash
   uv run poe format
   uv run poe lint
   uv run poe test
   ```

1. **Commit your changes** with a clear commit message **using scopes**

   ```bash
   # For client changes
   git commit -m "feat(client): add new domain helper"

   # For MCP server changes
   git commit -m "feat(mcp): add inventory tool"
   ```

1. **Push to your fork** and create a pull request

   For the first push of a new branch, use the explicit destination ref so the push
   doesn't depend on `push.default`, upstream-tracking config, or shell habits:

   ```bash
   git push -u origin HEAD:refs/heads/feat/your-feature-name
   ```

   The form `HEAD:refs/heads/<name>` names both the source (current HEAD) and the
   destination ref explicitly, so it's immune to git configs (e.g.
   `push.default = upstream`) that can reroute an under-specified push to whatever the
   branch tracks — which, if you created the branch via
   `git checkout -b <name> origin/main`, is `main`. A pre-push hook enforces the
   explicit form; never bypass with `--no-verify`. Full rationale + the incident that
   prompted the rule live in
   [COMMIT_STANDARDS "First-Push Safety"](../.github/agents/guides/shared/COMMIT_STANDARDS.md#first-push-safety).

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/) with **scopes**
for monorepo versioning:

**Type + Scope:**

- `feat(client):` new features in the client (triggers client release)
- `feat(mcp):` new features in MCP server (triggers MCP release)
- `fix(client):` bug fixes in the client (triggers client release)
- `fix(mcp):` bug fixes in MCP server (triggers MCP release)
- `docs:` documentation changes (no release)
- `test:` adding or updating tests (no release)
- `chore:` maintenance tasks (no release)

**Examples:**

```bash
# Release client package
git commit -m "feat(client): add Products domain helper"

# Release MCP server package
git commit -m "feat(mcp): implement check_inventory tool"

# No release (documentation only)
git commit -m "docs: update README with new examples"
```

**Important:** Use the correct scope based on what you're changing:

- Files in `katana_public_api_client/` → use `(client)` scope
- Files in `katana_mcp_server/` → use `(mcp)` scope
- Documentation or CI only → use `docs:` or `ci:` (no scope)

See [docs/RELEASE.md](RELEASE.md) for complete release documentation

### Pull Request Guidelines

- Include a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep the scope focused and atomic

## Project Structure

The repo is a 3-package monorepo (Python client, MCP server, TypeScript client). The
canonical tree lives in the root
[README.md → Project Structure](../README.md#project-structure); see also the linked
package READMEs from that section. The structure isn't reproduced here — keeping the
tree in two places is exactly the kind of drift-prone hand-maintained reference the rule
below forbids.

## Architecture Guidelines

### Core Principles

1. **Transparency**: Features should work automatically without configuration
1. **Resilience**: All API calls should handle errors gracefully
1. **Type Safety**: Use comprehensive type annotations
1. **Performance**: Leverage async/await and efficient HTTP handling
1. **Compatibility**: Maintain compatibility with the generated client

### Adding New Features

When adding features:

1. **Transport Layer First**: Implement core functionality in `ResilientAsyncTransport`
1. **Automatic Behavior**: Make features work transparently without user configuration
1. **Comprehensive Testing**: Include unit tests, integration tests, and error scenarios
1. **Documentation**: Update relevant documentation and examples

## Testing Guidelines

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test real API interactions (marked with
  `@pytest.mark.integration`)
- **Transport Tests**: Test the transport layer behavior directly

### Writing Tests

- Use descriptive test names that explain the scenario
- Include both success and error cases
- Mock external dependencies appropriately
- Use fixtures for common test setup

### Test Environment

Integration tests require valid Katana API credentials. Set these in your `.env` file:

```bash
KATANA_API_KEY=your_api_key_here
KATANA_BASE_URL=https://api.katanamrp.com/v1
```

## Documentation

### Updating Documentation

- Update relevant `.md` files in the `docs/` directory
- Keep examples current and working
- Update the README.md if adding user-facing features
- Include docstrings for all public methods

### No hand-maintained drift-prone references

When writing or updating documentation, **do not hard-code facts that have a
source-of-truth elsewhere**. They drift on every release, every spec sync, every
refactor, and every closed issue, and nobody can be expected to update both places. Rule
of thumb: if a fact in a doc requires updating in two places when something changes, the
fact is in the wrong place.

Things that are guaranteed to drift if hand-maintained:

- **Package version numbers** — use a shields.io PyPI/npm badge instead. The badge
  fetches the live version at render time.
- **Endpoint counts / tool counts / model counts** — either remove ("see the OpenAPI
  spec for the canonical endpoint surface", "see `katana://help/tools` for the current
  tool list") or generate from the source-of-truth via a `poe` task wired into
  pre-commit.
- **Hand-curated ADR lists** — link to the per-scope ADR `README.md` index instead. The
  indexes are short, easy to keep current, and live next to the ADRs they list.
- **Issue numbers cited as roadmap markers** — link to the
  [project board](https://github.com/users/dougborg/projects/5) instead. The board
  reflects current state; the issue number you cited may close, get renumbered, or
  scope-creep.
- **"Coming soon" / "planned" callouts** — either remove (git history is the answer) or
  link to a specific issue (which the project board can surface).
- **Dated "last updated" footers** — remove. Git history already records this.
- **File paths inside generated trees** — point at the parent dir or the spec, not
  individual files that move on regeneration.

If you find yourself adding such a fact, that's the signal to invert the relationship:
link out to where the fact lives instead of duplicating it. PRs that re-introduce
hand-maintained drift-prone references will be asked to abstract them.

## Client Regeneration

The OpenAPI client is automatically generated from `katana-openapi.yaml` using
[`openapi-python-client`](https://github.com/openapi-generators/openapi-python-client).

### Spec Maintenance

Before regenerating, audit the local spec against upstream. The full workflow lives in
[`docs/upstream-specs/README.md`](https://github.com/dougborg/katana-openapi-client/blob/main/docs/upstream-specs/README.md)
in the repo (kept out of the published docs site since the upstream-spec YAML and audit
reports are maintainer-only artefacts). Quick reference:

```bash
uv run poe refresh-upstream-spec      # pull cached upstream specs
uv run poe audit-spec                 # request-side drift vs. live gateway
uv run poe validate-response-examples # response-side drift vs. README.io portal
uv run poe validate-examples          # local example/schema consistency
```

`refresh-upstream-spec` writes to `docs/upstream-specs/` (idempotent — no-op if upstream
hasn't changed); the other three are read-only. Run them whenever you're changing
`docs/katana-openapi.yaml` or investigating possible upstream drift.

### Regeneration Process

```bash
# Regenerate client from OpenAPI spec
uv run python scripts/regenerate_client.py
```

### What Gets Regenerated

The canonical list of generated vs preserved paths lives in three places that stay in
sync with the actual generators:

- The "Generated Files (DO NOT EDIT)" and "Editable Files (Can Modify)" sections of
  [FILE_ORGANIZATION.md](../.github/agents/guides/shared/FILE_ORGANIZATION.md), which
  describe the boundary in detail.
- [`scripts/regenerate_client.py`](../scripts/regenerate_client.py) decides which
  *attrs* files get rewritten — read the `generated_items` list inside
  `move_client_to_workspace` for the exact list.
- [`scripts/generate_pydantic_models.py`](../scripts/generate_pydantic_models.py)
  decides which *pydantic* files get rewritten (the `_generated/` subtree and
  `_auto_registry.py` under `models_pydantic/`).

If the docs and either script ever disagree, the script wins.

The high-level rule: anything under `api/`, `models/`, `client.py`, `client_types.py`,
`errors.py`, `py.typed`, `__init__.py` (rewritten from a flattened-import template every
regen — *not* preserved despite the inline comment in the script suggesting otherwise),
and `models_pydantic/_generated/` (plus `_auto_registry.py`) is rewritten on every
regen. Everything else under `katana_public_api_client/` (including the rest of
`models_pydantic/` — hand-maintained pydantic infrastructure) is preserved.

### Regeneration Features

- **🔄 Flattened Structure**: No more `generated/` subdirectory
- **🛡️ File Preservation**: Custom files are never overwritten
- **🔧 Automatic Fixes**: Uses `ruff --unsafe-fixes` for code quality
- **✅ Dual Validation**: Both openapi-spec-validator and Redocly validation
- **🎯 Source-Level Fixes**: Issues resolved in OpenAPI spec when possible

### Documentation Style

- Use clear, concise language
- Include practical examples
- Follow the existing format and style
- Test any code examples to ensure they work

## Release Process

Releases are fully automated using python-semantic-release. See [RELEASE.md](RELEASE.md)
for complete documentation.

**Quick summary for contributors:**

- Use [Conventional Commits](https://www.conventionalcommits.org/) format
- `feat:` commits trigger minor version bump (0.x.0)
- `fix:` commits trigger patch version bump (0.0.x)
- Releases happen automatically when PR is merged to `main`

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
Please read and follow it in all interactions.

Thank you for contributing! 🎉
