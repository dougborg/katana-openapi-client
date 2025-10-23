# Release Process

Releases are fully automated using
[python-semantic-release](https://python-semantic-release.readthedocs.io/).

## How It Works

When a PR is merged to `main`:

1. **CI Tests Run**: All tests must pass first
1. **Semantic Analysis**: Analyzes commit messages since last release
1. **Version Determination**: Calculates next version based on conventional commits:
   - `feat:` commits trigger MINOR version bump (0.x.0)
   - `fix:` commits trigger PATCH version bump (0.0.x)
   - `feat!:` or `BREAKING CHANGE:` triggers MAJOR version bump (x.0.0)
1. **Automated Updates**:
   - Version updated in `pyproject.toml` and `__init__.py`
   - `CHANGELOG.md` generated from commits
   - Git commit and tag created
   - Changes pushed to `main`
   - GitHub release published
   - Package built and published to PyPI

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) for automatic
releases:

```bash
# Feature (minor version bump)
git commit -m "feat: add new domain helper classes"

# Bug fix (patch version bump)
git commit -m "fix: correct rate limit retry logic"

# Breaking change (major version bump)
git commit -m "feat!: redesign client authentication"
# or
git commit -m "feat: new API

BREAKING CHANGE: removed legacy authentication method"

# Non-release commits (no version bump)
git commit -m "docs: update contributing guide"
git commit -m "chore: update dependencies"
git commit -m "test: add integration tests"
```

## For Contributors

**You don't need to do anything!** Just:

1. Write good commit messages following conventional commits
1. Merge your PR to `main`
1. The release workflow automatically handles versioning and publishing

## Manual Release (Rare)

Only needed if the automated workflow fails:

```bash
# Trigger workflow manually
gh workflow run release.yml
```

## Technical Details

### Protected Branch Setup

The `main` branch is protected with required status checks. The release workflow uses a
Personal Access Token (`SEMANTIC_RELEASE_TOKEN`) to bypass protection and push release
commits. This is configured via Repository Rulesets with the repository owner's Admin
role having exempt bypass.

### Workflow Configuration

See `.github/workflows/release.yml` for the complete workflow configuration.

### Release Workflow Steps

1. **test** job: Runs full CI pipeline (format check, lint, tests)
1. **release** job:
   - Checks out code with PAT
   - Runs python-semantic-release to analyze commits
   - Creates version bump commit if needed
   - Pushes commit and tag to main
   - Creates GitHub release
   - Builds package
1. **publish-pypi** job:
   - Downloads built artifacts
   - Publishes to PyPI using Trusted Publisher (OIDC)

### Troubleshooting

**Release not triggered?**

- Check if there are any `feat:` or `fix:` commits since the last release
- Verify the test job passed (release only runs after tests pass)
- Check Actions tab for workflow run details

**Release created but PyPI publish failed?**

- Verify PyPI Trusted Publisher is configured for this repository
- Check that workflow has `id-token: write` permission

**Protected branch error?**

- Verify `SEMANTIC_RELEASE_TOKEN` secret is set:
  ```bash
  gh secret list --repo dougborg/katana-openapi-client
  ```
- Check if PAT has expired (create new one and update secret)
- Ensure PAT has correct permissions (Contents: write, PRs: write, Workflows: write)
