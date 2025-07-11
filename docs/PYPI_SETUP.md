# PyPI Publishing Setup Guide

This guide covers setting up the repository for automated publishing to PyPI via GitHub
Actions.

## Prerequisites

1. **PyPI Account**: Create accounts on [PyPI](https://pypi.org) and
   [Test PyPI](https://test.pypi.org)
1. **GitHub Repository**: Push the code to a GitHub repository
1. **API Tokens**: Generate API tokens for both PyPI and Test PyPI

## Step 1: Generate PyPI API Tokens

### PyPI (Production)

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
1. Click "Add API token"
1. Set scope to "Entire account" (for initial setup)
1. Copy the generated token (starts with `pypi-`)

### Test PyPI (Testing)

1. Go to [Test PyPI Account Settings](https://test.pypi.org/manage/account/)
1. Click "Add API token"
1. Set scope to "Entire account"
1. Copy the generated token (starts with `pypi-`)

## Step 2: Configure GitHub Secrets

In your GitHub repository settings:

1. Go to **Settings** → **Secrets and variables** → **Actions**

1. Add the following repository secrets:

   ```text
   PYPI_API_TOKEN=pypi-your-production-token-here
   TEST_PYPI_API_TOKEN=pypi-your-test-token-here
   ```

## Step 3: Set Up GitHub Environments

For additional security, create GitHub environments:

1. Go to **Settings** → **Environments**
1. Create two environments:
   - `pypi` (for production releases)
   - `test-pypi` (for test releases)
1. Configure environment protection rules as needed

## Step 4: Publishing Workflow

### Test Release (Manual)

To test the publishing workflow:

1. Go to **Actions** tab in GitHub
1. Select **Release** workflow
1. Click **Run workflow**
1. Enter a test version (e.g., `1.0.0-test.1`)
1. This will publish to Test PyPI for verification

### Production Release (Automatic)

For production releases:

1. Update version in `pyproject.toml`

1. Update `CHANGELOG.md` with release notes

1. Commit changes to main branch

1. Create and push a git tag:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

1. GitHub Actions will automatically:

   - Run tests
   - Build the package
   - Publish to PyPI
   - Create a GitHub Release

## Step 5: Verify Installation

After publishing, test the package installation:

```bash
# Install from PyPI
pip install katana-openapi-client

# Test import
python -c "from katana_public_api_client import KatanaClient; print('✅ Package installed successfully')"
```

## Version Management

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner
- **PATCH** version when you make backwards compatible bug fixes

Example version progression:

- `1.0.0` → `1.0.1` (bug fix)
- `1.0.1` → `1.1.0` (new feature)
- `1.1.0` → `2.0.0` (breaking change)

## Troubleshooting

### Common Issues

1. **Token permissions**: Ensure API tokens have correct scopes
1. **Package name conflicts**: PyPI package names must be unique
1. **Version conflicts**: Cannot upload same version twice to PyPI

### Testing Locally

Test package building locally:

```bash
# Build package
poetry build

# Check package
poetry run twine check dist/*

# Test upload to Test PyPI (optional)
poetry run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## Security Best Practices

1. **Never commit API tokens** to the repository
1. **Use environment protection rules** for production releases
1. **Regularly rotate API tokens**
1. **Review dependencies** for security vulnerabilities
1. **Enable 2FA** on PyPI accounts

## Monitoring

After setup, monitor:

- Package downloads on [PyPI stats](https://pypistats.org/)
- Security alerts from GitHub
- Dependency updates from Dependabot
- CI/CD pipeline health

## Support

For issues with:

- **PyPI publishing**: Check [PyPI Help](https://pypi.org/help/)
- **GitHub Actions**: See
  [GitHub Actions documentation](https://docs.github.com/en/actions)
- **Package building**: Review [Poetry documentation](https://python-poetry.org/docs/)
