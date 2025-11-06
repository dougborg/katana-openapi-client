# Validation Tiers

This project uses a four-tier validation system. Choose the right tier for your workflow
stage to balance speed and thoroughness.

## Quick Reference

| Tier       | Command                  | Duration | Use When                      | What It Runs               |
| ---------- | ------------------------ | -------- | ----------------------------- | -------------------------- |
| **Tier 1** | `uv run poe quick-check` | ~5-10s   | During development iterations | Format + Lint              |
| **Tier 2** | `uv run poe agent-check` | ~8-12s   | Before committing             | Format + Lint + Type check |
| **Tier 3** | `uv run poe check`       | ~30s     | **Before opening PR**         | All of Tier 2 + Tests      |
| **Tier 4** | `uv run poe full-check`  | ~40s     | Before requesting review      | All of Tier 3 + Docs       |

## Detailed Breakdown

### Tier 1: Quick Check (~5-10 seconds)

**Command:** `uv run poe quick-check`

**Use during:** Active development, frequent iterations

**Runs:**

- `ruff format` - Code formatting
- `ruff check` - Linting rules

**Purpose:** Fast feedback loop while coding. Catches style issues immediately.

**Skip if:** You're just exploring code or reading files.

______________________________________________________________________

### Tier 2: Agent Check (~8-12 seconds)

**Command:** `uv run poe agent-check`

**Use before:** Creating commits, pushing changes

**Runs:**

- Everything in Tier 1
- `mypy` - Type checking

**Purpose:** Ensure code quality before committing. Catches type errors and maintains
type safety.

**Required for:** All commits (enforced by pre-commit hooks in some configurations).

______________________________________________________________________

### Tier 3: Full Check (~30 seconds)

**Command:** `uv run poe check`

**Use before:** Opening pull requests

**Runs:**

- Everything in Tier 2
- `pytest` - Full test suite (parallel execution with pytest-xdist)

**Purpose:** Comprehensive validation that all tests pass. **REQUIRED before opening any
PR.**

**Critical:** Tests run in parallel with 4 workers (~16s). NEVER cancel early.

______________________________________________________________________

### Tier 4: Full Check with Docs (~40 seconds)

**Command:** `uv run poe full-check`

**Use before:** Requesting PR review, final pre-merge validation

**Runs:**

- Everything in Tier 3
- Documentation builds and validation

**Purpose:** Complete project validation including documentation integrity.

**Note:** This is the most thorough check. Use when you want absolute confidence.

______________________________________________________________________

## Individual Commands

If you need to run specific checks:

### Formatting

```bash
uv run poe format          # Auto-format code with ruff
```

### Linting

```bash
uv run poe lint            # Run ruff linting (11s, NEVER CANCEL)
uv run poe fix             # Auto-fix linting issues
```

### Type Checking

```bash
# Type checking is part of agent-check, no standalone command
```

### Testing

```bash
uv run poe test                    # Parallel tests (4 workers, ~16s)
uv run poe test-sequential         # Sequential tests (~25s)
uv run poe test-coverage           # Tests with coverage (~22s)
uv run poe test-unit               # Unit tests only
uv run poe test-integration        # Integration tests (requires KATANA_API_KEY)
uv run poe test-schema             # Schema validation tests
```

### Documentation

```bash
uv run poe docs-build      # Build documentation (2.5 min, NEVER CANCEL)
uv run poe docs-serve      # Serve docs locally
uv run poe docs-clean      # Clean docs artifacts
```

### OpenAPI Client

```bash
uv run poe validate-openapi           # Validate OpenAPI spec
uv run poe regenerate-client          # Regenerate client (2+ min, NEVER CANCEL)
uv run poe validate-openapi-redocly   # Validate with Redocly
```

______________________________________________________________________

## Command Timeouts (CRITICAL)

**NEVER CANCEL** these commands before their typical runtime:

| Command                        | Typical Runtime | Timeout Setting |
| ------------------------------ | --------------- | --------------- |
| `uv sync --all-extras`         | 5-10s           | 30+ minutes     |
| `uv run poe lint`              | 11s             | 15+ minutes     |
| `uv run poe test`              | 16s             | 30+ minutes     |
| `uv run poe test-coverage`     | 22s             | 45+ minutes     |
| `uv run poe check`             | 30s             | 60+ minutes     |
| `uv run poe docs-build`        | 2.5 min         | 60+ minutes     |
| `uv run poe regenerate-client` | 2+ min          | 60+ minutes     |

These commands may appear to hang but are actually processing. Generous timeouts prevent
false failures.

______________________________________________________________________

## Pre-Commit Hooks

The project uses pre-commit hooks that run validation automatically:

**Standard hook** (`.pre-commit-config.yaml`):

- Runs `quick-check` (Tier 1)
- Fast iteration for most work

**Full hook** (`.pre-commit-config-full.yaml`):

- Runs `agent-check` (Tier 2)
- More thorough validation

Switch between them:

```bash
# Standard (fast)
ln -sf .pre-commit-config.yaml .git/hooks/pre-commit

# Full (thorough)
ln -sf .pre-commit-config-full.yaml .git/hooks/pre-commit
```

______________________________________________________________________

## Workflow Recommendations

### Typical Development Cycle

1. **Make changes** → No validation
1. **Test changes** → `uv run poe quick-check` (Tier 1)
1. **Commit changes** → `uv run poe agent-check` (Tier 2, or auto via pre-commit)
1. **Open PR** → `uv run poe check` (Tier 3) ← **REQUIRED**
1. **Request review** → `uv run poe full-check` (Tier 4)

### CI/CD Pipeline

The CI pipeline runs Tier 3+ validation on all PRs:

- Format check
- Lint check
- Type check
- Full test suite
- Security scans

**Important:** Don't rely solely on CI. Run `uv run poe check` locally before pushing to
catch issues early.

______________________________________________________________________

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Ensure you're using the correct Python version (3.11, 3.12, or 3.13)
- Run `uv sync --all-extras` to update dependencies
- Check for environment-specific issues (.env file, API keys)

### Commands Seem Slow

- This is normal for comprehensive validation
- Use lower tiers during development for faster feedback
- Never cancel long-running commands (see timeouts above)

### Pre-Commit Hook Failures

- Network restrictions can cause package download timeouts
- Run commands manually if hooks fail: `uv run poe agent-check`
- Consider switching to lite pre-commit config

______________________________________________________________________

## Summary

**Remember:** Use the right tier for the right stage:

- 🏃 **Tier 1** (`quick-check`) - Fast development iterations
- 🔍 **Tier 2** (`agent-check`) - Before commits
- ✅ **Tier 3** (`check`) - **Before PRs (REQUIRED)**
- 🎯 **Tier 4** (`full-check`) - Before reviews

This tiered approach balances development speed with code quality assurance.
