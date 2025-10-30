# Agent Workflow Guide

This guide provides step-by-step instructions for AI agents working on the
katana-openapi-client project. Follow these guidelines to work efficiently and safely in
parallel with other agents.

## Quick Reference

**Fast Commands:**

- `uv run poe quick-check` - Format + lint only (~5-10s) - **Use during development**
- `uv run poe agent-check` - Format + lint + mypy (~10-15s) - **Use before committing**
- `uv run poe check` - Full validation (~40s) - **Required before opening PR**
- `uv run poe full-check` - Everything including docs (~50s) - **Use before requesting
  review**

**Pre-commit Hooks:**

- `.pre-commit-config-lite.yaml` - Fast iteration (~5-10s)
- `.pre-commit-config.yaml` - Full validation (~12-15s with parallel tests)

______________________________________________________________________

## Step-by-Step Workflow

### 1. Starting Work on an Issue

#### Check for Conflicts

Before starting, ensure no other agent is working on the same code:

```bash
# Check if issue is already assigned
gh issue view <issue-number>

# Check recent PRs touching same files
gh pr list --search "is:open <keyword>"

# Look at current branch activity
git branch -r | grep feature
```

#### Create Your Branch

Use consistent naming conventions:

```bash
# Pattern: feature/{issue-number}-{short-description}
git checkout -b feature/88-agent-workflow-doc

# Alternative: agent/{agent-id}/{issue-number}-{description}
git checkout -b agent/claude-1/88-agent-workflow-doc
```

**Branch Naming Rules:**

- Use `feature/` for general work
- Use `agent/` prefix if coordinating multiple agents
- Always include issue number
- Keep description short and kebab-case
- Examples:
  - `feature/92-release-concurrency`
  - `feature/94-pytest-xdist`
  - `agent/copilot-1/95-coverage-ratchet`

#### Update Issue Status

Comment on the issue to claim it:

```bash
gh issue comment <issue-number> --body "🤖 Starting work on this issue"
```

______________________________________________________________________

### 2. Development Workflow

#### Fast Iteration Loop

During active development, use quick validation for fast feedback:

```bash
# Make changes to code
vim src/file.py

# Quick validation (5-10 seconds)
uv run poe quick-check

# If using pre-commit lite
pre-commit run --config .pre-commit-config-lite.yaml --all-files

# Continue iterating
```

**When to Use Quick Check:**

- ✅ During active coding
- ✅ Testing different approaches
- ✅ Experimenting with solutions
- ✅ Multiple iterations needed

**When NOT to Use:**

- ❌ Before committing (use agent-check)
- ❌ Before opening PR (use check)
- ❌ Before requesting review (use full-check)

#### Before Committing

Run more thorough validation:

```bash
# Agent-level validation (10-15 seconds)
uv run poe agent-check

# Or use pre-commit lite
pre-commit run --config .pre-commit-config-lite.yaml --all-files

# If all passes, commit
git add <files>
git commit -m "feat: your commit message"
```

**Commit Message Format:** Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

- `feat` - New feature (triggers release)
- `fix` - Bug fix (triggers release)
- `docs` - Documentation only
- `test` - Test changes
- `refactor` - Code refactoring
- `chore` - Maintenance tasks
- `ci` - CI/CD changes

**Scopes (for monorepo):**

- `client` - Releases katana-openapi-client
- `mcp` - Releases katana-mcp-server
- (no scope) - Releases katana-openapi-client (default)

**Examples:**

```bash
git commit -m "feat(mcp): add inventory resources"
git commit -m "fix(client): handle null values in variants"
git commit -m "docs: update AGENT_WORKFLOW.md"
git commit -m "test: add coverage for edge cases"
```

______________________________________________________________________

### 3. Before Opening a Pull Request

#### Run Full Validation

**CRITICAL:** PRs must be green with full validation. No skips, no excludes.

```bash
# Full validation (required before PR)
uv run poe check

# Or use full pre-commit
pre-commit run --all-files

# Expected time: ~40 seconds (or ~12-15s with parallel tests)
```

**What `check` does:**

1. Format check (ruff, markdown)
1. Linting (ruff, mypy, yamllint)
1. Tests (pytest with coverage, excluding slow docs tests)

**If any checks fail:**

- ❌ **DO NOT** add skips or excludes
- ❌ **DO NOT** use `--no-verify` without justification
- ✅ **FIX** the actual issue
- ✅ **ASK** for help if blocked

**Exception:** Only skip checks if:

1. You document WHY in PR description
1. You create a follow-up issue to fix properly
1. The skip is temporary and necessary

#### Push Your Branch

```bash
# Push to remote
git push -u origin feature/88-agent-workflow-doc

# If you need to force push (be careful!)
git push --force-with-lease
```

______________________________________________________________________

### 4. Opening the Pull Request

#### Use GitHub CLI

```bash
# Create PR with template
gh pr create --fill

# Or specify details
gh pr create \
  --title "feat: add agent workflow documentation" \
  --body "Closes #88

## Description
Adds comprehensive AGENT_WORKFLOW.md guide for AI agents.

## Changes
- Created AGENT_WORKFLOW.md with step-by-step workflow
- Updated CLAUDE.md to link to new guide

## Testing
- Validated all commands work
- Reviewed formatting and links"
```

#### PR Checklist

Before requesting review, ensure:

- [ ] All CI checks passing (green)
- [ ] Full validation run locally (`uv run poe check`)
- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional commits
- [ ] No test/lint skips or excludes (unless justified)
- [ ] Issue number referenced in PR (e.g., "Closes #88")

#### Request Review

```bash
# Self-assign
gh pr edit --add-assignee @me

# Add labels
gh pr edit --add-label "documentation"

# Mark ready for review (if draft)
gh pr ready
```

______________________________________________________________________

### 5. Handling Review Feedback

#### Make Changes

```bash
# Make requested changes
vim files.py

# Validate
uv run poe check

# Commit
git add .
git commit -m "fix: address review feedback"

# Push
git push
```

#### Respond to Comments

```bash
# Comment on PR
gh pr comment <pr-number> --body "✅ Updated per your feedback"

# Resolve conversations (on GitHub web UI)
```

______________________________________________________________________

### 6. Before Merge

#### Final Validation

**CRITICAL:** Before merging, run complete validation:

```bash
# Full check including docs
uv run poe full-check

# This includes:
# - Format check
# - Linting (ruff, mypy, yamllint)
# - All tests (including docs tests)
# - Coverage check

# Expected time: ~50 seconds
```

#### Ensure CI is Green

Check GitHub UI or:

```bash
gh pr checks

# Should show all checks passing
```

#### Merge

```bash
# Squash and merge (recommended)
gh pr merge --squash

# Or merge commit
gh pr merge --merge

# Or rebase (be careful!)
gh pr merge --rebase
```

______________________________________________________________________

## Validation Tiers Reference

### Quick Check (~5-10 seconds)

**Command:** `uv run poe quick-check`

**Runs:**

- Ruff format check
- Ruff linting

**Use When:**

- During active development
- Fast iteration needed
- Experimenting with code

**Skip:**

- Mypy type checking
- Tests

______________________________________________________________________

### Agent Check (~10-15 seconds)

**Command:** `uv run poe agent-check`

**Runs:**

- Ruff format check
- Ruff linting
- Mypy type checking

**Use When:**

- Before committing
- Checking type safety
- Pre-commit validation

**Skip:**

- Tests (run separately if needed)

______________________________________________________________________

### Check (~40 seconds or ~12-15s with parallel tests)

**Command:** `uv run poe check`

**Runs:**

- Format check (ruff, markdown)
- Linting (ruff, mypy, yamllint)
- Tests (pytest with coverage, excluding docs)

**Use When:**

- **Before opening PR** (required)
- Before pushing to feature branch
- Validating completeness

**This is the standard for "PR ready"**

______________________________________________________________________

### Full Check (~50 seconds)

**Command:** `uv run poe full-check`

**Runs:**

- Everything in `check`
- Documentation tests (slow)
- Complete coverage report

**Use When:**

- **Before requesting review** (recommended)
- Before merging to main
- Final validation

**This is the gold standard**

______________________________________________________________________

## Conflict Resolution

### Detecting Conflicts

#### Before Starting Work

```bash
# Check who's working on what
gh issue list --assignee @me
gh pr list --author @me

# Check file history
git log --oneline --follow <file>

# Check open PRs touching same files
gh pr list --search "is:open"
```

#### During Work

```bash
# Keep your branch updated
git fetch origin
git rebase origin/main

# Check for conflicts
git status
```

### Resolving Conflicts

#### Simple Rebase

```bash
# Update main
git checkout main
git pull

# Rebase your branch
git checkout feature/your-branch
git rebase main

# If conflicts, resolve them
# Edit conflicting files
git add <resolved-files>
git rebase --continue

# Force push (safe with --force-with-lease)
git push --force-with-lease
```

#### Complex Conflicts

If you encounter complex conflicts:

1. **Communicate in the issue:**

   ```bash
   gh issue comment <issue-number> --body "Encountered conflicts with #<other-issue>. Coordinating resolution."
   ```

1. **Check with other agent (if parallel work):**

   - Review the other PR
   - Determine which changes take precedence
   - Coordinate in issue comments

1. **If blocked:**

   - Comment on issue explaining blockage
   - Provide details on conflict
   - Wait for guidance or coordinate with other agent

______________________________________________________________________

## Common Pitfalls & Solutions

### ❌ Pitfall: Skipping Validation

**Problem:** Using `--no-verify` or skipping checks to speed up workflow

**Solution:**

- Use tiered validation (quick-check, agent-check, check)
- Only full validation required before PR
- Fast iteration OK during development

______________________________________________________________________

### ❌ Pitfall: Committing with Failures

**Problem:** Committing when tests or linting fail

**Solution:**

- Always run `uv run poe agent-check` before committing
- Fix issues, don't skip them
- If blocked, ask for help in issue comments

______________________________________________________________________

### ❌ Pitfall: Adding Test/Lint Skips

**Problem:** Adding `# type: ignore`, `# noqa`, or pytest skips to pass CI

**Solution:**

- Fix the actual issue
- Only skip if absolutely necessary AND document why in PR
- Create follow-up issue to remove skip

______________________________________________________________________

### ❌ Pitfall: Force Pushing Without Care

**Problem:** Using `git push --force` and overwriting others' work

**Solution:**

- Use `git push --force-with-lease` (safer)
- Check if anyone else is on your branch
- Communicate before force pushing shared branches

______________________________________________________________________

### ❌ Pitfall: Not Updating Branch

**Problem:** Working on stale branch, causing conflicts

**Solution:**

```bash
# Update regularly
git fetch origin
git rebase origin/main

# Or merge if preferred
git merge origin/main
```

______________________________________________________________________

### ❌ Pitfall: Unclear Commit Messages

**Problem:** Vague commits like "fix stuff" or "update code"

**Solution:**

- Follow conventional commits format
- Be specific: "fix(client): handle null variant names"
- Include context: "refactor: extract helper for variant display names"

______________________________________________________________________

## Pre-commit Hook Usage

### Lite Config (Fast Iteration)

**File:** `.pre-commit-config-lite.yaml`

**Usage:**

```bash
# Run lite hooks
pre-commit run --config .pre-commit-config-lite.yaml --all-files

# Install as default
pre-commit install --config .pre-commit-config-lite.yaml
```

**When to Use:**

- During development
- Fast feedback loop
- Experimenting

______________________________________________________________________

### Full Config (Complete Validation)

**File:** `.pre-commit-config.yaml`

**Usage:**

```bash
# Run full hooks (includes tests)
pre-commit run --all-files

# Install as default
pre-commit install
```

**When to Use:**

- Before opening PR
- Before requesting review
- Final validation

**Note:** With pytest-xdist (parallel tests), this is now ~12-15 seconds instead of ~27
seconds.

______________________________________________________________________

## Working with Multiple Agents

### Coordination Strategies

#### 1. Claim Issues Early

```bash
# As soon as you start
gh issue comment <issue-number> --body "🤖 Starting work on this issue"
```

#### 2. Communicate in Issue Comments

```bash
# Update progress
gh issue comment <issue-number> --body "✅ Completed X, working on Y"

# Signal blocks
gh issue comment <issue-number> --body "⚠️ Blocked by #<other-issue>, waiting for resolution"

# Ask for coordination
gh issue comment <issue-number> --body "📋 This may conflict with #<other-issue>. Coordinating..."
```

#### 3. Branch Naming for Clarity

Use agent-specific prefixes if multiple agents working in parallel:

```bash
# Agent 1
git checkout -b agent/claude-1/88-agent-workflow

# Agent 2
git checkout -b agent/copilot-1/89-update-instructions
```

#### 4. Check Before Starting

```bash
# See what others are working on
gh issue list --label "agent-infrastructure" --state "open"
gh pr list --label "agent-infrastructure" --state "open"

# Check recent activity on files you'll touch
git log --oneline --follow <file>
```

______________________________________________________________________

## Troubleshooting

### Tests Failing Locally

```bash
# Run tests with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/test_specific.py::test_function

# Run with coverage
uv run poe test-coverage

# Check test markers
uv run pytest --markers
```

### Linting Errors

```bash
# See all linting issues
uv run poe lint

# Auto-fix what's possible
uv run poe fix

# Check specific file
uv run ruff check path/to/file.py
```

### Type Checking Errors

```bash
# Run mypy
uv run mypy katana_public_api_client

# Check specific file
uv run mypy path/to/file.py

# See mypy config
# Check [tool.mypy] in pyproject.toml
```

### Pre-commit Hook Timeouts

If pre-commit hooks timeout (e.g., in network-restricted environments):

```bash
# Use lite config
pre-commit run --config .pre-commit-config-lite.yaml --all-files

# Or skip hooks temporarily
git commit --no-verify

# But then run full validation manually
uv run poe check
```

### Coverage Failures

```bash
# Run tests with coverage report
uv run poe test-coverage

# View HTML coverage report
open htmlcov/index.html

# Check coverage for specific files
uv run pytest --cov=katana_public_api_client --cov-report=term-missing
```

______________________________________________________________________

## Additional Resources

- **[CLAUDE.md](CLAUDE.md)** - Project overview and quick start
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - Detailed
  instructions for GitHub Copilot
- **[pyproject.toml](pyproject.toml)** - See all poe tasks and configurations
- **[GitHub Project](https://github.com/users/dougborg/projects/4)** - Automation &
  Agent Infrastructure roadmap

______________________________________________________________________

## Summary: The Golden Rules

1. ✅ **Use tiered validation** - quick-check during dev, check before PR, full-check
   before review
1. ✅ **PRs must be green** - No skips, no excludes, no failures
1. ✅ **Communicate early** - Claim issues, update progress, signal blocks
1. ✅ **Follow conventions** - Branch naming, commit messages, PR format
1. ✅ **Coordinate conflicts** - Check before starting, rebase regularly, resolve
   proactively
1. ✅ **Ask for help** - If blocked, ask in issue comments
1. ✅ **Document exceptions** - If you must skip/exclude, document why in PR

Happy coding! 🤖
