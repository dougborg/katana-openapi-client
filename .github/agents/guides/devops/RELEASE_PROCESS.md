# Release Process Guide

Guide for managing releases with semantic-release in this monorepo.

## Quick Reference

**Monorepo releases:**

- `feat(client):` → Releases katana-openapi-client (MINOR)
- `fix(client):` → Releases katana-openapi-client (PATCH)
- `feat(mcp):` → Releases katana-mcp-server (MINOR)
- `fix(mcp):` → Releases katana-mcp-server (PATCH)
- `feat(client)!:` → Releases katana-openapi-client (MAJOR)

**Non-release commits:**

- `docs:`, `chore:`, `test:`, `ci:`, `refactor:` → No release

______________________________________________________________________

## Semantic Versioning

### Version Format: MAJOR.MINOR.PATCH

**MAJOR (Breaking Changes):**

```bash
git commit -m "feat(client)!: remove deprecated sync methods

BREAKING CHANGE: Synchronous client methods removed.
Use async methods with asyncio.run() instead."
```

Effect: 0.30.0 → 1.0.0

**MINOR (New Features):**

```bash
git commit -m "feat(mcp): add inventory management tools"
```

Effect: 0.7.0 → 0.8.0

**PATCH (Bug Fixes):**

```bash
git commit -m "fix(client): handle null pagination cursor"
```

Effect: 0.30.0 → 0.30.1

______________________________________________________________________

## Release Workflow

### Automated Release Process

**Trigger:** Merge to `main` branch

**Steps:**

1. semantic-release analyzes commits since last release
1. Determines version bump based on commit types
1. Updates version in `pyproject.toml`
1. Generates CHANGELOG.md
1. Creates git tag
1. Creates GitHub release
1. (Optional) Publishes to PyPI

### Manual Verification

**Before merge to main:**

```bash
# Verify conventional commits
git log --oneline origin/main..HEAD

# Check commit format
git log --oneline --grep="^feat" --grep="^fix" --all-match

# Ensure proper scope
git log --oneline | grep -E "(feat|fix)\((client|mcp)\):"
```

______________________________________________________________________

## Commit Scopes for Releases

### Client Package (`katana-openapi-client`)

```bash
# New feature
git commit -m "feat(client): add domain helper classes"
→ Releases client with MINOR bump

# Bug fix
git commit -m "fix(client): handle timeout errors"
→ Releases client with PATCH bump

# Breaking change
git commit -m "feat(client)!: migrate to Pydantic v2"
→ Releases client with MAJOR bump
```

### MCP Server Package (`katana-mcp-server`)

```bash
# New feature
git commit -m "feat(mcp): add sales order tools"
→ Releases MCP server with MINOR bump

# Bug fix
git commit -m "fix(mcp): correct order filtering"
→ Releases MCP server with PATCH bump

# Breaking change
git commit -m "feat(mcp)!: change tool parameter structure"
→ Releases MCP server with MAJOR bump
```

### No Scope (Defaults to Client)

```bash
# These are equivalent:
git commit -m "feat: add retry mechanism"
git commit -m "feat(client): add retry mechanism"

# Both release client package
```

______________________________________________________________________

## Non-Release Commits

These commit types **do not trigger releases:**

```bash
# Documentation
docs: update README
docs(client): add API examples
docs(mcp): update tool documentation

# Chores
chore: update dependencies
chore: configure linting rules

# Tests
test: add coverage for edge cases
test(client): fix flaky test

# CI/CD
ci: add parallel test execution
ci: update workflow

# Refactoring
refactor: simplify error handling
refactor(mcp): extract validation logic

# Performance
perf: optimize pagination

# Build
build: update uv configuration
```

______________________________________________________________________

## Release Scenarios

### Scenario 1: Client Feature Release

**Commits on branch:**

```
feat(client): add batch operations helper
test(client): add batch operations tests
docs(client): add batch operations guide
```

**Merge to main triggers:**

- Version: 0.30.0 → 0.31.0 (MINOR bump)
- Changelog entry for feature
- Git tag: client-v0.31.0
- GitHub release

### Scenario 2: MCP Bug Fix

**Commits on branch:**

```
fix(mcp): handle empty inventory responses
test(mcp): add test for empty responses
```

**Merge to main triggers:**

- Version: 0.7.0 → 0.7.1 (PATCH bump)
- Changelog entry for fix
- Git tag: mcp-v0.7.1
- GitHub release

### Scenario 3: Both Packages

**Commits on branch:**

```
feat(client): add new API endpoint
feat(mcp): add tool for new endpoint
```

**Merge to main triggers:**

- Client: 0.30.0 → 0.31.0
- MCP: 0.7.0 → 0.8.0
- Two separate releases

### Scenario 4: Breaking Change

**Commits on branch:**

```
feat(client)!: migrate from attrs to Pydantic

BREAKING CHANGE: All domain models now use Pydantic.
Update imports and model initialization code.
See MIGRATION.md for details.
```

**Merge to main triggers:**

- Version: 0.30.0 → 1.0.0 (MAJOR bump)
- Prominent changelog entry
- Migration guide recommended

______________________________________________________________________

## Version Tags

### Tag Format

**Client package:**

```
client-v0.31.0
client-v0.31.1
client-v1.0.0
```

**MCP server package:**

```
mcp-v0.7.0
mcp-v0.8.0
mcp-v1.0.0
```

### View Tags

```bash
# List all tags
git tag -l

# List client tags
git tag -l "client-v*"

# List MCP tags
git tag -l "mcp-v*"

# View tag details
git show client-v0.31.0
```

______________________________________________________________________

## Changelog Generation

### Automatic Generation

**semantic-release generates:**

- CHANGELOG.md in each package directory
- Organized by release version
- Grouped by commit type (Features, Bug Fixes, etc.)
- Links to commits and PRs

### Example Changelog Entry

```markdown
## [0.31.0](https://github.com/user/repo/compare/client-v0.30.0...client-v0.31.0) (2025-01-15)

### Features

* **client:** add batch operations helper ([abc1234](https://github.com/user/repo/commit/abc1234))
* **client:** add domain helper classes ([def5678](https://github.com/user/repo/commit/def5678))

### Bug Fixes

* **client:** handle null pagination cursor ([ghi9012](https://github.com/user/repo/commit/ghi9012))
```

______________________________________________________________________

## Release Monitoring

### Check Release Status

```bash
# List recent releases
gh release list

# View specific release
gh release view client-v0.31.0

# View release in browser
gh release view client-v0.31.0 --web
```

### Release Workflow Status

```bash
# Check workflow runs
gh run list --workflow=release.yml

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

______________________________________________________________________

## Manual Release (Emergency)

**Only if automated release fails:**

```bash
# 1. Determine version
# Calculate manually based on commits

# 2. Update version in pyproject.toml
# Edit manually

# 3. Update CHANGELOG.md
# Add entry manually

# 4. Commit
git commit -m "chore(release): client v0.31.0"

# 5. Tag
git tag client-v0.31.0

# 6. Push
git push origin main --tags

# 7. Create GitHub release
gh release create client-v0.31.0 \
  --title "client v0.31.0" \
  --notes "See CHANGELOG.md"
```

**Note:** Only do this if semantic-release is broken. Otherwise, let automation handle
it.

______________________________________________________________________

## Release Checklist

### Before Merge

- [ ] All commits follow conventional format
- [ ] Proper scopes used (`client` or `mcp`)
- [ ] Breaking changes documented with `!` and `BREAKING CHANGE:`
- [ ] All CI checks passing
- [ ] PR approved

### After Merge

- [ ] semantic-release workflow completed
- [ ] New version tag created
- [ ] GitHub release published
- [ ] CHANGELOG.md updated
- [ ] No errors in release workflow

______________________________________________________________________

## Troubleshooting

### Release Not Triggered

**Check:**

1. Are commits using `feat:` or `fix:`?
1. Are non-release types used? (`docs:`, `chore:`, etc.)
1. Did semantic-release workflow run?

```bash
# View workflow runs
gh run list --workflow=release.yml

# If no runs, check workflow file
cat .github/workflows/release.yml
```

### Wrong Version Bump

**Symptoms:**

- Expected MINOR, got PATCH
- Expected MAJOR, got MINOR

**Common causes:**

- Missing `!` for breaking change
- Using `fix:` instead of `feat:`
- Missing scope causes wrong package release

**Fix:** Can't undo release easily. Document in next release notes.

### Multiple Releases from One Merge

**This is normal** if commits affect both packages:

```
feat(client): add feature
feat(mcp): add related feature
```

Results in two releases (client + MCP).

______________________________________________________________________

## Best Practices

### DO ✅

- **Use conventional commits** always
- **Add BREAKING CHANGE:** footer for breaking changes
- **Test before merging to main**
- **Monitor release workflow**
- **Review generated changelog**
- **Coordinate breaking changes**

### DON'T ❌

- **Don't merge without proper commit format**
- **Don't forget scope** for multi-package changes
- **Don't manually edit versions** (let semantic-release handle it)
- **Don't force push to main**
- **Don't skip CI checks**

______________________________________________________________________

## Related Documentation

- [COMMIT_STANDARDS.md](../shared/COMMIT_STANDARDS.md) - Conventional commits
- [docs/MONOREPO_SEMANTIC_RELEASE.md](../../../../docs/MONOREPO_SEMANTIC_RELEASE.md) -
  Complete guide
- [Semantic Versioning](https://semver.org/) - Version specification

______________________________________________________________________

## Summary

**Release triggers:**

- `feat(client):` → Client MINOR release
- `fix(client):` → Client PATCH release
- `feat(mcp):` → MCP MINOR release
- `feat!:` → MAJOR release (breaking change)

**Process:**

1. Write conventional commits
1. Merge to main
1. semantic-release automates everything
1. Monitor with `gh release list`

**Remember:** Trust the automation. Manual releases only in emergencies!
