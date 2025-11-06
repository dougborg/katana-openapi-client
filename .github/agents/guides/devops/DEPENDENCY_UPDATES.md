# Dependency Updates Guide

Guide for managing dependencies with uv in this monorepo.

## Quick Commands

```bash
# Show all dependencies
uv pip list

# Show outdated packages
uv pip list --outdated

# Add new dependency
uv add <package>

# Add dev dependency
uv add --dev <package>

# Update specific package
uv add "package>=2.0"

# Update all packages
uv lock --upgrade

# Sync dependencies
uv sync --all-extras
```

______________________________________________________________________

## Dependency Management with uv

### Adding Dependencies

**Production dependency:**

```bash
# Add to katana-openapi-client
cd katana_public_api_client
uv add httpx

# Add to katana-mcp-server
cd katana_mcp_server
uv add pydantic
```

**Development dependency:**

```bash
uv add --dev pytest
uv add --dev ruff
```

**With version constraints:**

```bash
uv add "httpx>=0.27.0,<1.0"
uv add "pydantic>=2.0"
```

### Updating Dependencies

**Update single package:**

```bash
uv add "httpx>=0.27.2"  # Update to minimum 0.27.2
```

**Update all packages:**

```bash
# Regenerate lock file with latest versions
uv lock --upgrade

# Sync to apply updates
uv sync --all-extras
```

**Update and test:**

```bash
uv lock --upgrade
uv sync --all-extras
uv run poe check  # Verify nothing broke
```

______________________________________________________________________

## Monorepo Dependency Structure

### Workspace Configuration

**Root pyproject.toml:**

```toml
[tool.uv.workspace]
members = ["katana_public_api_client", "katana_mcp_server"]
```

### Package Dependencies

**katana-openapi-client** (independent):

- httpx, attrs, python-dateutil, etc.
- No dependency on MCP server

**katana-mcp-server** (depends on client):

```toml
[project]
dependencies = [
    "katana-openapi-client",  # Internal dependency
    "mcp>=1.0.0",
    # ...
]
```

______________________________________________________________________

## Common Tasks

### Security Updates

**Vulnerable dependency:**

```bash
# Update to secure version
uv add "requests>=2.31.0"

# Verify fix
uv pip list | grep requests

# Commit
git add uv.lock pyproject.toml
git commit -m "security: update requests to 2.31.0 (CVE-2023-XXXXX)"
```

### Dependency Conflicts

**Symptom:**

```
error: Failed to resolve dependencies:
  package-a requires foo>=2.0
  package-b requires foo<2.0
```

**Resolution:**

```bash
# Option 1: Update both packages
uv add "package-a>=2.0" "package-b>=3.0"

# Option 2: Add explicit constraint
uv add "foo>=1.9,<2.0"

# Option 3: Use override (last resort)
# Add to pyproject.toml:
[tool.uv]
override-dependencies = ["foo==1.9.5"]
```

### Lock File Issues

**Out of sync:**

```bash
# Regenerate lock file
uv lock

git add uv.lock
git commit -m "build: regenerate lock file"
```

**Corrupted:**

```bash
# Delete and regenerate
rm uv.lock
uv lock

# Test
uv sync --all-extras
uv run poe check
```

______________________________________________________________________

## Dependabot Configuration

**File:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "python"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "dependencies"
      - "github-actions"
```

**Handling Dependabot PRs:**

```bash
# Review PR
gh pr view <dependabot-pr>

# Check what changed
gh pr diff <dependabot-pr>

# Run tests locally
gh pr checkout <dependabot-pr>
uv sync --all-extras
uv run poe check

# Approve and merge if passing
gh pr review <dependabot-pr> --approve
gh pr merge <dependabot-pr> --squash
```

______________________________________________________________________

## Version Pinning Strategy

### Direct Dependencies (Flexible)

```toml
[project]
dependencies = [
    "httpx>=0.27.0",        # Allow patch updates
    "pydantic>=2.0,<3.0",   # Allow minor updates
    "mcp>=1.0.0",           # Allow all updates
]
```

### Why Flexible Versions?

- Get security updates automatically
- Benefit from bug fixes
- Reduce maintenance burden
- Lock file provides reproducibility

### When to Pin Strictly

```toml
dependencies = [
    "legacy-package==1.2.3",  # Known breakage in 1.2.4
]
```

Only pin when:

- Known incompatibility
- Critical stability requirement
- Temporary workaround

______________________________________________________________________

## Testing Dependency Updates

### Pre-Update Checklist

```bash
# 1. Ensure clean state
git status  # Should be clean

# 2. Run full test suite
uv run poe check

# 3. Note current versions
uv pip list > deps-before.txt
```

### Update and Test

```bash
# 4. Update dependencies
uv lock --upgrade

# 5. Sync
uv sync --all-extras

# 6. Run full validation
uv run poe check

# 7. Note new versions
uv pip list > deps-after.txt

# 8. Review changes
diff deps-before.txt deps-after.txt
```

### Rollback if Needed

```bash
# Restore old lock file
git checkout uv.lock

# Resync
uv sync --all-extras

# Verify
uv run poe check
```

______________________________________________________________________

## CI Integration

### Dependency Caching

**Already configured in workflows:**

```yaml
- uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true
```

### Dependency Review

**Security check on PRs:**

```yaml
# .github/workflows/security.yml
- name: Dependency Review
  uses: actions/dependency-review-action@v4
```

______________________________________________________________________

## Common Issues

### "Package not found"

**Symptom:**

```
error: Package 'foo' not found
```

**Fix:**

```bash
# Verify package name on PyPI
# https://pypi.org/project/foo/

# Use correct name
uv add correct-package-name
```

### "Version conflict"

**Symptom:**

```
error: Cannot satisfy requirements
```

**Debug:**

```bash
# Check dependency tree
uv pip tree

# Find conflicting requirements
uv pip show package-name
```

### "Lock file out of date"

**Symptom:**

```
error: The lockfile is out of sync
```

**Fix:**

```bash
uv lock
git add uv.lock
git commit -m "build: update lock file"
```

______________________________________________________________________

## Best Practices

### DO ✅

- **Keep dependencies up to date**
- **Review Dependabot PRs promptly**
- **Test after updates**
- **Use version ranges for flexibility**
- **Commit lock file with updates**
- **Document pinned versions**

### DON'T ❌

- **Don't ignore security updates**
- **Don't pin without reason**
- **Don't update without testing**
- **Don't commit broken lock files**
- **Don't skip CI checks**

______________________________________________________________________

## Summary

**Quick workflow:**

1. `uv lock --upgrade` - Update all
1. `uv sync --all-extras` - Apply updates
1. `uv run poe check` - Test
1. `git add uv.lock pyproject.toml` - Commit
1. `git commit -m "build: update dependencies"`

**Key files:**

- `pyproject.toml` - Dependency requirements
- `uv.lock` - Pinned versions
- `.github/dependabot.yml` - Automated updates

**Remember:** Lock file provides reproducibility, flexible versions enable updates!
