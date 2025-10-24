# Monorepo Semantic Release Configuration

## Overview

This repository uses **Python Semantic Release v10** with monorepo support to
independently version and release two packages:

1. **katana-openapi-client** - The main Python API client
1. **katana-mcp-server** - The Model Context Protocol server

Each package can be released independently based on commit scopes, allowing them to
evolve at their own pace.

## Commit Convention

We use **conventional commits** with **scopes** to control which package(s) get
released:

### Client Package Releases

Commits affecting the main client:

```bash
feat(client): add new Products helper methods
fix(client): resolve pagination edge case
perf(client): optimize retry backoff algorithm
```

Or commits **without a scope** (defaults to client):

```bash
feat: add automatic pagination support
fix: handle 429 rate limits correctly
```

### MCP Server Releases

Commits affecting the MCP server:

```bash
feat(mcp): add inventory tools
fix(mcp): correct stock level calculation
docs(mcp): update usage examples
```

### Both Packages

If you want to release both packages (rare), make two separate commits:

```bash
git commit -m "feat(client): add domain helpers"
git commit -m "feat(mcp): add tools using new helpers"
```

## How It Works

### Configuration Files

#### Root pyproject.toml

```toml
[tool.semantic_release]
tag_format = "client-v{version}"
commit_message = "chore(release): client v{version}"
# Only processes commits with (client) scope or no scope
```

#### katana_mcp_server/pyproject.toml

```toml
[tool.semantic_release]
tag_format = "mcp-v{version}"
commit_message = "chore(release): mcp v{version}"
# Only processes commits with (mcp) scope
```

### Release Workflow

The `.github/workflows/release.yml` workflow runs on every push to `main` and performs
**two independent semantic-release checks**:

1. **Client Release** (`release-client` job):

   - Checks for commits with `feat(client):`, `fix(client):`, or no scope
   - Creates tag: `client-v{version}`
   - Builds and publishes to PyPI as `katana-openapi-client`

1. **MCP Server Release** (`release-mcp` job):

   - Checks for commits with `feat(mcp):`, `fix(mcp):`
   - Creates tag: `mcp-v{version}`
   - Builds and publishes to PyPI as `katana-mcp-server`

Both jobs run in parallel and are independent.

## Versioning Strategy

### Version Bumps

| Commit Type                        | Example                          | Version Bump          |
| ---------------------------------- | -------------------------------- | --------------------- |
| `feat:` or `feat(scope):`          | `feat(mcp): add search tool`     | MINOR (0.1.0 → 0.2.0) |
| `fix:` or `fix(scope):`            | `fix(client): resolve auth bug`  | PATCH (0.1.0 → 0.1.1) |
| `perf:` or `perf(scope):`          | `perf(mcp): optimize queries`    | PATCH (0.1.0 → 0.1.1) |
| `feat!:` or `feat(scope)!:`        | `feat(client)!: breaking change` | MAJOR (0.1.0 → 1.0.0) |
| Other (`docs:`, `chore:`, `test:`) | `docs(mcp): update README`       | NO BUMP               |

### Current Versions

- **katana-openapi-client**: `0.23.0` (tracks main client)
- **katana-mcp-server**: `0.1.0a1` (alpha release)

### Tag Format

- Client tags: `client-v0.23.0`, `client-v0.24.0`, etc.
- MCP tags: `mcp-v0.1.0a1`, `mcp-v0.1.0`, etc.

This prevents tag conflicts and makes it clear which package each tag refers to.

## Publishing to PyPI

### Automatic Publishing

When semantic-release creates a new version:

1. A git tag is created (e.g., `mcp-v0.1.0a1`)
1. The package is built
1. Build artifacts are uploaded
1. The `publish-*-pypi` job publishes to PyPI using **trusted publishing**

### PyPI Trusted Publishers

Both packages are configured with PyPI trusted publishers:

- **katana-openapi-client**: Publishes from `release-client` job
- **katana-mcp-server**: Publishes from `release-mcp` job

No API tokens needed - authentication via GitHub OIDC.

## Manual Release (Emergency)

If you need to manually trigger a release:

### Option 1: Workflow Dispatch

```bash
gh workflow run release.yml
```

### Option 2: Manual Tag (MCP only)

The `release-mcp.yml` workflow can be triggered by pushing a tag:

```bash
git tag mcp-v0.1.1
git push origin mcp-v0.1.1
```

## Examples

### Example 1: Release MCP Server Only

```bash
# On branch: feature/add-inventory-tools
git add katana_mcp_server/src/katana_mcp/tools/inventory.py
git commit -m "feat(mcp): implement check_inventory tool

- Add CheckInventoryRequest and StockInfo models
- Implement tool using Products domain helper
- Add comprehensive unit tests"

git push origin feature/add-inventory-tools
# Create PR, merge to main
# → Triggers MCP release (e.g., 0.1.0a1 → 0.2.0a1)
```

### Example 2: Release Client Only

```bash
# On branch: feature/domain-helpers
git add katana_public_api_client/helpers/products.py
git commit -m "feat(client): add Products domain helper class

- Implement CRUD operations
- Add search and filtering methods
- Full test coverage"

git push origin feature/domain-helpers
# Create PR, merge to main
# → Triggers client release (e.g., 0.23.0 → 0.24.0)
```

### Example 3: Release Both (Separate Commits)

```bash
# First commit for client
git add katana_public_api_client/helpers/inventory.py
git commit -m "feat(client): add Inventory domain helper"

# Second commit for MCP
git add katana_mcp_server/src/katana_mcp/tools/inventory.py
git commit -m "feat(mcp): add inventory tools using new helper"

git push origin feature/inventory-support
# Create PR, merge to main
# → Triggers BOTH releases independently
```

## Changelog Management

Each package maintains its own changelog:

- **Client**: `docs/CHANGELOG.md`
- **MCP Server**: `katana_mcp_server/CHANGELOG.md`

Semantic-release automatically updates these files on each release.

## Testing Release Configuration

You can test the release configuration without actually releasing:

### Test Client Release

```bash
uv run semantic-release version --print --no-commit --no-tag --no-push
```

### Test MCP Release

```bash
uv run semantic-release version --print --no-commit --no-tag --no-push \
  -c katana_mcp_server/pyproject.toml
```

Note: These commands only work on the `main` branch or configured release branches.

## Troubleshooting

### "No release will be made"

**Cause**: No commits with `feat:`, `fix:`, or `perf:` since last release

**Solution**: Ensure your commits follow conventional commit format with appropriate
scopes

### "Branch isn't in any release groups"

**Cause**: Not on `main` branch or a configured release branch

**Solution**: Only `main` branch triggers releases. Test on feature branches won't work.

### Wrong Package Released

**Cause**: Missing or incorrect commit scope

**Solution**:

- Use `feat(client):` or `fix(client):` for client releases
- Use `feat(mcp):` or `fix(mcp):` for MCP releases
- Commits without scope default to client

### Dependency Between Packages

**Problem**: MCP server depends on client. If client version bumps, does MCP need to
release?

**Answer**: Only if MCP needs the new client features. Update
`katana_mcp_server/pyproject.toml` dependencies manually:

```toml
dependencies = [
    "katana-openapi-client>=0.24.0",  # Update minimum version
]
```

Then commit with `feat(mcp): update to client v0.24.0`

## Best Practices

1. **Use descriptive commit scopes**: Always include `(client)` or `(mcp)` scope for
   clarity
1. **Keep changes focused**: Avoid mixing client and MCP changes in single commits
1. **Update dependencies**: When MCP needs newer client version, update pyproject.toml
   explicitly
1. **Test before merging**: Ensure all CI checks pass before merging to `main`
1. **Review changelogs**: Check generated changelog entries before releases

## Future Enhancements

Potential improvements to the release process:

1. **Pre-release automation**: Automatically create pre-release versions for alpha/beta
1. **Dependency bump automation**: Auto-update MCP dependencies when client releases
1. **Release notes templates**: Custom templates for each package type
1. **Manual version override**: Allow manual version specification via workflow_dispatch

## References

- [Python Semantic Release Documentation](https://python-semantic-release.readthedocs.io/)
- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [UV Workspace Documentation](https://docs.astral.sh/uv/concepts/workspaces/)
