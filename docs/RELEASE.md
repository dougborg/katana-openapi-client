# Release Process

This repository uses [release-please](https://github.com/googleapis/release-please) in
**manifest mode** to independently version and release two packages:

1. **katana-openapi-client** - The main Python API client
1. **katana-mcp-server** - The Model Context Protocol server

Each package is released independently. release-please decides which package(s) to
bump based on **which paths a commit touches**, not on commit scope - a commit that
only touches `katana_mcp_server/` bumps only the MCP server; a commit touching the
repo root (outside `katana_mcp_server/`) bumps the client; a commit touching both
bumps both. Conventional-commit scopes (`(client)` / `(mcp)`) remain useful for
changelog readability but are no longer load-bearing for version decisions.

## How releases work

### 1. Every push to `main` updates the release PR

[`release-please.yml`](../.github/workflows/release-please.yml) is the **only**
workflow that watches pushes to `main` for release purposes. On every push it runs
[`googleapis/release-please-action`](https://github.com/googleapis/release-please-action)
against [`release-please-config.json`](../release-please-config.json) /
[`.release-please-manifest.json`](../.release-please-manifest.json) and either:

- opens or updates **one aggregated release PR** covering both packages
  (`separate-pull-requests: false`), or
- if that release PR was just merged, creates the tag(s) + a **draft** GitHub Release
  for each changed package at the merge commit.

This workflow **never pushes to `main` itself** - it only writes to the release PR
branch or creates tags/releases at a commit that already exists on `main`. There is no
job here to race with another job over who pushes next.

### 2. The release PR keeps itself internally consistent

[`release-pr-prepare.yml`](../.github/workflows/release-pr-prepare.yml) runs only on
release-please's own PR branch (matched by the `release-please--` prefix, and only for
branches in this repository - never a fork). It:

- keeps `katana_mcp_server/pyproject.toml`'s `katana-openapi-client>=X` floor equal to
  the client version proposed by the release PR, and
- re-runs `uv lock` so `uv.lock` matches the bumped versions.

If either changed, it commits directly to the release PR branch. Because this lands on
the PR branch, the fix merges **atomically** with the version bump in a single commit

- there is no follow-up commit to `main` the way the old `sync-lockfile` job worked.

### 3. Merging the release PR creates tags and draft releases

Merging release-please's PR is the only thing that actually creates a release. At that
point `release-please.yml` runs one more time, sees the merge, and creates
`client-vX.Y.Z` / `mcp-vX.Y.Z` tags plus a **draft** GitHub Release for each package
that changed.

### 4. Tags trigger publishing

[`publish.yml`](../.github/workflows/publish.yml) is the **only** workflow that builds
and ships artifacts. It triggers exclusively on `client-v*` / `mcp-v*` tag pushes -
never on a `main` push - and:

1. builds the package (`uv build`)
1. publishes it to PyPI via Trusted Publishing (OIDC, no tokens)
1. attaches the built wheel/sdist to the **still-draft** release
1. publishes the release (`gh release edit --draft=false`)

For `mcp-v*` tags, a follow-on job also builds and pushes the multi-arch Docker image
to `ghcr.io/dougborg/katana-mcp-server`.

Releases are always finalized (published) only **after** their assets are attached.
Draft releases accept asset uploads; once a release is published it becomes
[immutable](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
and permanently rejects further uploads, so building/publishing the registry package
before finalizing the release avoids ever losing an asset.

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat(client): add domain helper classes"
git commit -m "fix(mcp): correct stock level calculation"
git commit -m "feat(client)!: redesign authentication flow"
```

| Commit type                                                        | Version bump |
| ------------------------------------------------------------------ | ------------ |
| `fix:`, `perf:`                                                    | PATCH        |
| `feat:`                                                            | MINOR        |
| `feat!:` / `BREAKING CHANGE:` footer                               | MAJOR        |
| `docs:`, `chore:`, `test:`, `ci:`, `refactor:`, `style:`, `build:` | No bump      |

Which package bumps is determined by **which files the commit touches**:

- Changed files under `katana_mcp_server/`? The MCP server bumps.
- Changed files anywhere else in the tree (client code, root `pyproject.toml`, etc.)?
  The client bumps.
- Changed both? Both bump.

Scopes like `(client)`/`(mcp)` are still encouraged for changelog clarity, but no
longer decide which package releases.

## Tag format

- **Client tags**: `client-v0.81.0`, `client-v0.82.0`, etc.
- **MCP tags**: `mcp-v0.115.0`, `mcp-v0.116.0`, etc.

`include-component-in-tag: true` in `release-please-config.json` preserves this exact
format, so tag history from the previous python-semantic-release setup is continuous.

## PyPI Trusted Publishers

Both packages already have **active** PyPI Trusted Publishers configured, unchanged by
this migration:

- **katana-openapi-client**: published from the `publish-client-pypi` job in
  `publish.yml`
- **katana-mcp-server**: published from the `publish-mcp-pypi` job in `publish.yml`

Neither job declares a GitHub Environment - the existing Trusted Publisher
registrations on PyPI were made without an environment name, and the OIDC claim
includes that name, so adding one now would break publishing. Configuration: PyPI
Project Settings -> Publishing -> Trusted Publishers.

## Manual release (emergency only)

If `release-please.yml` or `publish.yml` is broken and a release must ship anyway:

```bash
# 1. Build and check the package
uv build  # or: uv build --package katana-mcp-server

# 2. Tag manually (must match the existing tag format)
git tag client-v0.82.0   # or mcp-v0.116.0
git push origin client-v0.82.0

# 3. Publish to PyPI by hand, or re-run publish.yml's steps locally with
#    twine/uv publish using a scoped API token (Trusted Publishing requires
#    the tag-triggered workflow context, so a manual push needs a fallback
#    token from PyPI).

# 4. Create the GitHub release with the built assets attached
gh release create client-v0.82.0 dist/* --title "client v0.82.0" --notes "See docs/CHANGELOG.md"
```

Only do this if the automated pipeline is broken. Prefer fixing the workflow.

## Troubleshooting

### No release PR appearing

- Check that a commit since the last release actually has a releasable type
  (`feat:`, `fix:`, `perf:`) touching a tracked path.
- Check the `release-please` job logs in `release-please.yml`'s latest run.
- release-please skips work with nothing to release - this is expected between
  releases, not a failure.

### `uv.lock` or the MCP client pin looks stale on the release PR

- Check that `release-pr-prepare.yml` actually ran and pushed a commit - it only
  triggers on `pull_request` events (`opened`, `synchronize`, `reopened`) for branches
  matching `release-please--*` in this repository.
- If release-please force-pushed the PR branch again after `release-pr-prepare.yml`
  last ran, `synchronize` re-triggers it automatically; give it a minute.

### Publish auth failures

- Verify the PyPI Trusted Publisher is still registered for `publish.yml` with **no**
  environment name (see above) - a mismatch here is the most common cause of
  `Non-user identities cannot create new projects` or `invalid-publisher` errors.
- Confirm the tag actually matches `client-v*` or `mcp-v*` - `publish.yml` does not
  trigger on anything else.

### Release stuck in draft

- Each `publish.yml` job publishes to PyPI, uploads build artifacts, and *then* runs
  `gh release edit --draft=false`. If the job failed before that last step, the draft
  release is expected to remain in draft - check the workflow run for the actual
  failure and re-run the job; `gh release upload --clobber` and `gh release edit` are
  both safe to re-run against a still-draft release.

## Branch protection interaction

`main` is protected by the "Protect Main" ruleset (required PRs, linear history,
required status checks, Copilot review). release-please satisfies the PR requirement
by construction - it always opens a PR rather than pushing directly. The
`dougborg-release-please` GitHub App's ruleset bypass (previously needed so
python-semantic-release could push release commits straight to `main`) becomes
optional under this design, needed only if the release PR should auto-merge without
review (see #429). This PR does not change the ruleset itself.

## Further reading

- [release-please documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/) - commit message
  specification
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/) - OIDC-based
  publishing
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
