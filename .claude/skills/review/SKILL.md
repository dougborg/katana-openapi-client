---
name: review
description: >-
  Six-dimension code review of the current branch's diff against main.
  Delegates to the code-reviewer agent for the actual review and reports
  findings.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git show *)
  - Bash(uv run poe check)
---

# /review — Code Review

## PURPOSE

Full review of branch changes for correctness, security, design, and Katana conventions.

## CRITICAL

- **Read-only review** — propose fixes, don't apply them. Use `code-modernizer` agent to actively rewrite.
- **Trust the test suite** — re-run `uv run poe check` only to confirm green; don't second-guess linters.

## STANDARD PATH

### 1. Classify the change

- **Type**: feature / bug fix / refactor / spec change / config / docs
- **Risk**: low (cosmetic) / medium (new feature) / high (spec, transport, auth, breaking)
- **Affected packages**: client / mcp / typescript / cross-cutting

### 2. Delegate to the code-reviewer agent

The `code-reviewer` agent (`.claude/agents/code-reviewer.md`) covers:

- Six review dimensions (Correctness, Design, Readability, Performance, Testing, Security)
- Project-specific checklist (generated files, transport-layer resilience, UNSET, response helpers, list `data` envelope, spec/pydantic regen, help resource)
- Severity-tagged output (BLOCKING / SUGGESTION / NITPICK)

Spawn it via the `Agent` tool with `subagent_type: code-reviewer`.

### 3. Verify

```bash
uv run poe check
```

If it doesn't pass, surface the failures as `[BLOCKING]` issues.

### 4. Self-improvement

If the review reveals a pattern worth codifying (new anti-pattern, missing convention, pitfall), update `CLAUDE.md` so future work benefits.

## EDGE CASES

- **Caller impact** — for every changed function signature, run `LSP findReferences` (or `git grep`) and read each caller. Diff-only review misses ripple effects.
- **Out-of-scope findings** — recommend filing a GitHub issue; never let deferred work go untracked.

## RELATED

- `code-reviewer` agent — does the actual review
- `verifier` agent — mechanical gate (passes/fails, no design opinions)
- `pr-preparer` agent — process readiness (coverage, ADRs, help resource)
- `/open-pr` skill — runs review automatically before opening PR
