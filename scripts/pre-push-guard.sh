#!/usr/bin/env bash
# Pre-push guard: refuse pushes that land non-main commits on the `main` ref.
#
# Why this exists: when a feature branch is created via
#   git checkout -b <name> origin/main
# git sets the new local branch's upstream to origin/main. A subsequent
#   git push -u origin <name>
# resolves <name> to the tracked upstream and pushes straight to main. This
# actually happened — commit 30f3fd86 reached main and triggered an unintended
# semantic-release publish before we could cancel the pipeline.
#
# pre-commit invokes this with the remote name as $1, the URL as $2, and
# `<local-ref> <local-sha> <remote-ref> <remote-sha>` lines on stdin.
#
# Bypass via --no-verify is forbidden by project policy (see CLAUDE.md). The
# right form for first-time feature-branch pushes is:
#   git push -u origin HEAD:refs/heads/<branch-name>

set -euo pipefail

EXIT_CODE=0

while read -r local_ref _local_sha remote_ref _remote_sha; do
    # Skip deletions (local_ref is empty when a remote ref is being deleted).
    [ -z "$local_ref" ] && continue

    # Only guard pushes that target main.
    case "$remote_ref" in
        refs/heads/main) ;;
        *) continue ;;
    esac

    # The local ref-name pushed to main must itself be `main`. Refuse anything else.
    case "$local_ref" in
        refs/heads/main) ;;  # ok — main → main is the legitimate path for admins
        *)
            local_short="${local_ref#refs/heads/}"
            cat >&2 <<EOF
ERROR: refusing to push '$local_short' to remote 'main'.

This is almost always git's tracked-upstream resolution biting you — the
local branch was probably created via 'git checkout -b $local_short origin/main',
so its upstream is origin/main and a bare 'git push -u origin $local_short' targets main.

The fix: use an explicit destination ref so the remote branch name matches:

    git push -u origin HEAD:refs/heads/$local_short

If you genuinely need to push to main from a non-main branch (rare), do it
through a PR. Bypassing this hook with --no-verify is forbidden by project policy
— see CLAUDE.md 'Known Pitfalls'.
EOF
            EXIT_CODE=1
            ;;
    esac
done

exit "$EXIT_CODE"
