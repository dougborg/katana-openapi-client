---
name: review-pr
description: >-
  Address PR review comments — fetch all unresolved comments, fix the issues,
  validate with `uv run poe check`, commit, push, and reply to each comment
  on GitHub. Use when asked to handle PR review feedback.
argument-hint: "[PR number]"
allowed-tools:
  - Bash(gh api *)
  - Bash(gh pr *)
  - Bash(git status)
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(git add *)
  - Bash(git commit *)
  - Bash(git push *)
  - Bash(git rebase *)
  - Bash(git stash *)
  - Bash(git fetch *)
  - Bash(git merge *)
  - Bash(uv run poe check)
  - Bash(uv run poe agent-check)
  - Bash(uv run poe fix)
---

# PR Review Comment Workflow

Address all unresolved PR review comments: fix the code, validate, commit, push, and
reply.

## Phase 1: Identify the PR

If `$ARGUMENTS` is provided and non-empty, use it as the PR number. Otherwise,
auto-detect from the current branch:

```bash
gh pr view --json number,url,title,baseRefName
```

Determine the repo owner/name:

```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

If no PR is found, tell the user and stop.

Store the PR's base branch (from `baseRefName`) — use `origin/<baseRefName>` as the
rebase/log target throughout the workflow. Do **not** assume `main`.

## Phase 1b: Check for merge conflicts and CI failures

Before reviewing comments, check if the PR is mergeable and if CI is passing:

```bash
gh pr view {number} --json mergeable,mergeStateStatus,statusCheckRollup
```

### If there are merge conflicts (`mergeable: CONFLICTING`):

1. Fetch the latest base branch and attempt a merge:
   ```bash
   git fetch origin <baseRefName>
   git merge origin/<baseRefName>
   ```
1. Resolve conflicts by reading each conflicted file, understanding both sides, and
   keeping the correct resolution (usually our branch's intent integrated with the base
   branch's changes).
1. After resolving, stage the files and continue the merge:
   ```bash
   git add <resolved files>
   git commit -m "merge: resolve conflicts with <baseRefName>"
   ```

### If CI is failing (`mergeStateStatus: not SUCCESS`):

1. Check what's failing:
   ```bash
   gh pr checks {number}
   ```
1. If it's a code issue (lint, type-check, test failure), fix it as part of Phase 4.
1. If it's an infrastructure issue (flaky CI, timeout), note it in the summary but don't
   block on it.

**Always resolve conflicts and build failures before addressing review comments** —
review comments may no longer apply after a conflict resolution.

## Phase 2: Fetch all review comments

Fetch every review comment on the PR:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
```

Also fetch review threads to check resolved status:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100) {
          nodes {
            isResolved
            comments(first: 100) {
              nodes {
                id
                databaseId
                body
                path
                line
                author { login }
              }
            }
          }
        }
      }
    }
  }
' -F owner="{owner}" -F repo="{repo}" -F number={number}
```

Present a summary table of all comments:

| #   | Status     | File:Line     | Author   | Comment (truncated)   |
| --- | ---------- | ------------- | -------- | --------------------- |
| 1   | unresolved | src/foo.py:42 | reviewer | "Consider using..."   |
| 2   | resolved   | src/bar.py:10 | reviewer | "Typo in variable..." |

Skip resolved threads — only work on **unresolved** comments.

## Phase 3: Triage each unresolved comment

For each unresolved comment:

1. **Read the affected file** and surrounding context
1. **Check if already fixed** — the code may have changed since the comment was posted
1. **Classify** the comment:
   - **fix needed** — code change required
   - **already fixed** — issue was addressed in a prior commit, just needs a reply
   - **acknowledge** — valid point but deferring, or explaining why current approach is
     correct

If a comment has prior replies, check whether the replies actually resolved the concern.
If not, treat it as still needing action.

## Phase 4: Fix all issues

Make all necessary code changes across affected files. Remember this repo's constraints:

- NEVER edit generated files (`api/**/*.py`, `models/**/*.py`, `client.py`)
- Use `unwrap_unset()`, `unwrap_as()`, `is_success()` helpers per CLAUDE.md patterns
- Resilience is at the transport layer — don't wrap API methods with retries

Then validate:

```bash
uv run poe check
```

This runs format + lint + type-check + tests. **ALL must pass.** If validation fails:

1. Run `uv run poe fix` for auto-fixable lint/format issues
1. Fix remaining issues manually
1. Re-run `uv run poe check` until clean

## Phase 5: Commit, rebase, and push

The goal is a **clean commit history** — review fixes should be folded into the commits
they logically belong to, not piled on as separate "fix review comments" commits. Don't
squash everything into one commit; preserve meaningful commit boundaries.

### Step 1: Stage and commit fixes

Stage only the files that were changed (never use `git add -A` or `git add .`):

```bash
git add <file1> <file2> ...
```

Create a temporary fixup commit:

```bash
git commit -m "$(cat <<'EOF'
fixup! <original commit subject line this fix belongs to>

- Description of fix 1
- Description of fix 2

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

If fixes span multiple original commits, create multiple fixup commits — one per target
commit.

If fixes don't clearly map to an existing commit (e.g., they address a cross-cutting
concern), create a standalone commit with a descriptive message instead.

### Step 2: Rebase to fold fixups into their target commits

```bash
git fetch origin <baseRefName>
git rebase --autosquash origin/<baseRefName>
```

This automatically reorders and squashes `fixup!` commits into their targets. After the
rebase, verify with:

```bash
git log origin/<baseRefName>..HEAD --oneline
```

The result should be a clean set of logical commits — no "fix review comments" or
"address feedback" commits.

### Step 3: Force-push the rebased branch

Since the branch is already pushed, a force-push is required after rebasing:

```bash
git push --force-with-lease
```

Use `--force-with-lease` (not `--force`) to avoid overwriting changes pushed by others.

**NEVER reply to comments before pushing.** Replies confirm the fix is live.

## Phase 6: Reply to each comment

After pushing, reply to every unresolved comment using:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  -X POST -f body='...'
```

Reply format by classification:

- **Code fix**: "Fixed — [describe what was changed]. [mention tests if added]"
- **Already fixed**: "This was already addressed in [commit hash] — [brief explanation]"
- **Acknowledged/deferred**: "Acknowledged — [reason for deferring]. Tracked in #NNN."
  (must include a GitHub issue link)

Reply to **EVERY** unresolved comment. None should be left without a response.

## Phase 7: Update PR description

After fixing review comments (especially if the scope has changed), update the PR
description to reflect the current state:

```bash
gh pr edit {number} --body "$(cat <<'EOF'
## Summary
<updated bullet points reflecting current scope>

## Test plan
<updated checklist>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Review the commit log (`git log origin/<baseRefName>..HEAD --oneline`) to ensure the
description covers all changes, not just the original PR scope.

## Phase 8: Summary

Print a final summary for the user:

- Number of comments addressed (fixed / already fixed / acknowledged)
- Files changed
- Validation result (tests, lint, type-check)
- Any comments that couldn't be addressed, with explanation

## Important Rules

- **Fix first, reply after push** — never reply before the code is pushed
- **Reply to every comment** — even if just acknowledging
- **No shortcuts** — `uv run poe check` must pass; never use `--no-verify`, `noqa`, or
  `type: ignore`
- **Be specific in replies** — describe what changed, don't just say "done"
- **Clean history via rebase** — fold review fixes into the commits they belong to using
  `fixup!` + `--autosquash`; don't pile on "fix review comments" commits, but also don't
  squash everything into one commit — preserve meaningful commit boundaries
- **Evaluate existing replies** — if a comment already has replies, check whether the
  issue was actually resolved; if not, fix it and add a new reply
- **No ignores or suppressions** — never use `noqa`, `type: ignore`, or skip tests to
  make validation pass
- **File issues for deferred work** — if a review comment identifies a valid issue that
  is out of scope or too large to fix in this PR, create a GitHub issue with
  `gh issue create` before replying. The reply MUST include the issue number. Never
  defer work without a tracking issue.
