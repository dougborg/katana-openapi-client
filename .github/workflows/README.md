# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Katana OpenAPI Client project.

## Workflows

### [ci.yml](ci.yml)

**Trigger:** Pull requests to `main` branch

**Purpose:** Continuous integration checks for pull requests

**Steps:**

- Install dependencies with uv
- Run full CI pipeline (`uv run poe ci`)
  - Format checking
  - Linting (ruff, mypy, yamllint)
  - Tests with coverage
  - OpenAPI validation

**Permissions:** `contents: read`

### [docs.yml](docs.yml)

**Trigger:**

- Push to `main` branch (when docs-related files change)
- Manual workflow dispatch

**Purpose:** Build and deploy documentation to GitHub Pages

**Steps:**

- Build MkDocs documentation
- Upload documentation artifacts
- Deploy to GitHub Pages

**Permissions:** `contents: read`, `pages: write`, `id-token: write`

**Note:** This workflow only runs when documentation files change (docs/\*\*,
mkdocs.yml, etc.) to avoid unnecessary builds.

### [release.yml](release.yml)

**Trigger:**

- Push to `main` branch
- Manual workflow dispatch

**Purpose:** Automated releases using semantic versioning for both packages

**Jobs:**

1. **test**: Run full CI pipeline
1. **release-client**: Create client package release
   - Uses Python Semantic Release
   - Creates `client-v*` tags
   - Builds distribution packages
1. **release-mcp**: Create MCP server package release
   - Uses Python Semantic Release
   - Creates `mcp-v*` tags
   - Builds distribution packages
1. **publish-client-pypi**: Publish client to PyPI (only if client released)
   - Uses trusted publishing (OIDC)
   - Includes package attestations
1. **publish-mcp-pypi**: Publish MCP to PyPI (only if MCP released)
   - Uses trusted publishing (OIDC)
   - Includes package attestations
1. **publish-mcp-docker**: Publish MCP Docker image to GHCR (only if MCP released)

**Permissions:**

- test: `contents: read`
- release-\*: `contents: write`, `id-token: write`
- publish-\*: `id-token: write`

**Note:** This workflow supports monorepo releases using commit scopes. See
[MONOREPO_SEMANTIC_RELEASE.md](../../docs/MONOREPO_SEMANTIC_RELEASE.md) for details.

### [security.yml](security.yml)

**Trigger:** Weekly schedule (Sundays at 00:00 UTC)

**Purpose:** Security scanning and dependency audits

**Steps:**

- Dependency vulnerability scanning
- Code security analysis
- License compliance checks

**Permissions:** `contents: read`, `security-events: write`

### [update-mcp-dependency.yml](update-mcp-dependency.yml)

**Trigger:** After successful completion of Release workflow

**Purpose:** Automatically update MCP's client dependency when a new client version is
released

**Steps:**

- Check for new `client-v*` tags created in the Release workflow
- Extract the new client version number
- Update `katana_mcp_server/pyproject.toml` dependency specification
- Update `uv.lock` file
- Create a PR with conventional commit message `feat(mcp): update client dependency to vX.Y.Z`

**Permissions:** `contents: write`, `pull-requests: write`

**How it works:**

1. Detects if Release workflow created a new `client-v*` tag
1. Compares tag timestamp with workflow start time to confirm it's new
1. Checks current MCP dependency version
1. Skips if dependency is already up to date
1. Updates dependency and creates PR for review
1. When PR is merged, triggers new MCP release via `feat(mcp):` commit

See [Automated Dependency
Management](../../docs/MONOREPO_SEMANTIC_RELEASE.md#automated-dependency-management)
for details.

### [copilot-setup-steps.yml](copilot-setup-steps.yml)

**Type:** Reusable workflow

**Purpose:** Common setup steps for GitHub Copilot integrations

**Provides:**

- Dependency installation
- Environment configuration
- Caching setup

## Workflow Orchestration

```mermaid
graph TD
    A[Push to main] --> B[CI checks]
    A --> C[Release workflow]
    A --> D[Docs workflow]

    B --> E{Tests pass?}
    E -->|Yes| F[Continue]
    E -->|No| G[Fail]

    C --> H{Semantic Release}
    H -->|Client changes| I[Create Client Release]
    H -->|MCP changes| J[Create MCP Release]
    H -->|No changes| K[Skip]
    
    I --> L[Publish Client to PyPI]
    I --> M[Trigger Update MCP Dependency]
    
    J --> N[Publish MCP to PyPI]
    J --> O[Publish MCP to GHCR]
    
    M --> P{Dependency outdated?}
    P -->|Yes| Q[Create PR: feat mcp: update client]
    P -->|No| R[Skip]
    
    Q --> S[Merge PR]
    S --> T[Trigger MCP Release]

    D --> U{Docs changed?}
    U -->|Yes| V[Build & Deploy]
    U -->|No| W[Skip]

    style A fill:#e1f5ff
    style I fill:#d4edda
    style J fill:#d4edda
    style L fill:#d4edda
    style N fill:#d4edda
    style O fill:#d4edda
    style V fill:#d4edda
    style Q fill:#fff3cd
```

## Configuration

### Secrets Required

- `GITHUB_TOKEN` - Automatically provided by GitHub Actions
- PyPI publishing uses Trusted Publishers (no manual tokens needed)

### Environments

- **PyPI Release** - Protected environment for PyPI publishing
  - URL: https://pypi.org/p/katana-openapi-client
- **github-pages** - GitHub Pages deployment environment

### Branch Protection

- `main` branch requires:
  - CI checks to pass
  - Up-to-date branches
  - No direct pushes (PRs only)

## Local Testing

Test workflows locally using [act](https://github.com/nektos/act):

```bash
# Test CI workflow
act pull_request -W .github/workflows/ci.yml

# Test docs build (without deploy)
act workflow_dispatch -W .github/workflows/docs.yml

# Test release (dry-run)
act push -W .github/workflows/release.yml
```

## Maintenance

### Updating Actions

Keep actions up to date by:

1. Monitoring Dependabot alerts
1. Reviewing action changelogs
1. Testing in a branch before merging

### Adding New Workflows

When adding new workflows:

1. Create the workflow file
1. Update this README
1. Test locally with `act`
1. Create a PR for review
1. Update branch protection rules if needed

## Troubleshooting

### Common Issues

**Dependency update PR not created:**

- Check that Release workflow completed successfully
- Verify a new `client-v*` tag was created
- Check if MCP dependency is already up to date
- Review update-mcp-dependency workflow logs
- Ensure `SEMANTIC_RELEASE_TOKEN` has `pull-requests: write` permission

**MCP release not triggering after dependency update:**

- Ensure the dependency update PR was merged to `main`
- Check that PR commit message follows format: `feat(mcp): update client dependency to vX.Y.Z`
- Review release workflow logs for MCP changes detection
- Verify semantic-release configuration in `katana_mcp_server/pyproject.toml`

**Docs not deploying:**

- Check that `docs/**` files were actually changed
- Verify GitHub Pages is enabled in repository settings
- Check workflow logs for build errors

**Release not creating:**

- Ensure commits follow conventional commit format
- Check semantic-release configuration in `pyproject.toml`
- Review workflow logs for PSR errors

**PyPI publish failing:**

- Verify Trusted Publisher is configured in PyPI
- Check that release was actually created
- Review PyPI environment protection rules

### Debug Mode

Enable workflow debug logging:

```bash
# In repository settings > Secrets and variables > Actions
# Add repository secret:
ACTIONS_STEP_DEBUG=true
ACTIONS_RUNNER_DEBUG=true
```

## Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Python Semantic Release](https://python-semantic-release.readthedocs.io/)
- [MkDocs](https://www.mkdocs.org/)
