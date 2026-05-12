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

# /open-pr — Open PR Workflow

## PURPOSE

Take a feature branch from "implementation done" to "PR open, CI green, review addressed."

## CRITICAL

- **Validate before opening** — `uv run poe check` must pass; never use `--no-verify`, `noqa`, or `type: ignore`.
- **Self-review the full diff** — review every change before opening, not just the latest commit.
- **Stage specific files** — never `git add -A` or `git add .`.
- **HEREDOC for messages** — commit messages and PR bodies always use HEREDOC for proper formatting.
- **Push with the safe refspec, never the bare branch name** — use `git push -u origin HEAD:refs/heads/<branch-name>`, **not** `git push -u origin <branch-name>`. The bare form resolves the destination via the local branch's *upstream*. When a feature branch is created with `git checkout -b <name> origin/main`, its upstream is `origin/main` — and `git push -u origin <name>` then pushes straight to **`main`**, not to a new remote `<name>` ref. This actually happened twice in this repo (commit 30f3fd86 and again during #436 development); the pre-push guard at `scripts/pre-push-guard.sh` exists for this reason but does not fire from worktrees that haven't installed the repo hooks via `uv run pre-commit install`. Always use the explicit-destination form. Same rule applies to subsequent pushes (`git push --force-with-lease` after a rebase).
- **Prefer `/open-pr` over manual `git push` + `gh pr create`** — never hand-roll the PR-opening flow even when the changes are small. The skill encodes the validate → self-review → push → CI-watch → review-address sequence; manual sequences skip self-review and reopen the push-refspec trap above. If the work isn't yet at a clean tip, run `/pre-commit` or `/verify` first, then `/open-pr`.
- **File issues for deferred work** — if the self-review identifies out-of-scope problems, create a tracking issue with `gh issue create` before opening the PR.
- **Delegate review-comment handling** — never duplicate `/review-pr`; invoke it.
- **Run `/review-pr` before auto-merge can land** — CI-green is not the only gate. Reviewer feedback (Copilot, human, bot) is the other half. Auto-merge fires the moment CI passes, which can race ahead of unresolved comments and silently land a PR with unaddressed findings. After opening the PR, **always** invoke `/review-pr <#>` to surface and address every unresolved comment before allowing the merge to land. Applies to small cleanup PRs too — the failure mode compounds across multi-PR epics.
- **In multi-PR epics, run `/simplify` and `/review-pr` between each PR** — after each PR in a series merges to `main`, do a cleanup pass on `main` before starting the next PR. Post-merge is the cheapest time to catch complexity accretion, drift, and review follow-ups that slipped through. Waiting until the end of the epic means the whole series carries forward whatever cruft each step introduced. Bake the pair into the plan as an explicit step between PR N and PR N+1, not a one-off step at the end. Recent epic context: applied during #342 cache-back wave and the #346 `get_*` exhaustive wave.

## STANDARD PATH

1. **If the branch is behind the chosen base branch (default `main`), run `/rebase` first** — opening a PR from a stale tip means CI runs against the old base, conflict resolution happens mid-review, and `uv.lock` drift from sibling-package releases isn't caught until pre-commit fights with you. `/rebase` handles the conflict resolution + lockfile-bundling protocol cleanly. Resolve the base from `$ARGUMENTS` (default `main`), then check freshness with `git fetch origin <base> && git log --oneline HEAD..origin/<base> | head -1` — if anything appears, rebase first. The `git fetch` is required: `origin/<base>` is a remote-tracking ref that may be stale without it, which would silently let a "behind" branch through.
2. **Pre-flight** — confirm not on `main`, run `uv run poe check`, check for existing PR (Phase 1).
3. **Self-review** — read the full diff vs base; fix issues found (Phase 2).
4. **Organize commits** — group into logical commits with conventional format (Phase 3).
5. **Push and create** — `git push -u origin HEAD:refs/heads/<branch>`, `gh pr create` with HEREDOC body (Phase 4).
6. **Wait for CI** — `gh pr checks --watch`; fix failures in-place (Phase 5).
7. **Wait for review** — poll for ≤15 min; if comments arrive, delegate to `/review-pr` (Phases 6–7).
8. **Summary** — print PR URL, commit count, CI status, review state (Phase 8).

See phase detail below.

## EDGE CASES

- **Existing open PR on this branch** — stop and tell the user to use `/review-pr` instead.
- **CI fails** — fetch logs with `gh run view --log-failed`, fix locally, push; never close + reopen.
- **15-minute review timeout** — report "CI green, no comments yet" and stop. Don't wait forever.

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

1. **Surface linked-issue board status** — after creating the PR, parse the PR body
   for GitHub closing keywords (`Closes #N` / `Fixes #N` / `Resolves #N` — the three
   forms GitHub recognizes as "linked issues") and confirm each linked issue is on
   project #5 (the Rolling Backlog). `Refs #N` is a reference, not a link, and won't
   trigger GitHub's auto-move workflow — so it's intentionally excluded from both the
   regex and the workflow expectations. The two-step check:

   ```bash
   # Find linked issues (closing keywords only — Refs/See excluded by design).
   gh pr view <number> --json body --jq '.body' \
     | grep -oiE '(close[sd]?|fixe[sd]?|resolve[sd]?) #[0-9]+' \
     | grep -oE '[0-9]+' \
     | sort -u

   # For each linked issue, fetch the project item (if any) and surface its
   # Priority + Workstream so we can see the classification at a glance.
   gh issue view <issue#> --json projectItems \
     --jq '.projectItems[]
           | select(.title=="Katana MCP — Rolling Backlog")
           | {status, priority, workstream}'
   ```

   If a linked issue is **not** on the board, add it now (it should auto-add via the
   project workflow, but the workflow has a delay or could be misconfigured):

   ```bash
   gh project item-add 5 --owner @me --url "$issue_url"
   # then set Priority + Workstream — see CLAUDE.md "Project Backlog" for the
   # field-IDs / option-IDs lookup via `gh project field-list 5 --owner @me --format json`.
   ```

   The board's "Pull request linked to issue" workflow should auto-move the linked
   issue's Status to **In Progress** once the PR opens. Confirm by re-reading the
   issue's project status after creating the PR. If Status didn't move (sometimes
   the workflow lags or doesn't fire for cross-repo references), nudge it manually
   via `gh project item-edit --field-id <Status> --single-select-option-id <In Progress>`.

   Don't gate the PR on this — board status is observability, not a release gate. But
   surface the result in the summary (Phase 8) so the user knows the board reflects
   reality.

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
- **Board state** — for each linked issue, the project #5 Status (In Progress / Done /
  not-on-board) so the user can see at a glance that the board reflects the work
  (see Phase 4 step 4).

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
