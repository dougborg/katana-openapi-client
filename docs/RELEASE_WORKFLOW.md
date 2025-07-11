# Release Workflow Guide

This document explains the automated release workflow for the Katana OpenAPI Client.

## Overview

The release workflow uses **automatic publishing to production PyPI** for every release:

1. **Automatic Release Creation** - Based on conventional commits
1. **Automatic PyPI Publishing** - Every release goes to production PyPI automatically

## Workflow Triggers

### Automatic Triggers

- **Push to main**: When code is pushed to the main branch
- **Semantic Release**: If commits follow conventional commit format, a new version is
  automatically created
- **Production PyPI**: New versions are automatically published to production PyPI

### Manual Triggers

- **Workflow Dispatch**: Use GitHub's "Run workflow" button to trigger releases manually

## Release Process

### Automatic Release Flow

1. **CI Tests**: Full test suite runs on all supported Python versions
1. **Semantic Release**: Version bumping based on conventional commits
1. **Package Build**: Create wheel and source distributions
1. **Production PyPI Upload**: Automatic publish to https://pypi.org/

## OIDC Trusted Publishing Setup

The workflow uses OpenID Connect (OIDC) for secure, keyless authentication:

### Production PyPI Configuration

- **Environment**: `PyPI Release`
- **Repository**: `https://pypi.org/`
- **Trusted Publisher**: GitHub Actions workflow

## Environment Configuration

### Required GitHub Environments

1. **`PyPI Release`** (automatic)

   - Protected environment with required reviewers (optional)
   - Automatic publishing on releases

### PyPI Trusted Publishing Setup

For production PyPI:

1. Go to your project settings
1. Navigate to "Trusted Publishing"
1. Add a new trusted publisher:
   - **Publisher**: GitHub
   - **Repository owner**: `dougborg`
   - **Repository name**: `katana-openapi-client`
   - **Workflow name**: `release.yml`
   - **Environment name**: `PyPI Release`

## Monitoring and Troubleshooting

### Workflow Status

- **Production PyPI**: Check <https://pypi.org/project/katana-openapi-client/>
- **GitHub Actions**: Monitor workflow runs in the Actions tab

### Testing a Release

After an automatic release, verify the package:

```bash
# Install from PyPI
pip install katana-openapi-client

# Test the package
python -c "from katana_public_api_client import KatanaClient; print('✅ Import successful')"
```

## Security Features

### Automatic Attestations

- All packages include cryptographic attestations
- Provides proof of authenticity and build integrity
- Automatically generated for PyPI

### Environment Protection

- Production releases can be protected with environment rules
- OIDC eliminates the need for long-lived API tokens

## Common Issues

1. **OIDC Authentication Failure**: Verify trusted publisher configuration
1. **Package Name Conflict**: Ensure package name is available
1. **Version Conflict**: Check that semantic release generated a new version
1. **Changelog Formatting**: The changelog is auto-generated in `docs/CHANGELOG.md` and
   formatted with mdformat

## Conventional Commits

The workflow uses conventional commits for automatic version bumping:

- `feat:` → Minor version bump (0.1.0 → 0.2.0)
- `fix:` → Patch version bump (0.1.0 → 0.1.1)
- `BREAKING CHANGE:` → Major version bump (0.1.0 → 1.0.0)

### Examples

```text
feat: add new retry configuration options
fix: resolve timeout handling in concurrent requests
docs: update API documentation
```

## Best Practices

1. **Use conventional commits** for automatic versioning
1. **Monitor GitHub Actions** for workflow failures
1. **Verify package integrity** after each release
1. **Keep environments secure** with proper access controls

## Related Documentation

- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Semantic Release](https://python-semantic-release.readthedocs.io/)
- [Poetry Publishing](https://python-poetry.org/docs/repositories/#publishing-to-pypi/)
