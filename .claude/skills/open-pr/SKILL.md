---
name: open-pr
description: >-
  Open a PR for the current feature branch — self-review the diff, organize
  commits, push, create the PR, wait for CI and review, then address feedback.
  Use when implementation is complete and ready for review.
argument-hint: "[base branch]"
allowed-tools:
  - Bash(gh pr *)
  - Bash(gh api *)
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git branch *)
  - Bash(git stash *)
  - Bash(uv run poe check)
  - Bash(uv run poe fix)
---

# Open PR Workflow

Take the current feature branch from "implementation done" to "PR open, CI green,
first-round review addressed."

## Phase 1: Pre-flight checks

1. **Verify feature branch** — confirm we're not on `main`:

   ```bash
   git branch --show-current
   ```

   If on `main`, stop and tell the user to create a feature branch first.

1. **Determine base branch** — use `$ARGUMENTS` if provided and non-empty, otherwise
   default to `main`.

1. **Run validation**:

   ```bash
   uv run poe check
   ```

   This runs format + lint + type-check + tests. **ALL must pass.** If validation fails:

   - Run `uv run poe fix` for auto-fixable lint/format issues
   - Fix remaining issues manually
   - Re-run `uv run poe check` until clean

1. **Check for existing PR** on this branch:

   ```bash
   gh pr view --json number,url,state
   ```

   If a PR already exists and is open, tell the user and stop — use `/review-pr`
   instead.

## Phase 2: Self-review

Review **every change** that will be in the PR. Get the full diff:

```bash
git diff <base>...HEAD
```

Also check uncommitted changes:

```bash
git diff
git diff --cached
```

Review every change for:

- **Bugs, logic errors, edge cases** — incorrect conditions, off-by-one, missing null
  checks
- **Generated file edits** — ensure no manual changes to `api/**/*.py`,
  `models/**/*.py`, `client.py`
- **Anti-patterns from CLAUDE.md** — UNSET misuse, manual status checks, retry wrapping
- **Missing error handling** — unhandled exceptions, missing fallbacks
- **Code quality / style** — naming, structure, consistency with codebase patterns
- **Security concerns** — secrets in code, injection vulnerabilities
- **Missing or inadequate tests** — new code paths without test coverage
- **Leftover debug code** — `print()`, `TODO`/`FIXME` without issue refs, commented-out
  code

Fix any issues found. After fixes, re-run validation:

```bash
uv run poe check
```

## Phase 3: Organize commits

1. **Review current state**:

   ```bash
   git log <base>..HEAD --oneline
   git status
   git diff
   ```

1. **Decide on commit organization**:

   - If all changes are uncommitted: group into logical commits (e.g., separate feature
     code from tests, separate refactoring from new functionality)
   - If commits already exist and are well-organized: just commit any remaining
     uncommitted changes
   - If commits exist but are messy (fixup commits, WIP): consider interactive cleanup

1. **Stage specific files per commit** — never use `git add -A` or `git add .`

1. **Commit format** — use conventional commits with scope and trailer:

   ```bash
   git commit -m "$(cat <<'EOF'
   feat(client): short description

   Optional longer explanation of the change.

   Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```

   Valid scopes: `client`, `mcp`, or no scope for cross-cutting changes.

## Phase 4: Push and open PR

1. **Push the branch**:

   ```bash
   git push -u origin <branch>
   ```

1. **Craft PR title and body**:

   - Title: conventional format, under 70 chars (e.g.,
     `feat(client): add batch stock endpoint`)
   - Body format using HEREDOC:

   ```bash
   gh pr create --base <base> --title "feat(scope): short description" --body "$(cat <<'EOF'
   ## Summary
   - Bullet points describing what this PR does

   ## Test plan
   - [ ] How to verify the changes work

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

   - If there's a related GitHub issue, include `Closes #N` in the summary

1. **Print the PR URL** for the user.

## Phase 5: Wait for CI

1. **Poll CI status**:

   ```bash
   gh pr checks <number> --watch --fail-fast
   ```

   If `--watch` is not available, poll manually:

   ```bash
   gh pr checks <number>
   ```

1. **If a check fails**:

   - Fetch the failure logs:
     ```bash
     gh run view <run-id> --log-failed
     ```
   - Fix the issue (code change, lint fix, etc.)
   - Run `uv run poe check` locally
   - Commit the fix (specific files only, never `git add -A`), push, and resume waiting

1. Once all required checks pass, move on.

## Phase 6: Wait for review comments

1. **Poll for review activity** every 60 seconds, with a **15-minute timeout**:

   ```bash
   # Check for review comments
   gh api repos/{owner}/{repo}/pulls/{number}/comments --jq 'length'

   # Check for PR reviews (approve/request-changes)
   gh pr view {number} --json reviews --jq '.reviews | length'
   ```

1. **If the PR is approved** with no comments — tell the user and stop.

1. **If comments arrive** — proceed to Phase 7.

1. **If timeout (15 min) with no comments** — tell the user "CI is green, PR is open, no
   review comments yet" and stop.

## Phase 7: Address review comments

Invoke the `/review-pr` skill to handle all review comments:

```
/review-pr <number>
```

This handles: fetching comments, triaging, fixing, validating, committing, pushing, and
replying.

**Do not duplicate this workflow** — always delegate to `/review-pr`.

## Phase 8: Final summary

Print an overall summary:

- **PR URL**
- **Number of commits** on the branch
- **CI status** (all green / any failures)
- **Review comments addressed** (count, if any)
- **Current PR state** (ready for re-review, approved, etc.)

## Important Rules

- **Validate before opening** — `uv run poe check` must pass before creating the PR
- **Self-review is mandatory** — always review the full diff before opening
- **Logical commits** — organize changes into meaningful commits, not one giant squash
- **No shortcuts** — never use `--no-verify`, `noqa`, or `type: ignore`
- **Fix CI failures in-place** — don't close and re-open the PR
- **Timeout on review wait** — don't wait forever for human review (15 min max)
- **Invoke `/review-pr`** — don't duplicate the review-comment workflow; delegate to the
  existing skill
- **Stage specific files** — never use `git add -A` or `git add .`
- **HEREDOC for messages** — always pass commit messages and PR bodies via HEREDOC for
  proper formatting
- **File issues for deferred work** — if the self-review identifies issues that are out
  of scope, create GitHub issues with `gh issue create` before opening the PR. Never
  defer work without a tracking issue.
