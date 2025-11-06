# CI Debugging Guide

Guide for troubleshooting GitHub Actions CI/CD failures.

## Quick CI Commands

```bash
# View PR checks
gh pr checks <pr-number>

# View workflow runs
gh run list --workflow=ci.yml --limit 10

# View specific run
gh run view <run-id>

# View run logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id> --failed
```

______________________________________________________________________

## CI Workflow Overview

### Main Workflows

**ci.yml** - Main CI pipeline

- Quality checks (ruff format, ruff check, mypy)
- Tests (Python 3.11, 3.12, 3.13)
- Runs on: PRs, pushes to main

**security.yml** - Security scanning

- Dependency review
- Security vulnerability scanning
- Runs on: PRs, pushes to main

**codeql.yml** - CodeQL analysis

- Static analysis for security issues
- Runs on: PRs, pushes to main, schedule

**docs.yml** - Documentation build

- MkDocs build validation
- Runs on: PRs affecting docs/, pushes to main

______________________________________________________________________

## Common Failure Patterns

### 1. Quality Check Failures

#### Ruff Format Failures

**Symptom:**

```
Error: Files would be reformatted:
  katana_mcp_server/src/katana_mcp/tools/inventory.py
```

**Fix:**

```bash
# Locally format the code
uv run poe format

# Commit and push
git add .
git commit -m "style: apply ruff formatting"
git push
```

#### Ruff Lint Failures

**Symptom:**

```
katana_mcp_server/src/katana_mcp/tools/inventory.py:42:5: F841 Local variable `result` is assigned to but never used
```

**Fix:**

```bash
# Auto-fix linting issues
uv run poe fix

# Or manually fix and commit
# Then push
git commit -am "fix: address linting issues"
git push
```

#### MyPy Type Check Failures

**Symptom:**

```
katana_mcp_server/src/katana_mcp/tools/inventory.py:42: error: Incompatible return value type (got "str", expected "int")
```

**Fix:**

```bash
# Fix type issues in code
# Then verify locally
uv run poe agent-check

git commit -am "fix: correct type annotations"
git push
```

______________________________________________________________________

### 2. Test Failures

#### Flaky Tests

**Symptom:**

```
tests/integration/test_orders.py::test_create_order FAILED
AssertionError: Connection timeout
```

**Debug:**

```bash
# Run test locally multiple times
for i in {1..10}; do uv run pytest tests/integration/test_orders.py::test_create_order || break; done

# Check for timing issues, network dependencies
```

**Fix:**

- Add retries for network operations
- Increase timeouts
- Mock external dependencies
- Mark as flaky with `@pytest.mark.flaky(reruns=3)`

#### Environment-Specific Failures

**Symptom:**

```
Test passes locally but fails in CI
```

**Common causes:**

- Missing environment variables
- Different Python versions
- Dependency version mismatches
- Timing/race conditions

**Fix:**

```bash
# Check CI environment
- name: Debug environment
  run: |
    python --version
    uv pip list
    env | sort

# Add to .github/workflows/ci.yml temporarily
```

#### Missing Dependencies

**Symptom:**

```
ModuleNotFoundError: No module named 'pytest_asyncio'
```

**Fix:**

```bash
# Ensure dependency in pyproject.toml
uv add --dev pytest-asyncio

# Commit lock file
git add uv.lock pyproject.toml
git commit -m "build: add missing test dependency"
git push
```

______________________________________________________________________

### 3. Build Failures

#### uv sync Failures

**Symptom:**

```
error: Failed to download distributions
```

**Causes:**

- Network issues in CI
- Dependency resolution conflicts
- PyPI outage

**Fix:**

```bash
# Check for dependency conflicts locally
uv sync --all-extras

# If resolution conflict, update constraints
uv add "package>=1.0,<2.0"

# Regenerate lock file
git add uv.lock
git commit -m "build: resolve dependency conflict"
git push
```

#### Lock File Out of Sync

**Symptom:**

```
error: The lockfile is out of sync with the pyproject.toml
```

**Fix:**

```bash
# Regenerate lock file
uv lock

git add uv.lock
git commit -m "build: regenerate lock file"
git push
```

______________________________________________________________________

### 4. Documentation Build Failures

#### MkDocs Build Errors

**Symptom:**

```
ERROR - Config value 'nav': File not found: docs/guide.md
```

**Fix:**

```bash
# Test docs build locally
uv run poe docs-build

# Fix missing files or broken links
# Commit and push
git commit -am "docs: fix broken documentation links"
git push
```

#### Missing API References

**Symptom:**

```
WARNING - Could not find 'katana_mcp.tools.inventory' in docstrings
```

**Fix:**

- Ensure docstrings exist for all public APIs
- Check mkdocstrings configuration
- Verify import paths are correct

______________________________________________________________________

### 5. Security Scan Failures

#### Dependency Vulnerabilities

**Symptom:**

```
Vulnerability found in package 'requests' version 2.28.0
CVE-2023-XXXXX
```

**Fix:**

```bash
# Update vulnerable package
uv add "requests>=2.31.0"

# Verify no vulnerabilities
uv pip list | grep requests

git add uv.lock pyproject.toml
git commit -m "security: update requests to fix CVE-2023-XXXXX"
git push
```

#### Dependency Review Failures

**Symptom:**

```
Dependency review detected 3 new dependencies with security concerns
```

**Fix:**

- Review flagged dependencies
- Update to secure versions
- If false positive, document rationale

______________________________________________________________________

## Debugging Workflow

### Step 1: Identify Failure

```bash
# View all PR checks
gh pr checks <pr-number>

# Output shows:
# X quality - failing
# ✓ test (3.11) - passing
# ✓ test (3.12) - passing
# ✓ test (3.13) - passing
```

### Step 2: View Logs

```bash
# Get run ID from checks
gh pr checks <pr-number> --json url

# View logs
gh run view <run-id> --log

# Or view in browser
gh pr checks <pr-number> --web
```

### Step 3: Reproduce Locally

```bash
# Match CI environment
python --version  # Should match CI (3.11, 3.12, or 3.13)

# Run same commands as CI
uv sync --all-extras
uv run poe check  # Runs full validation

# Or run specific check
uv run poe quick-check  # Format + lint
uv run poe agent-check  # Format + lint + type
```

### Step 4: Fix and Verify

```bash
# Fix the issue
# ...

# Verify fix locally
uv run poe check

# Commit and push
git commit -am "fix: resolve CI failure"
git push

# Monitor CI
gh pr checks <pr-number> --watch
```

______________________________________________________________________

## CI Configuration Files

### .github/workflows/ci.yml

**Key sections:**

```yaml
# Quality check job
quality:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
    - run: uv sync --all-extras
    - run: uv run poe agent-check

# Test jobs (matrix)
test:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      python-version: ["3.11", "3.12", "3.13"]
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v4
      with:
        python-version: ${{ matrix.python-version }}
    - run: uv sync --all-extras
    - run: uv run poe test
```

### Modifying CI

**To add a new check:**

```yaml
# Add step to quality job
- name: Check OpenAPI spec
  run: uv run poe validate-openapi
```

**To change Python versions:**

```yaml
# Update matrix
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13", "3.14"]  # Add 3.14
```

______________________________________________________________________

## Performance Optimization

### Cache Dependencies

```yaml
# Already configured in workflows
- uses: astral-sh/setup-uv@v4
  with:
    enable-cache: true  # Caches uv dependencies
```

### Parallel Test Execution

```yaml
# Tests already run in parallel via pytest-xdist
- run: uv run poe test  # Uses -n auto (4 workers)
```

### Skip Unnecessary Runs

**Path filters** (add to workflow):

```yaml
on:
  pull_request:
    paths-ignore:
      - 'docs/**'
      - '**.md'
      - '.github/copilot/**'
```

______________________________________________________________________

## Emergency Procedures

### CI is Completely Broken

**Symptom:** All checks failing across all PRs

**Actions:**

1. Check GitHub Status: https://www.githubstatus.com/
1. Check PyPI Status: https://status.python.org/
1. Review recent workflow changes
1. Revert problematic commit if identified

### Flaky Tests Blocking All PRs

**Temporary mitigation:**

```bash
# Skip flaky test temporarily
@pytest.mark.skip(reason="Flaky test blocking CI - Issue #XXX")
def test_flaky_operation():
    ...

# Create issue to fix properly
gh issue create --title "Fix flaky test: test_flaky_operation"
```

### Dependency Resolution Deadlock

**Symptom:** uv sync fails with circular dependencies

**Actions:**

```bash
# Clear lock file and regenerate
rm uv.lock
uv lock --upgrade

# Or add constraints
uv add "problematic-package>=1.0,<1.5"
```

______________________________________________________________________

## Best Practices

### DO ✅

- **Run `uv run poe check` before pushing**
- **Monitor CI after pushing**
- **Fix failures immediately**
- **Keep workflows simple**
- **Use caching for dependencies**
- **Document non-obvious fixes**

### DON'T ❌

- **Don't merge with failing checks**
- **Don't skip tests to "fix later"**
- **Don't disable checks without documenting why**
- **Don't ignore flaky tests**
- **Don't commit lock file changes without testing**

______________________________________________________________________

## Summary

**Quick debugging process:**

1. `gh pr checks <pr-number>` - Identify failure
1. `gh run view <run-id> --log` - View logs
1. Reproduce locally with `uv run poe check`
1. Fix and verify
1. Push and monitor: `gh pr checks <pr-number> --watch`

**Common fixes:**

- Format: `uv run poe format`
- Lint: `uv run poe fix`
- Types: Fix manually, verify with `uv run poe agent-check`
- Tests: Debug locally, add retries/timeouts if flaky
- Deps: `uv add package>=version`, commit `uv.lock`

**Remember:** CI failures are feedback. Fix promptly to maintain team velocity!
