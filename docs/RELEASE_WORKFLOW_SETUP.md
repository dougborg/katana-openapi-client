# Automated Release Workflow Setup

This guide documents how the automated release workflow is configured to work with
protected branches.

## Overview

The release workflow uses `python-semantic-release` to automatically:

1. Analyze commits since the last release
1. Determine the next version number (using semantic versioning)
1. Update version in `pyproject.toml` and `__init__.py`
1. Generate/update `CHANGELOG.md`
1. Create a git commit and tag
1. Push to the `main` branch
1. Create a GitHub release
1. Publish to PyPI

## The Challenge

The `main` branch is protected with:

- Required pull request reviews
- Required status checks (tests, linting, security scans)
- Linear history enforcement

The workflow needs to push commits directly to `main`, but the default `GITHUB_TOKEN`
cannot bypass these protections.

## The Solution: Personal Access Token (PAT)

Following the
[official python-semantic-release documentation](https://python-semantic-release.readthedocs.io/en/latest/configuration/automatic-releases/github-actions.html),
we use a **Fine-Grained Personal Access Token**.

### Why This Works

1. **PAT authenticates as the repository owner** (not as `github-actions[bot]`)
1. **Repository owner has Admin role** (highest permission level)
1. **Repository Ruleset exempts RepositoryRole "Maintain"** from all rules
1. **Admin > Maintain**, so the PAT gets automatic exempt bypass
1. **Workflow can push without triggering branch protection**

### Configuration

#### 1. Repository Ruleset (Already Configured)

The `main` branch is protected by a Repository Ruleset named "Protect Main":

- **Status**: Active
- **Required status checks**: `test (3.11)`, `test (3.12)`, `test (3.13)`, `quality`,
  `security-scan`
- **PR requirements**: 1 approval required
- **Bypass actors**: RepositoryRole "Maintain" with `exempt` mode

View ruleset: https://github.com/dougborg/katana-openapi-client/rules/6756621

#### 2. Personal Access Token (Manual Setup Required)

**Create the token:**

1. Go to: https://github.com/settings/personal-access-tokens/new

1. Configure:

   - **Token name**: `semantic-release-katana-openapi-client`

   - **Expiration**: 90 days (or your preference)

   - **Description**: For python-semantic-release to push to protected main branch

   - **Repository access**: Only select repositories → `katana-openapi-client`

   - **Permissions**:

     - Contents: Read and write ✓
     - Metadata: Read-only (automatically selected) ✓
     - Pull requests: Read and write ✓
     - Workflows: Read and write ✓

1. Click "Generate token" and **copy it** (shown only once!)

**Add as repository secret:**

```bash
gh secret set SEMANTIC_RELEASE_TOKEN --repo dougborg/katana-openapi-client
```

Paste the token when prompted.

#### 3. Workflow Configuration (Already Updated)

The release workflow at `.github/workflows/release.yml` uses the PAT:

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0
      token: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}  # ← PAT for git operations

  - name: Python Semantic Release
    uses: python-semantic-release/python-semantic-release@v10.2.0
    with:
      github_token: ${{ secrets.SEMANTIC_RELEASE_TOKEN }}  # ← PAT for GitHub API
```

## Security Considerations

✅ **Scoped to single repository**: Fine-grained PAT only works on this repo ✅ **Limited
permissions**: Only the minimum required permissions ✅ **Expiration**: Token expires
after 90 days (renewable) ✅ **Audit trail**: All commits show as authored by the PAT
owner ✅ **Protected secret**: Stored as GitHub encrypted secret ✅ **Role-based bypass**:
Uses existing ruleset bypass (not a backdoor)

## How It Works

When a PR is merged to `main`:

1. **CI tests run** on the merge commit (as normal)
1. **Release workflow triggers** (after tests pass)
1. **Semantic release analyzes** commits since last release
1. **If release needed**:
   - Version is bumped
   - CHANGELOG is updated
   - Commit is created using PAT authentication
   - Commit is pushed to `main` (bypasses ruleset via Admin role)
   - Git tag is created and pushed
   - GitHub release is published
   - Package is built and published to PyPI
1. **If no release needed**: Workflow exits cleanly

## Troubleshooting

### Workflow fails with "protected branch" error

**Check:**

1. Is the `SEMANTIC_RELEASE_TOKEN` secret set?

   ```bash
   gh secret list --repo dougborg/katana-openapi-client
   ```

1. Has the PAT expired? Create a new one and update the secret.

1. Does the PAT have the correct permissions? (Contents: write, PRs: write, Workflows:
   write)

### Release not triggered after merge

**Check:**

1. Are there any `feat:` or `fix:` commits since the last release?
1. Did the test job pass? (Release only runs after tests pass)
1. Check the Actions tab for workflow run details

### Release created but PyPI publish failed

**Check:**

1. Is PyPI Trusted Publisher configured for this repository?
1. Does the workflow have `id-token: write` permission?

## References

- [Python Semantic Release - GitHub Actions](https://python-semantic-release.readthedocs.io/en/latest/configuration/automatic-releases/github-actions.html)
- [GitHub Repository Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets)
- [Fine-Grained Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)

______________________________________________________________________

**Last Updated**: 2025-10-23 **Status**: Configured and ready (pending PAT creation)
