# MCP Server Deployment Guide

This document describes how the Katana MCP Server is released and published to PyPI
using **[release-please](https://github.com/googleapis/release-please)** (manifest
mode). See [docs/RELEASE.md](../../docs/RELEASE.md) for the canonical, repo-wide
reference.

## Overview

Releases are **fully automated** via release-please. You don't manually update version
numbers or publish to PyPI - the CI/CD pipeline handles everything based on
conventional commits, gated behind a review step: merging a normal PR updates an
aggregated release PR, and merging *that* release PR is what actually ships anything.

## How Releases Work

### Automated Release Process

When a PR is merged to `main` with MCP-related changes:

1. **CI Tests Run**: All quality checks, tests, and security scans must pass
1. **release-please Analysis**: `release-please.yml` (the only workflow watching
   `main`) analyzes commits touching `katana_mcp_server/` since the last MCP release
1. **Version Calculation**: Determines next version based on commit types:
   - `feat(mcp):` → MINOR bump (0.1.0 → 0.2.0)
   - `fix(mcp):` → PATCH bump (0.1.0 → 0.1.1)
   - `feat(mcp)!:` → MAJOR bump (0.1.0 → 1.0.0)
1. **Release PR Updated**: version in `katana_mcp_server/pyproject.toml`,
   `CHANGELOG.md`, and the client-version floor + `uv.lock` (via
   `release-pr-prepare.yml`) are all proposed on release-please's aggregated release
   PR - nothing is pushed to `main` yet
1. **On Merge**: `release-please.yml` creates the `mcp-v{version}` tag and a **draft**
   GitHub Release at the merge commit
1. **Build and Publish** (triggered by the tag, via `publish.yml`):
   - Package built with `uv build --package katana-mcp-server`
   - Published to PyPI using Trusted Publisher (OIDC, no tokens)
   - Docker image built and pushed to GHCR
   - Assets attached to the draft release, then the release is published

## For Developers

### How to Trigger a Release

**Just write good commit messages with the `(mcp)` scope:**

```bash
# Feature (minor version bump)
git commit -m "feat(mcp): add search_products tool"

# Bug fix (patch version bump)
git commit -m "fix(mcp): correct stock level calculation"

# Breaking change (major version bump)
git commit -m "feat(mcp)!: redesign tool request models

BREAKING CHANGE: Tool request parameters now require explicit types"

# No release (documentation only)
git commit -m "docs(mcp): update README examples"
```

**That's it!** Merge your PR and the release happens automatically.

### Which Commits Trigger Releases?

| Commit Type   | Example                    | Release? | Version Bump        |
| ------------- | -------------------------- | -------- | ------------------- |
| `feat(mcp):`  | Add inventory tool         | ✅       | MINOR (0.1.0→0.2.0) |
| `fix(mcp):`   | Fix auth error             | ✅       | PATCH (0.1.0→0.1.1) |
| `perf(mcp):`  | Optimize query performance | ✅       | PATCH (0.1.0→0.1.1) |
| `feat(mcp)!:` | Breaking API change        | ✅       | MAJOR (0.1.0→1.0.0) |
| `docs(mcp):`  | Update documentation       | ❌       | No release          |
| `test(mcp):`  | Add unit tests             | ❌       | No release          |
| `chore(mcp):` | Update dependencies        | ❌       | No release          |
| `feat:` (no   | Feature without scope      | ❌       | Releases client     |
| scope)        |                            |          | instead             |

**IMPORTANT**: Always use the `(mcp)` scope for MCP server changes! Without it, the
client package will be released instead.

## Verify a Release

After a release is published (check
[GitHub Releases](https://github.com/dougborg/katana-openapi-client/releases)):

### 1. Check PyPI Page

Visit: https://pypi.org/project/katana-mcp-server/

Verify:

- ✅ New version is listed
- ✅ README renders correctly
- ✅ Project metadata is correct
- ✅ Installation command works

### 2. Test Installation from PyPI

```bash
# Create fresh test environment
cd /tmp
python3 -m venv test-pypi-install
source test-pypi-install/bin/activate

# Install from PyPI
pip install katana-mcp-server

# Verify installation
pip list | grep katana

# Test command (should require API key)
katana-mcp-server
# Expected: "KATANA_API_KEY environment variable is required"

# Clean up
deactivate
rm -rf /tmp/test-pypi-install
```

### 3. Test with Claude Desktop

Update Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop and verify:

- ✅ Server starts without errors
- ✅ Inventory tools appear in MCP tools list
- ✅ Tools work when invoked

## Manual Testing Before Release

Before merging a PR that will trigger a release, test locally:

### Run All Tests

```bash
cd katana_mcp_server

# Unit tests (fast)
uv run pytest tests/ -m "not integration"

# Integration tests (requires KATANA_API_KEY in .env)
uv run pytest tests/ -m integration

# All tests
uv run pytest tests/
```

### Test Local Build

```bash
cd katana_mcp_server

# Build package
uv build

# Install locally (in a test venv)
cd /tmp
python3 -m venv test-local
source test-local/bin/activate
pip install /path/to/katana-openapi-client/katana_mcp_server/dist/*.whl

# Test
katana-mcp-server --help

# Clean up
deactivate
rm -rf /tmp/test-local
```

## Emergency Manual Release

If the automated workflow fails, you can trigger a manual release:

### Option 1: Re-run GitHub Workflow

```bash
# Re-run the most recent publish run (e.g. after a transient PyPI failure)
gh run list --workflow=publish.yml
gh run rerun <run-id> --failed
```

### Option 2: Manual Tag (Last Resort)

Only use if release-please or `publish.yml` is completely broken:

```bash
# WARNING: This bypasses release-please and version management!
# Only use in emergencies after coordinating with maintainers

# Manually update version in pyproject.toml first
# Then create and push tag
git tag mcp-v0.1.0
git push origin mcp-v0.1.0

# This triggers publish.yml directly (build + PyPI publish + Docker),
# but does NOT create a GitHub Release for the tag - create one by hand
# (gh release create mcp-v0.1.0 ...) if publish.yml's asset-upload step
# has nothing to attach to.
```

**Note**: Manual tags bypass changelog generation and version file updates. Use
sparingly.

## Troubleshooting

### Release Not Triggered

**Symptom**: PR merged but no release created

**Causes**:

1. No `feat(mcp):` or `fix(mcp):` commits since last release
1. Forgot the `(mcp)` scope - released client instead
1. CI tests failed - release only runs after tests pass

**Solutions**:

- Check commit messages: `git log --oneline main`
- Verify scope is present: `git log --grep="(mcp)" main`
- Check GitHub Actions for failures

### Wrong Package Released

**Symptom**: Client package released instead of MCP server

**Cause**: Missing `(mcp)` scope in commit message

**Solution**: Use `feat(mcp):` or `fix(mcp):` for all MCP changes

### PyPI Publish Failed

**Symptom**: Release created but PyPI publish failed

**Causes**:

1. PyPI Trusted Publisher misconfigured
1. Version already exists on PyPI (can't overwrite)
1. PyPI service outage

**Solutions**:

1. Check PyPI Trusted Publisher configuration (no environment, correct repo/workflow)
1. Check if version exists: https://pypi.org/project/katana-mcp-server/#history
1. Check PyPI status: https://status.python.org/
1. Re-run the workflow: `gh run rerun <run-id> --failed`

### Tests Failed in CI

**Symptom**: PR checks failing, blocking release

**Solutions**:

1. Run tests locally: `uv run pytest tests/`
1. Check test output in GitHub Actions
1. Fix the issue and push new commit
1. Ensure commit uses `(mcp)` scope for release

### Version Conflict

**Symptom**: "Version X.Y.Z already exists on PyPI"

**Cause**: PyPI doesn't allow re-uploading the same version

**Solutions**:

1. This shouldn't happen with release-please (it always increments)
1. If it does, check if someone manually published that version
1. Force next version with additional commit: `fix(mcp): force version bump`

## Release Workflow Details

### release-please Configuration

Located in `release-please-config.json` at the repo root (component `mcp`, path
`katana_mcp_server`):

```jsonc
"katana_mcp_server": {
  "release-type": "python",
  "component": "mcp",
  "package-name": "katana-mcp-server",
  "changelog-path": "CHANGELOG.md"
}
```

`include-component-in-tag: true` preserves the `mcp-v{version}` tag format. The
current version is tracked in `.release-please-manifest.json`, not in a
`[tool.semantic_release]` block (that block was removed from
`katana_mcp_server/pyproject.toml`).

### GitHub Workflows

- **`.github/workflows/release-please.yml`** - the only workflow watching `main`.
  Opens/updates the aggregated release PR; on merge, creates the `mcp-v{version}` tag
  - draft GitHub Release.
- **`.github/workflows/release-pr-prepare.yml`** - runs only on release-please's PR
  branch; keeps `uv.lock` and the MCP server's `katana-openapi-client>=X` floor in
  sync with the proposed client version.
- **`.github/workflows/publish.yml`** - triggered by the `mcp-v*` tag push. Jobs:
  `publish-mcp-pypi` (PyPI) and `publish-mcp-docker` (GHCR, needs `publish-mcp-pypi`).

### PyPI Trusted Publisher

Configured at: https://pypi.org/manage/project/katana-mcp-server/settings/publishing/

- **Owner**: `dougborg`
- **Repository**: `katana-openapi-client`
- **Workflow**: `publish.yml`
- **Job**: `publish-mcp-pypi`
- **Environment**: (none) - unchanged by this migration; `publish.yml` intentionally
  does not scope this job to a GitHub Environment, matching how the publisher was
  originally registered

## Version Numbering

This project uses semantic versioning with pre-release identifiers:

### Version Format: `MAJOR.MINOR.PATCH[-prerelease]`

- **MAJOR**: Breaking changes (`feat(mcp)!:` or `BREAKING CHANGE:`)
- **MINOR**: New features (`feat(mcp):`)
- **PATCH**: Bug fixes (`fix(mcp):`, `perf(mcp):`)

### Pre-release Phases:

- **Alpha** (0.1.0a1, 0.1.0a2): Early development, unstable, breaking changes expected
- **Beta** (0.1.0b1): Feature complete, testing, API stabilizing
- **RC** (0.1.0rc1): Release candidate, final testing
- **Stable** (0.1.0, 1.0.0): Production-ready release

**Current Phase**: Alpha - API may change between versions

### Example Version Progression:

```
0.1.0a1  (first alpha - inventory tools)
  ↓ feat(mcp): add search
0.2.0a1  (new feature added)
  ↓ fix(mcp): auth error
0.2.1a1  (bug fix)
  ↓ feat(mcp): sales orders
0.3.0a1  (new feature)
  ↓ ready for beta
0.3.0b1  (beta testing)
  ↓ fix(mcp): critical bug
0.3.1b1  (bug fix in beta)
  ↓ ready for release
0.3.1    (stable release)
```

## Checklist for Contributors

Before submitting a PR that will trigger a release:

- [ ] All tests pass locally: `uv run pytest tests/`
- [ ] Commit messages use `(mcp)` scope
- [ ] Commit messages follow conventional commits
- [ ] README updated if adding new features
- [ ] Integration tests added/updated if needed
- [ ] Breaking changes documented in commit body (if any)

After PR is merged:

- [ ] Check GitHub Actions for successful release
- [ ] Verify new version on PyPI
- [ ] Test installation from PyPI
- [ ] Check GitHub Release notes

## Related Documentation

- **Main Release Guide**: [docs/RELEASE.md](../docs/RELEASE.md) - Monorepo release
  process (release-please, manifest mode)
- **Contributing**: [docs/CONTRIBUTING.md](../docs/CONTRIBUTING.md) - Commit message
  format
- **MCP Documentation Index**: [docs/mcp-server/README.md](../docs/mcp-server/README.md)
  \- All MCP documentation

## Related Links

- **PyPI Project**: https://pypi.org/project/katana-mcp-server/
- **GitHub Repository**: https://github.com/dougborg/katana-openapi-client
- **GitHub Releases**:
  https://github.com/dougborg/katana-openapi-client/releases?q=mcp-v
- **Main Client**: https://pypi.org/project/katana-openapi-client/
