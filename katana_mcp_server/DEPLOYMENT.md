# MCP Server Deployment Guide

This document describes how to package and publish the Katana MCP Server to PyPI.

## Prerequisites

Before publishing:

1. **Ensure all tests pass**:
   ```bash
   cd katana_mcp_server
   uv run pytest tests/ -m "not integration"
   ```

2. **Update version number** in three places:
   - `katana_mcp_server/pyproject.toml` - `version = "X.Y.Za#"`
   - `katana_mcp_server/src/katana_mcp/__init__.py` - `__version__ = "X.Y.Za#"`
   - `katana_mcp_server/src/katana_mcp/server.py` - `mcp = FastMCP(..., version="X.Y.Za#", ...)`
   - `katana_mcp_server/tests/test_package.py` - Update version in assertions
   - `katana_mcp_server/tests/test_server.py` - Update version in assertions

3. **Update README.md** with release notes and version info

## Local Build and Test

### Step 1: Build the Package

```bash
cd katana_mcp_server
uv build
```

This creates:
- `dist/katana_mcp_server-X.Y.Za#-py3-none-any.whl` (wheel)
- `dist/katana_mcp_server-X.Y.Za#.tar.gz` (source distribution)

**Note**: The dist folder will be created at the repository root, not in `katana_mcp_server/`.

### Step 2: Test Local Installation

Create a fresh virtual environment and test the package:

```bash
# Create test environment
cd /tmp
python3 -m venv test-mcp-install
source test-mcp-install/bin/activate

# Install from local wheel
pip install /path/to/katana-openapi-client/dist/katana_mcp_server-X.Y.Za#-py3-none-any.whl

# Verify installation
pip list | grep katana

# Test the command works
katana-mcp-server --help

# Test it requires API key (expected to fail)
katana-mcp-server
# Should show: "KATANA_API_KEY environment variable is required"

# Clean up
deactivate
rm -rf /tmp/test-mcp-install
```

### Expected Results

- ✅ Package installs without errors
- ✅ Command `katana-mcp-server` is available
- ✅ Server requires KATANA_API_KEY (correct behavior)

## PyPI Publishing

### Option A: Automated via Git Tag (Recommended)

This triggers the GitHub Actions workflow that builds, tests, and publishes automatically.

```bash
# Tag the release
git tag mcp-vX.Y.Za#
git push origin mcp-vX.Y.Za#

# GitHub Actions will automatically:
# 1. Run tests
# 2. Build package
# 3. Publish to PyPI (using trusted publisher)
```

### Option B: Manual Publish

For manual publishing (requires PyPI API token or trusted publisher setup):

```bash
cd katana_mcp_server

# Ensure build artifacts exist
uv build

# Install twine (if not already installed)
pip install twine

# Upload to PyPI
# This will use PyPI trusted publisher if configured,
# or prompt for credentials if not
twine upload dist/*

# Or use API token:
# twine upload -u __token__ -p <your-token> dist/*
```

## PyPI Trusted Publisher Setup

To enable automated publishing via GitHub Actions, configure PyPI trusted publisher:

1. **Go to PyPI**: https://pypi.org/manage/account/publishing/

2. **Add Trusted Publisher**:
   - **PyPI Project Name**: `katana-mcp-server`
   - **Owner**: `dougborg`
   - **Repository name**: `katana-openapi-client`
   - **Workflow name**: `release-mcp.yml`
   - **Environment name**: (leave blank)

3. **Save** the configuration

**Note**: The package name will be created on first publish if it doesn't exist yet.

## Verify PyPI Release

After publishing (either method):

### 1. Check PyPI Page

Visit: https://pypi.org/project/katana-mcp-server/

Verify:
- ✅ Version X.Y.Za# is listed
- ✅ README renders correctly
- ✅ Project metadata is correct
- ✅ Installation command shown: `pip install katana-mcp-server==X.Y.Za#`

### 2. Test Installation from PyPI

```bash
# Create fresh test environment
cd /tmp
python3 -m venv test-pypi-install
source test-pypi-install/bin/activate

# Install from PyPI
pip install katana-mcp-server==X.Y.Za#

# Verify installation
pip list | grep katana

# Test command
katana-mcp-server --help

# Clean up
deactivate
rm -rf /tmp/test-pypi-install
```

**Expected**: Package installs from PyPI without errors.

### 3. Test with Claude Desktop

Update Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server==X.Y.Za#"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop and verify:
- ✅ Server starts without errors
- ✅ 3 inventory tools appear in MCP tools list
- ✅ Tools work when invoked

## Create GitHub Release

After successful PyPI publishing, create a GitHub release:

```bash
# Create release with notes
gh release create mcp-vX.Y.Za# \
  --title "Katana MCP Server vX.Y.Z-alpha#" \
  --notes "$(cat <<'EOF'
## Katana MCP Server vX.Y.Z-alpha#

First alpha release of the Katana MCP Server! 🎉

### Features

- **3 Inventory Tools**:
  - `check_inventory` - Check stock levels for a SKU
  - `list_low_stock_items` - Find products below threshold
  - `search_products` - Search by name or SKU

### Installation

\`\`\`bash
pip install katana-mcp-server==X.Y.Za#
\`\`\`

### Claude Desktop Setup

Add to your \`claude_desktop_config.json\`:

\`\`\`json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server==X.Y.Za#"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
\`\`\`

### What's Next

This alpha release focuses on inventory management. Future releases will add:
- Sales order management tools
- Purchase order management tools
- Manufacturing order management tools

### Known Limitations

- Alpha release - API may change
- Only inventory tools in this version
- Requires \`katana-openapi-client>=0.22.0\`

### Documentation

See [README](https://github.com/dougborg/katana-openapi-client/blob/main/katana_mcp_server/README.md) for complete documentation.
EOF
)" \
  --prerelease

# Attach build artifacts (optional)
gh release upload mcp-vX.Y.Za# dist/*
```

## Troubleshooting

### Build Fails

**Issue**: `uv build` fails with errors

**Solutions**:
1. Ensure you're in the `katana_mcp_server` directory
2. Run `uv sync` to install dependencies
3. Check `pyproject.toml` for syntax errors
4. Ensure all source files are present in `src/katana_mcp/`

### Tests Fail

**Issue**: Tests fail during CI or local testing

**Solutions**:
1. Run tests locally: `uv run pytest tests/ -v -m "not integration"`
2. Check version numbers match in all files
3. Verify imports work: `uv run python -c "import katana_mcp; print(katana_mcp.__version__)"`

### Import Errors After Installation

**Issue**: `ModuleNotFoundError: No module named 'katana_mcp'`

**Solutions**:
1. Check wheel contents: `python -m zipfile -l dist/*.whl`
2. Verify `[tool.hatch.build.targets.wheel]` in `pyproject.toml` has `packages = ["src/katana_mcp"]`
3. Ensure source files are in `src/katana_mcp/` not just `katana_mcp/`

### PyPI Upload Fails

**Issue**: `twine upload` fails with authentication error

**Solutions**:
1. Configure PyPI trusted publisher (see above)
2. Or use API token: `twine upload -u __token__ -p <token> dist/*`
3. Ensure you have maintainer access to the PyPI project

### Version Conflicts

**Issue**: PyPI rejects upload because version already exists

**Solutions**:
1. PyPI doesn't allow re-uploading the same version
2. Increment the version number (e.g., `0.1.0a1` → `0.1.0a2`)
3. Test releases thoroughly before publishing

## Version Numbering

This project uses semantic versioning with alpha/beta markers:

- **Alpha releases**: `0.1.0a1`, `0.1.0a2`, etc. (unstable, breaking changes expected)
- **Beta releases**: `0.1.0b1`, `0.1.0b2`, etc. (feature complete, testing)
- **Release candidates**: `0.1.0rc1`, `0.1.0rc2`, etc. (final testing)
- **Stable releases**: `0.1.0`, `0.2.0`, `1.0.0`, etc.

## Checklist for Release

Before publishing:

- [ ] All tests pass: `uv run pytest tests/ -m "not integration"`
- [ ] Version updated in all 5 files (pyproject.toml, __init__.py, server.py, test_package.py, test_server.py)
- [ ] README.md updated with release notes
- [ ] Local build succeeds: `uv build`
- [ ] Local installation test passes
- [ ] PyPI trusted publisher configured (first time only)

After publishing:

- [ ] PyPI page shows correct version and README
- [ ] Installation from PyPI works
- [ ] Works with Claude Desktop via uvx
- [ ] GitHub release created with notes

## Related Links

- **PyPI Project**: https://pypi.org/project/katana-mcp-server/
- **GitHub Repository**: https://github.com/dougborg/katana-openapi-client
- **Main Client**: https://pypi.org/project/katana-openapi-client/
- **PyPI Publishing Guide**: https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
