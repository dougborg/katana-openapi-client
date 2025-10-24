# Release Process

This repository uses **monorepo semantic-release** to independently version and release
two packages:

1. **katana-openapi-client** - The main Python API client
1. **katana-mcp-server** - The Model Context Protocol server

Each package is released independently based on **commit scopes**, allowing them to
evolve at their own pace.

## Quick Reference

### For Client Package Releases

```bash
git commit -m "feat(client): add new domain helper classes"
git commit -m "fix(client): resolve pagination edge case"
```

### For MCP Server Releases

```bash
git commit -m "feat(mcp): add inventory tools"
git commit -m "fix(mcp): correct stock level calculation"
```

### No Release Needed

```bash
git commit -m "docs: update contributing guide"
git commit -m "chore: update dependencies"
git commit -m "test: add integration tests"
```

## How Releases Work

### Automated Release Workflow

When a PR is merged to `main`, the `.github/workflows/release.yml` workflow runs **two
independent semantic-release jobs**:

1. **Client Release** (`release-client` job):

   - Checks for commits with `feat(client):`, `fix(client):`, or no scope
   - Calculates next version based on conventional commits
   - Creates tag: `client-v{version}` (e.g., `client-v0.24.0`)
   - Updates `pyproject.toml` and `__init__.py` versions
   - Generates `docs/CHANGELOG.md` from commits
   - Builds and publishes to PyPI as `katana-openapi-client`

1. **MCP Server Release** (`release-mcp` job):

   - Checks for commits with `feat(mcp):` or `fix(mcp):`
   - Calculates next version based on conventional commits
   - Creates tag: `mcp-v{version}` (e.g., `mcp-v0.1.0`)
   - Updates `katana_mcp_server/pyproject.toml` version
   - Generates `katana_mcp_server/CHANGELOG.md` from commits
   - Builds and publishes to PyPI as `katana-mcp-server`

Both jobs run **in parallel** and are **completely independent**.

### Version Bumps

| Commit Type                       | Example                         | Version Bump                   |
| --------------------------------- | ------------------------------- | ------------------------------ |
| `feat(scope):`                    | `feat(mcp): add search tool`    | MINOR (0.1.0 → 0.2.0)          |
| `fix(scope):`                     | `fix(client): resolve auth bug` | PATCH (0.1.0 → 0.1.1)          |
| `perf(scope):`                    | `perf(mcp): optimize queries`   | PATCH (0.1.0 → 0.1.1)          |
| `feat(scope)!:` or Breaking       | `feat(client)!: redesign API`   | MAJOR (0.1.0 → 1.0.0)          |
| Other (`docs:`, `chore:`, `test`) | `docs(mcp): update README`      | NO BUMP                        |
| `feat:` (no scope)                | `feat: add pagination`          | Client MINOR (0.23.0 → 0.24.0) |

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) with scopes:

### Structure

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Examples

**Client Package Release:**

```bash
feat(client): add Products domain helper class

- Implement CRUD operations
- Add search and filtering methods
- Full test coverage
```

**MCP Server Release:**

```bash
feat(mcp): implement check_inventory tool

- Add CheckInventoryRequest and StockInfo models
- Implement tool using Products domain helper
- Add comprehensive unit tests

Closes #35
```

**Breaking Change (Major Version):**

```bash
feat(client)!: redesign authentication flow

BREAKING CHANGE: Removed legacy BasicAuth class. Use KatanaClient with API key instead.
```

**Documentation (No Release):**

```bash
docs: update monorepo release documentation

Added comprehensive guide for semantic-release with scopes.
```

## For Contributors

**You don't need to do anything special!** Just:

1. Write good commit messages following conventional commits **with scopes**
1. Use `(client)` scope for client changes, `(mcp)` scope for MCP server changes
1. Merge your PR to `main`
1. The release workflow automatically handles versioning and publishing

### Which Scope Should I Use?

- **Changed files in `katana_public_api_client/`?** → Use `(client)` scope
- **Changed files in `katana_mcp_server/`?** → Use `(mcp)` scope
- **Changed both?** → Make two separate commits, one for each scope
- **Changed only docs or CI?** → Use `docs:` or `ci:` (no scope, no release)

## Release Workflow Steps

### 1. CI Tests Run

All tests must pass before release:

- Code quality checks (ruff, mypy)
- Unit and integration tests
- Security scans (CodeQL, Semgrep, Trivy)

### 2. Semantic-Release Analysis (Per Package)

For **each package**, semantic-release:

- Analyzes commits since last release for that package
- Determines if a release is needed
- Calculates the next version number

### 3. Version Updates (If Releasing)

For each package being released:

- Updates version in `pyproject.toml`
- Updates version variables (`__init__.py` for client)
- Generates/updates changelog
- Creates release commit
- Creates version tag

### 4. Build and Publish

For each package being released:

- Builds Python wheel and source distribution
- Publishes to PyPI using **Trusted Publisher** (OIDC, no API tokens)
- Creates GitHub release with auto-generated notes

## Current Versions

- **katana-openapi-client**: See [PyPI](https://pypi.org/project/katana-openapi-client/)
- **katana-mcp-server**: See [PyPI](https://pypi.org/project/katana-mcp-server/)

## Tag Format

- **Client tags**: `client-v0.23.0`, `client-v0.24.0`, etc.
- **MCP tags**: `mcp-v0.1.0`, `mcp-v0.2.0`, etc.

This prevents tag conflicts and makes it clear which package each tag refers to.

## Manual Release (Emergency Only)

If the automated workflow fails or you need to force a release:

### Option 1: Trigger Workflow Manually

```bash
gh workflow run release.yml
```

This will analyze commits and release any packages with releasable changes.

### Option 2: Manual Tag (Advanced)

**For MCP Server only** (there's a backup workflow):

```bash
git tag mcp-v0.1.1
git push origin mcp-v0.1.1
```

This triggers `.github/workflows/release-mcp.yml` which builds and publishes the MCP
package directly.

## Troubleshooting

### "No release will be made"

**Cause**: No commits with `feat:`, `fix:`, or `perf:` since last release for that
package.

**Solution**: Ensure your commits follow conventional commit format with appropriate
scopes:

- Use `feat(client):` or `fix(client):` for client releases
- Use `feat(mcp):` or `fix(mcp):` for MCP releases

### Release not triggered?

**Check**:

- Are there `feat:` or `fix:` commits with the correct scope?
- Did the test job pass? (release only runs after tests pass)
- Check Actions tab for workflow run details

### Wrong package released?

**Cause**: Missing or incorrect commit scope.

**Solution**:

- Use `feat(client):` or `fix(client):` for client releases
- Use `feat(mcp):` or `fix(mcp):` for MCP releases
- Commits without scope default to client package

### Release created but PyPI publish failed?

**Check**:

- Verify PyPI Trusted Publisher is configured for the repository
- Ensure workflow has `id-token: write` permission
- Check PyPI status page for outages

### Protected branch error?\*\*

**Check**:

- Verify `SEMANTIC_RELEASE_TOKEN` secret is set:
  ```bash
  gh secret list --repo dougborg/katana-openapi-client
  ```
- Ensure PAT has correct permissions (Contents: write, PRs: write)
- Verify PAT hasn't expired

### Version conflict?

**Cause**: PyPI version already exists (can happen if manual release conflicts with
automated).

**Solution**: Semantic-release will skip the publish step. Wait for next release cycle.

## Technical Details

### Protected Branch Setup

The `main` branch is protected with required status checks. The release workflow uses a
Personal Access Token (`SEMANTIC_RELEASE_TOKEN`) to bypass protection and push release
commits.

### Workflow Configuration

See `.github/workflows/release.yml` for the complete workflow configuration.

### PyPI Trusted Publishers

Both packages use PyPI Trusted Publishers for secure, tokenless authentication:

- **katana-openapi-client**: Published from `release-client` job
- **katana-mcp-server**: Published from `release-mcp` job

Configuration: PyPI Project Settings → Publishing → Trusted Publishers

### Semantic-Release Configuration

Each package has its own semantic-release configuration:

- **Client**: `pyproject.toml` (root) - `[tool.semantic_release]`
- **MCP Server**: `katana_mcp_server/pyproject.toml` - `[tool.semantic_release]`

Configuration includes:

- Version file locations
- Tag format
- Commit message format
- Changelog generation
- Build commands

## Further Reading

- **[MONOREPO_SEMANTIC_RELEASE.md](MONOREPO_SEMANTIC_RELEASE.md)** - Comprehensive guide
  with examples
- **[Conventional Commits](https://www.conventionalcommits.org/)** - Commit message
  specification
- **[Python Semantic Release](https://python-semantic-release.readthedocs.io/)** -
  Official documentation
- **[PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)** - OIDC-based
  publishing
