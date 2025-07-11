# Semantic Release Guide

## Overview

This project uses Python Semantic Release to automatically manage versioning and
releases based on commit messages.

## Commit Message Format

Use conventional commits format:

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- **feat**: New feature (triggers minor version bump)
- **fix**: Bug fix (triggers patch version bump)
- **perf**: Performance improvement (triggers patch version bump)
- **docs**: Documentation changes (no version bump)
- **style**: Code style changes (no version bump)
- **refactor**: Code refactoring (no version bump)
- **test**: Test changes (no version bump)
- **chore**: Maintenance tasks (no version bump)
- **ci**: CI/CD changes (no version bump)
- **build**: Build system changes (no version bump)

### Breaking Changes

For breaking changes (major version bump), add `BREAKING CHANGE:` in the footer or use
`!` after the type:

```text
feat!: remove deprecated auto-pagination helpers

BREAKING CHANGE: The auto-pagination helpers have been removed.
Use the new ResilientAsyncTransport which handles pagination automatically.
```

## Examples

```bash
# Feature (0.1.0 -> 0.2.0)
git commit -m "feat(client): add automatic retry mechanism"

# Bug fix (0.1.0 -> 0.1.1)
git commit -m "fix(transport): handle connection timeouts properly"

# Performance improvement (0.1.0 -> 0.1.1)
git commit -m "perf(client): optimize request caching"

# Documentation (no version change)
git commit -m "docs: update API examples"

# Breaking change (0.1.0 -> 1.0.0)
git commit -m "feat!: redesign client initialization API"
```

## Local Testing

Before pushing commits, test what the next version would be:

```bash
# Check configuration and see what would happen
./scripts/check_release.sh

# Or use poetry directly
poetry run semantic-release version --dry-run
```

## Release Process

### Automatic (Recommended)

1. Push commits to `main` branch
1. GitHub Actions will automatically:
   - Run tests
   - Analyze commits since last release
   - Determine next version
   - Update version in `pyproject.toml` and `__init__.py`
   - Generate changelog
   - Create GitHub release
   - Publish to PyPI

### Manual

```bash
# Generate new version and changelog
poetry run semantic-release version

# Publish to PyPI (if not done by CI)
poetry run semantic-release publish
```

## Configuration

Semantic release is configured in `pyproject.toml`:

- Version files: `pyproject.toml`, `katana_public_api_client/__init__.py`
- Changelog: `CHANGELOG.md`
- Build command: `poetry build`
- Commit author: `github-actions[bot]`

## Troubleshooting

### No release triggered

- Check commit messages follow conventional format
- Ensure commits contain changes that warrant a version bump
- Verify GitHub Actions has proper permissions

### Release failed

- Check GitHub Actions logs
- Ensure `PYPI_TOKEN` secret is set
- Verify package builds successfully: `poetry build`

## Best Practices

1. **Write clear commit messages**: Follow conventional commits
1. **Test locally**: Use `./scripts/check_release.sh` before pushing
1. **Group related changes**: Use semantic commits for logical units
1. **Document breaking changes**: Always explain impact in commit body
1. **Review changelog**: Check generated changelog makes sense
