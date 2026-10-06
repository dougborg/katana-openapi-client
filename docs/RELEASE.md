# Release Process

This repository uses [release-please](https://github.com/googleapis/release-please) in
**manifest mode** to independently version and release three packages:

1. **katana-openapi-client** (PyPI) - The main Python API client
1. **katana-mcp-server** (PyPI) - The Model Context Protocol server
1. **katana-openapi-client** (npm) - The TypeScript client in `packages/katana-client`

Each package is released independently. release-please decides which package(s) to bump
based on **which paths a commit touches**, not on commit scope - a commit that only
touches `katana_mcp_server/` bumps only the MCP server; one that only touches
`packages/katana-client/` bumps only the TypeScript client; a commit touching the repo
root (outside both) bumps the Python client; a commit touching several bumps each of
them. Conventional-commit scopes (`(client)` / `(mcp)` / `(ts)`) remain useful for
changelog readability but are no longer load-bearing for version decisions.

## How releases work

### 1. Every push to `main` updates the release PR

[`release-please.yml`](../.github/workflows/release-please.yml) is the **only** workflow
that watches pushes to `main` for release purposes. On every push it runs
[`googleapis/release-please-action`](https://github.com/googleapis/release-please-action)
against [`release-please-config.json`](../release-please-config.json) /
[`.release-please-manifest.json`](../.release-please-manifest.json) and either:

- opens or updates **one aggregated release PR** covering both packages
  (`separate-pull-requests: false`), or
- if that release PR was just merged, creates the tag(s) + a **draft** GitHub Release
  for each changed package at the merge commit.

The Python packages use release-please's `python` strategy (bumps `pyproject.toml`); the
TypeScript client uses the `node` strategy (bumps
`packages/katana-client/package.json`). `pnpm-lock.yaml` does not record the root
package's own version, so nothing else needs syncing for the TS bump.

The aggregated PR is titled `chore(release): release main` (the
`group-pull-request-title-pattern` uses `${branch}`), not `release <version>`. That is
deliberate: release-please's Merge plugin fills `${version}` from the *root* package's
release only, so a release PR that bumps just the MCP server or just the TypeScript
client would get a version-less title that the release step then rejects as "Bad pull
request title" and never tags (this bit the first TS release; see #1138). The
per-package versions live in the PR body's `<details>` sections and in the resulting
tags.

Release creation and release-PR preparation are separate action invocations. The first
only creates releases for merged PRs. If it created a release, the workflow creates the
exact Git refs and skips preparing another PR during that run. Otherwise, a second
invocation only updates the next release PR. This avoids scanning for a just-released
manifest version before its draft release has a Git ref, which previously replayed old
history into a spurious version bump. The sequence uses action outputs, not delays.

This workflow **never pushes to `main` itself** - it only writes to the release PR
branch or creates tags/releases at a commit that already exists on `main`. There is no
job here to race with another job over who pushes next.

### 2. The release PR keeps itself internally consistent

[`release-pr-prepare.yml`](../.github/workflows/release-pr-prepare.yml) runs only on
release-please's own PR branch (matched by the `release-please--` prefix, and only for
branches in this repository - never a fork). It:

- keeps `katana_mcp_server/pyproject.toml`'s `katana-openapi-client>=X` floor equal to
  the client version proposed by the release PR, and
- re-runs `uv lock` so `uv.lock` matches the bumped versions, and
- formats the generated client changelog with `mdformat` to satisfy CI.

If any changed, it commits directly to the release PR branch. Because this lands on the
PR branch, the fix merges **atomically** with the version bump in a single commit

- there is no follow-up commit to `main` the way the old `sync-lockfile` job worked.

### 3. Merging the release PR creates tags and draft releases

Merging release-please's PR is the only thing that actually creates a release. At that
point `release-please.yml` runs one more time, sees the merge, and creates
`client-vX.Y.Z` / `mcp-vX.Y.Z` / `ts-vX.Y.Z` tags plus a **draft** GitHub Release for
each package that changed.

GitHub does not create Git refs for draft releases. After release-please creates the
drafts, the workflow explicitly creates each tag at the action's reported commit SHA
using the GitHub App token. This triggers publishing while keeping the release mutable
for artifact uploads. An existing tag is accepted only if it points to the same commit;
the workflow never moves release tags.

### 4. Tags trigger publishing

[`publish.yml`](../.github/workflows/publish.yml) is the **only** workflow that builds
and ships artifacts. It triggers exclusively on `client-v*` / `mcp-v*` / `ts-v*` tag
pushes - never on a `main` push - and:

1. builds the package (`uv build` for the Python packages;
   `pnpm install --frozen-lockfile && pnpm run build && pnpm pack` for the TypeScript
   client)
1. publishes it to its registry via Trusted Publishing (OIDC, no tokens) - PyPI for the
   Python packages, npm for the TypeScript client (with provenance attached)
1. attaches the built wheel/sdist (or npm tarball) to the **still-draft** release
1. publishes the release (`gh release edit --draft=false`)

For `mcp-v*` tags, a follow-on job also builds and pushes the multi-arch Docker image to
`ghcr.io/dougborg/katana-mcp-server`. That image installs the client source from the
same tagged commit, so the Docker build does not depend on the separate client PyPI
publish finishing first.

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
| `feat!:` / `BREAKING CHANGE:` footer                               | MINOR\*      |
| `docs:`, `chore:`, `test:`, `ci:`, `refactor:`, `style:`, `build:` | No bump      |

\* **While both packages are pre-1.0**, a breaking change bumps the MINOR version
(`0.81.0` -> `0.82.0`), not the major. This is `"bump-minor-pre-major": true` in
`release-please-config.json`.

Without that flag, release-please's default takes the first breaking change straight to
`1.0.0` — which happened in #1006, where a narrow request-model fix proposed a `1.0.0`
release. Going 1.0 is a deliberate statement about API stability, not something a commit
footer should decide. Keep marking breaking changes honestly with `!` /
`BREAKING CHANGE:`; the changelog needs them. When you *do* want 1.0, remove the flag.

Which package bumps is determined by **which files the commit touches**:

- Changed files under `katana_mcp_server/`? The MCP server bumps.
- Changed files under `packages/katana-client/`? The TypeScript client bumps.
- Changed files anywhere else in the tree (client code, root `pyproject.toml`, etc.)?
  The Python client bumps.
- Changed several? Each affected package bumps.

release-please gives the root (`.`) package every commit unless told otherwise, so the
Python client's entry carries `exclude-paths` for `katana_mcp_server` and
`packages/katana-client` - that is what makes the rule above literally true.

Scopes like `(client)`/`(mcp)`/`(ts)` are still encouraged for changelog clarity, but no
longer decide which package releases.

## Tag format

- **Client tags**: `client-v0.81.0`, `client-v0.82.0`, etc.
- **MCP tags**: `mcp-v0.115.0`, `mcp-v0.116.0`, etc.
- **TypeScript client tags**: `ts-v0.1.0`, `ts-v0.2.0`, etc.

`include-component-in-tag: true` in `release-please-config.json` preserves this exact
format, so tag history from the previous python-semantic-release setup is continuous.

## PyPI Trusted Publishers

Both packages already have **active** PyPI Trusted Publishers configured, unchanged by
this migration:

- **katana-openapi-client**: published from the `publish-client-pypi` job in
  `publish.yml`
- **katana-mcp-server**: published from the `publish-mcp-pypi` job in `publish.yml`

Neither job declares a GitHub Environment - the existing Trusted Publisher registrations
on PyPI were made without an environment name, and the OIDC claim includes that name, so
adding one now would break publishing. Configuration: PyPI Project Settings ->
Publishing -> Trusted Publishers.

## npm Trusted Publisher (TypeScript client)

The `publish-ts-npm` job in `publish.yml` publishes `packages/katana-client` to npm as
`katana-openapi-client` with
[npm Trusted Publishing](https://docs.npmjs.com/trusted-publishers) - the OIDC exchange
is done by pnpm itself (`pnpm publish --provenance`), with no `NPM_TOKEN` anywhere. Like
the PyPI jobs, it declares **no** GitHub Environment, so the npm registration must also
leave the environment name blank.

**One-time bootstrap.** npm attaches a trusted publisher to an *existing* package, so
the package has to exist before CI can publish to it. Do **not** bootstrap by publishing
the first real release by hand - that would put an unattested, locally-built tarball on
npm while the GitHub release carries CI's differently-built one. Instead, publish the
placeholder version that `package.json` already carries on `main` (`0.0.1`, which the
release-please manifest treats as the pre-release baseline), register the workflow, and
let the first real `ts-vX.Y.Z` tag go through CI with provenance:

```bash
# 1. Locally, from a clean checkout of main (package.json version is still 0.0.1)
cd packages/katana-client
pnpm install --frozen-lockfile && pnpm run build
npm login
pnpm publish --access public --no-git-checks
npm deprecate katana-openapi-client@0.0.1 "bootstrap placeholder; use >=0.1.0"

# 2. On npmjs.com -> package -> Settings -> Trusted Publisher: GitHub Actions,
#    organization/user `dougborg`, repository `katana-openapi-client`,
#    workflow filename `publish.yml` (bare filename), environment name left
#    EMPTY, and under "Allowed actions" tick "Allow npm publish". Without that
#    box the publisher may only *stage* releases, and publish.yml's direct
#    `pnpm publish` is refused with "OIDC permission denied for this action".

# 3. Still in package Settings -> Publishing access: require 2FA *or* a trusted
#    publisher (disallow tokens), so CI is the only unattended path.
```

Every later version is published only by `publish-ts-npm`, so the npm tarball and the
GitHub release asset are always the same bytes. If a `ts-v*` tag's run already failed on
the registry step before the bootstrap was done, re-run that workflow run after step 2 -
the tag, draft release, and tarball are all still in place.

**Re-runs are safe.** npm never accepts the same version twice, so the job checks
`pnpm view katana-openapi-client@<version>` first and skips the publish step when that
version already exists (any probe failure other than `E404` stops the job rather than
being mistaken for "not published"). A re-run after a failure in a *later* step (release
asset upload, un-drafting) therefore just finishes the release instead of dying on the
registry.

## Re-running a publish with a fixed workflow

A tag push runs `publish.yml` **as of that tag's commit**, so re-running a failed tag
run re-runs the old workflow file - a bug fixed in `publish.yml` on `main` is never
picked up that way. For that case `publish.yml` has a `workflow_dispatch` recovery path:
dispatch it from `main` with the existing tag, and main's workflow runs against that
tag's commit (the tag itself is never moved). The registry/asset/un-draft steps are
idempotent, so this is safe after any partial failure:

```bash
gh workflow run publish.yml --ref main -f tag=ts-v0.1.0
```

## Manual release (emergency only)

If `release-please.yml` or `publish.yml` is broken and a release must ship anyway:

```bash
# 1. Build and check the package
uv build  # or: uv build --package katana-mcp-server

# 2. Tag manually (must match the existing tag format)
git tag client-v0.82.0   # or mcp-v0.116.0, or ts-v0.2.0 for the TypeScript client
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

- Check that a commit since the last release actually has a releasable type (`feat:`,
  `fix:`, `perf:`) touching a tracked path.
- Check the `release-please` job logs in `release-please.yml`'s latest run.
- release-please skips work with nothing to release - this is expected between releases,
  not a failure.

### `uv.lock` or the MCP client pin looks stale on the release PR

- Check that `release-pr-prepare.yml` actually ran and pushed a commit - it only
  triggers on `pull_request` events (`opened`, `synchronize`, `reopened`) for branches
  matching `release-please--*` in this repository.
- If release-please force-pushed the PR branch again after `release-pr-prepare.yml` last
  ran, `synchronize` re-triggers it automatically; give it a minute.

### Publish auth failures

- Verify the PyPI Trusted Publisher is still registered for `publish.yml` with **no**
  environment name (see above) - a mismatch here is the most common cause of
  `Non-user identities cannot create new projects` or `invalid-publisher` errors.
- Confirm the tag actually matches `client-v*`, `mcp-v*`, or `ts-v*` - `publish.yml`
  does not trigger on anything else.
- For npm (`publish-ts-npm`): a `404`/`E404` or `ENEEDAUTH` on `pnpm publish` almost
  always means the trusted publisher is not registered for this repository + workflow
  yet (or the package has never been published - see the bootstrap above). Check the
  package's Settings -> Trusted Publisher on npmjs.com.
- For npm: `E403 ... OIDC permission denied for this action` means the token was minted
  and matched a registered publisher, but that publisher is not allowed to publish
  directly - tick "Allow npm publish" under its Allowed actions (see the bootstrap).
- For npm: a successful `pnpm publish` can take a few minutes to show up in `npm view` /
  the registry document. Do not conclude the version was staged or lost until several
  minutes have passed; the first release took ~2.5 minutes to appear.

### Release stuck in draft

- If no publishing run exists, check the release workflow's **Create tags for draft
  releases** step and confirm the Git ref exists. A draft release alone cannot trigger
  the tag-based publishing workflow.
- Each `publish.yml` job publishes to PyPI, uploads build artifacts, and *then* runs
  `gh release edit --draft=false`. If the job failed before that last step, the draft
  release is expected to remain in draft - check the workflow run for the actual failure
  and re-run the job; `gh release upload --clobber` and `gh release edit` are both safe
  to re-run against a still-draft release.

## Branch protection interaction

`main` is protected by the "Protect Main" ruleset (required PRs, linear history,
required status checks, Copilot review). release-please satisfies the PR requirement by
construction - it always opens a PR rather than pushing directly. The
`dougborg-release-please` GitHub App's ruleset bypass (previously needed so
python-semantic-release could push release commits straight to `main`) becomes optional
under this design, needed only if the release PR should auto-merge without review (see
#429). This PR does not change the ruleset itself.

## Further reading

- [release-please documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/) - commit message
  specification
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/) - OIDC-based
  publishing
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
