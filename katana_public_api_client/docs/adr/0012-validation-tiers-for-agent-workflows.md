# ADR-0012: Validation Tiers for Agent Workflows

## Status

Accepted

Date: 2025-10-30

## Context

AI agents working on this codebase need fast feedback loops during development, but also
need comprehensive validation before opening pull requests. The existing `check` command
(~40s) is too slow for rapid iteration but necessary for PR readiness.

Key tensions:

1. **Speed vs Thoroughness**: Full validation (format + lint + mypy + tests) takes 40+
   seconds, which is slow for "did this fix work?" checks during active development
1. **Agent Workflow Stages**: Agents have distinct workflow stages (development,
   pre-commit, PR preparation, final review) with different validation needs
1. **Command Discoverability**: Agents need clear guidance on which validation to run
   when
1. **Resource Efficiency**: Running full tests on every small change wastes CI minutes
   and agent time
1. **PR Quality Gates**: Need to enforce "full validation passed" before PR opens

Without tiered validation, agents either:

- Run slow checks constantly (wasting time)
- Run fast checks only (missing errors before PR)
- Guess which checks to run (inconsistent quality)

## Decision

We will implement **4-tier validation system** via poe tasks, with each tier optimized
for a specific workflow stage:

### Tier 1: quick-check (~5-10s)

- **When**: During active development, rapid iteration
- **Runs**: `format-check + lint-ruff` (fast linting only)
- **Command**: `uv run poe quick-check`
- **Use Case**: "Did my change break syntax/formatting?"

### Tier 2: agent-check (~10-15s)

- **When**: Before committing changes
- **Runs**: `format-check + lint-ruff + lint-mypy`
- **Command**: `uv run poe agent-check`
- **Use Case**: "Are there type errors I should fix before committing?"

### Tier 3: check (~40s)

- **When**: Before opening PR (REQUIRED)
- **Runs**: `format-check + lint + test` (full validation)
- **Command**: `uv run poe check`
- **Use Case**: "Is my PR ready to open?"

### Tier 4: full-check (~50s)

- **When**: Before requesting review
- **Runs**: `format-check + lint + test + docs-build`
- **Command**: `uv run poe full-check`
- **Use Case**: "Final validation before marking PR ready for review"

### Documentation Integration

- Add tier reference to AGENT_WORKFLOW.md (complete guide)
- Add tier summary to CLAUDE.md (Claude Code quick reference)
- Add tier details to .github/copilot-instructions.md (GitHub Copilot)
- Include in timeout reference tables

## Consequences

### Positive Consequences

- **Faster Development**: 5-10s feedback vs 40s enables rapid iteration
- **Clear Workflow**: Each stage has obvious validation command
- **Better PR Quality**: Explicit "must pass check before PR" requirement
- **Resource Efficiency**: Only run full tests when needed
- **Agent Guidance**: Reduces confusion about which command to run when
- **Parallel Work**: Multiple agents can iterate faster without CI congestion
- **Pre-commit Integration**: Tiers align with .pre-commit-config-lite.yaml vs full

### Negative Consequences

- **More Commands**: 4 validation commands instead of 1 (but with clear purpose)
- **Documentation Overhead**: Must explain tier system in multiple places
- **Potential Confusion**: New contributors need to learn tier system
- **Enforcement**: Relies on agents following guidelines (can't enforce
  programmatically)

### Neutral Consequences

- **Backward Compatible**: Existing `check` command unchanged, just contextualized
- **Optional Adoption**: Agents can still use `check` for everything if desired
- **CI Unchanged**: CI still runs full validation regardless of tier used locally

## Alternatives Considered

### Alternative 1: Single "check" Command with Flags

- **Description**: `uv run poe check --fast`, `uv run poe check --full`, etc.
- **Pros**: Single command to remember, flags provide flexibility
- **Cons**:
  - Flags are harder to remember than distinct commands
  - Harder to document clearly
  - Doesn't match poe task composition patterns
- **Why Rejected**: Distinct commands are clearer and more discoverable

### Alternative 2: Watch Mode for Continuous Validation

- **Description**: `uv run poe watch` that reruns checks on file changes
- **Pros**: Even faster feedback (no command needed)
- **Cons**:
  - Requires persistent process (problematic for agents)
  - Doesn't solve "which validation level" problem
  - Adds complexity (file watching, process management)
- **Why Rejected**: Doesn't fit agent workflow patterns, added complexity

### Alternative 3: Git Hooks for Automatic Validation

- **Description**: Pre-commit/pre-push hooks that auto-run validation
- **Pros**: Automatic, no need to remember commands
- **Cons**:
  - Already have pre-commit hooks (network issues common)
  - Can't customize per workflow stage
  - Agents may need to skip hooks sometimes
  - Enforcement without flexibility is frustrating
- **Why Rejected**: Pre-commit hooks exist but don't replace tiered workflow

### Alternative 4: Just Use Existing Commands

- **Description**: Keep only `check`, `format-check`, `lint`, `test`
- **Pros**: Simpler, fewer commands
- **Cons**:
  - Agents must manually compose workflows
  - No clear "pre-commit" vs "pre-PR" distinction
  - Slower iteration (no "quick check" option)
- **Why Rejected**: Doesn't solve the workflow stage problem

## References

- [Issue #93: infra: Create quick-check and agent-check poe tasks](https://github.com/dougborg/katana-openapi-client/issues/93)
- [PR #107: docs: update copilot-instructions.md and CLAUDE.md with uv and validation tiers](https://github.com/dougborg/katana-openapi-client/pull/107)
- [AGENT_WORKFLOW.md](../../AGENT_WORKFLOW.md) - Complete agent workflow guide
- [ADR-009: Migrate from Poetry to uv](0009-migrate-from-poetry-to-uv.md) - Package
  manager that enabled fast validation
