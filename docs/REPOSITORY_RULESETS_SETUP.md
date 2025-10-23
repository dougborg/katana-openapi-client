# Repository Rulesets Setup Guide

This guide explains how to configure GitHub Repository Rulesets to allow the automated
release workflow to bypass branch protection on the `main` branch.

## Background

The release workflow uses `python-semantic-release` which needs to:

1. Push version bump commits to `main`
1. Create and push git tags
1. Create GitHub releases

However, the `main` branch is protected with required status checks. The modern solution
(as of 2025) is to use **Repository Rulesets** with an **exemption** for
`github-actions[bot]`.

## Why Repository Rulesets over Branch Protection?

- **More granular control**: Define bypass rules for specific actors
- **Exemption type**: Silent bypass with audit trail (added September 2025)
- **No PAT required**: Uses built-in `GITHUB_TOKEN` securely
- **Recommended by GitHub**: Modern replacement for branch protection

## Step-by-Step Configuration

### Step 1: Access Repository Settings

1. Go to: https://github.com/dougborg/katana-openapi-client/settings
1. Click on **"Rules"** in the left sidebar (under "Code and automation")
1. Click **"Rulesets"** tab

### Step 2: Create a New Ruleset

1. Click **"New ruleset"** → **"New branch ruleset"**

1. Configure the ruleset:

   **Ruleset Name**: `main-branch-protection`

   **Enforcement status**: `Active`

### Step 3: Configure Branch Targeting

Under **"Target branches"**:

1. Click **"Add target"** → **"Include by pattern"**
1. Enter pattern: `main`
1. This ensures the ruleset applies only to the `main` branch

### Step 4: Configure Branch Protection Rules

Enable the following rules:

#### ✅ Require a pull request before merging

- ☑ **Require approvals**: `1`
- ☑ **Dismiss stale pull request approvals when new commits are pushed**
- ☑ **Require review from Code Owners** (if you have CODEOWNERS file)

#### ✅ Require status checks to pass

- ☑ **Require branches to be up to date before merging**
- Add required status checks:
  - `test (3.11)`
  - `test (3.12)`
  - `test (3.13)`
  - `quality`
  - `security-scan`

#### ✅ Block force pushes

#### ✅ Require linear history (optional but recommended)

### Step 5: Configure Bypass List (CRITICAL)

This is the key step that allows the release workflow to work!

Under **"Bypass list"**:

1. Click **"Add bypass"**
1. Select **"Repository roles"** → **"Maintain"** or **"Admin"** (allows repository
   maintainers to bypass)
1. Click **"Add bypass"** again
1. Select **"Apps"** → Search for and select **"GitHub Actions"**
1. **IMPORTANT**: Change the bypass mode to **"Exempt"** (not "Bypass")
   - "Exempt" = Silent bypass, no approval needed
   - "Bypass" = Requires explicit approval

### Step 6: Remove Old Branch Protection (if exists)

If you previously had branch protection rules on `main`:

1. Go to **Settings** → **Branches**
1. Delete the old branch protection rule for `main`
1. Repository Rulesets will replace it

### Step 7: Save and Test

1. Click **"Create"** to save the ruleset
1. The workflow should now be able to push to `main` automatically

## Verification

After configuration, verify the setup:

```bash
# Check that rulesets are active
gh api repos/dougborg/katana-openapi-client/rulesets

# Trigger a test release (if ready)
git push origin main
```

The release workflow should now:

1. ✅ Run tests
1. ✅ Analyze commits with semantic-release
1. ✅ Push version bump commit to `main` (bypassing protection)
1. ✅ Create and push git tag
1. ✅ Create GitHub release
1. ✅ Publish to PyPI

## Troubleshooting

### If the workflow still fails with "protected branch" error:

1. **Verify the ruleset is Active** (not Disabled or Evaluate mode)
1. **Check that GitHub Actions is in the bypass list** with **Exempt** mode
1. **Ensure old branch protection rules are deleted**
1. **Check workflow permissions**: The release job has `contents: write` permission

### If you see "status checks required" error:

1. Make sure status checks are configured in the ruleset
1. Verify the exact names match your CI workflow job names
1. The `test` job in the release workflow ensures checks pass before releasing

### If GitHub Actions bypass isn't working:

1. Try using **"Exempt"** mode instead of **"Bypass"** mode
1. Verify you're on the latest GitHub plan (Rulesets are free for public repos)
1. Check the
   [GitHub Changelog](https://github.blog/changelog/2025-09-10-github-ruleset-exemptions-and-repository-insights-updates/)
   for updates

## Security Considerations

✅ **Secure**: Uses built-in `GITHUB_TOKEN` (no PAT required) ✅ **Auditable**: All
exemption uses are logged ✅ **Least privilege**: Only `github-actions[bot]` can bypass,
not all workflows ✅ **Status checks still run**: The workflow runs all CI checks before
releasing

## References

- [GitHub Repository Rules Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub Ruleset Exemptions Changelog (Sept 2025)](https://github.blog/changelog/2025-09-10-github-ruleset-exemptions-and-repository-insights-updates/)
- [Python Semantic Release Documentation](https://python-semantic-release.readthedocs.io/)

______________________________________________________________________

**Last Updated**: 2025-10-23 **Status**: Active configuration for automated releases
