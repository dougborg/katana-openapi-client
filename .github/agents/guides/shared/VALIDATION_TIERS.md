# Validation Tiers

This project uses a four-tier validation system. Choose the right tier for your workflow
stage to balance speed and thoroughness.

The canonical command + timing table lives in [CLAUDE.md](../../../../CLAUDE.md) under
"Essential Commands" — that table is what agents see on session start. This guide
explains **what each tier runs** and **why**, so you know which one to reach for and
what to expect when something fails.

## At a glance

| Tier       | Command                  | Use When                      | Adds                     |
| ---------- | ------------------------ | ----------------------------- | ------------------------ |
| **Tier 1** | `uv run poe quick-check` | During development iterations | Format-check + ruff lint |
| **Tier 2** | `uv run poe agent-check` | Before committing             | Tier 1 + type-check      |
| **Tier 3** | `uv run poe check`       | **Before opening PR**         | Tier 2 + tests + browser |
| **Tier 4** | `uv run poe full-check`  | Before requesting review      | Tier 3 + docs build      |

For current wall-clock timings (which drift as the test/lint surface grows), see the
Essential Commands table in [CLAUDE.md](../../../../CLAUDE.md). The exact compositions
are defined in `[tool.poe.tasks]` in `pyproject.toml` — that's the single source of
truth if you're trying to reason about what runs when.

## Detailed Breakdown

### Tier 1: `quick-check`

**Use during:** active development, frequent iterations.

**Runs:** `format-check` (ruff format) + `lint-ruff` (ruff check).

**Purpose:** fast feedback while coding. Catches style and obvious lint issues
immediately without waiting on type-check or tests.

**Skip if:** you're just exploring code or reading files.

______________________________________________________________________

### Tier 2: `agent-check`

**Use before:** creating commits, pushing changes.

**Runs:** Tier 1 + `typecheck` (`ty` — Astral's fast Rust-based type checker).

**Purpose:** ensure code quality before committing. Catches type errors that ruff alone
won't see.

**Note:** Tier 2 deliberately does **not** run pyright — pyright is the secondary
type-check (catches things `ty` doesn't yet, e.g., generic-invariance on `Response[T]`),
and lives in Tier 3+ via `lint`. The faster `ty`-only pass is the agent default.

______________________________________________________________________

### Tier 3: `check`

**Use before:** opening pull requests.

**Runs:** `format-check` + `lint` (ruff + ty + pyright + yamllint) + `test` (parallel
pytest) + `test-browser` (headless Chromium Prefab UI render tests).

**Purpose:** comprehensive validation that all tests pass and Prefab cards actually
render in a real browser. **REQUIRED before opening any PR.**

**First-time browser setup:** `uv run playwright install chromium` (one-time, ~250 MB).

**Critical:** tests run in parallel with 4 workers, browser tests run sequentially
(single MCP-port pair). NEVER cancel early — see "Command Timeouts" below.

______________________________________________________________________

### Tier 4: `full-check`

**Use before:** requesting PR review, final pre-merge validation.

**Runs:** Tier 3 + `docs-build` (MkDocs).

**Purpose:** complete project validation including the documentation build. Use when you
want absolute confidence — particularly if you touched docstrings, ADRs, or
mkdocstrings-driven content.

______________________________________________________________________

## Individual Commands

`pyproject.toml`'s `[tool.poe.tasks]` is the source of truth; `uv run poe help` lists
the current set. The most commonly invoked individually:

```bash
uv run poe format          # Auto-format code with ruff
uv run poe format-check    # Check formatting without modifying
uv run poe lint            # Full lint pass (ruff + ty + pyright + yamllint)
uv run poe lint-ruff       # Just ruff
uv run poe typecheck       # Just ty
uv run poe typecheck-pyright  # Just pyright
uv run poe fix             # Auto-fix lint issues (format + ruff --fix)

uv run poe test                    # Parallel tests (4 workers)
uv run poe test-sequential         # Sequential (debugging parallel issues)
uv run poe test-coverage           # With coverage
uv run poe test-unit               # Unit tests only
uv run poe test-integration        # Requires KATANA_API_KEY
uv run poe test-schema             # Schema validation tests
uv run poe test-browser            # Headless Prefab UI render tests
```

For OpenAPI / generator workflows (`regenerate-client`, `audit-spec`, etc.), see
[`katana_public_api_client/docs/spec-authoring.md`](../../../../katana_public_api_client/docs/spec-authoring.md).

For documentation tasks (`docs-build`, `docs-serve`, `docs-autobuild`), the targets are
defined in `pyproject.toml`.

______________________________________________________________________

## Command Timeouts (CRITICAL)

**NEVER CANCEL** long-running commands — they may appear to hang but are processing.
Generous timeouts prevent false failures.

The slowest commands (`regenerate-client`, `docs-build`) take 2+ minutes. Leave them.

For exact current timings, see the Essential Commands table in
[CLAUDE.md](../../../../CLAUDE.md) — kept up to date as the test surface evolves.

______________________________________________________________________

## Pre-Commit Hooks

Pre-commit is configured in `.pre-commit-config.yaml` and installs both `pre-commit` and
`pre-push` hook types via `default_install_hook_types`. The hooks run ruff format + ruff
check, mdformat, yamllint, the default unit-test suite (`uv run poe test` — which
excludes `docs`, `schema_validation`, `integration`, and `browser` markers; run
`uv run poe test-browser` separately for Prefab UI render tests), and the
`block-push-to-main` guard.

**Worktrees:** re-run `uv run pre-commit install` after `git worktree add` — pre-commit
hooks aren't shared across worktrees. The `pre-push-guard.sh` that blocks unintended
pushes to `main` only fires when the hook is installed in the worktree's `.git/hooks/`.

______________________________________________________________________

## Workflow Recommendations

The session-default workflow:

1. **Make changes** → no validation.
1. **Iterate** → `uv run poe quick-check` (Tier 1).
1. **Commit** → run `uv run poe agent-check` explicitly (Tier 2 — adds `ty` typecheck).
   Pre-commit fires on the commit but only runs ruff format / ruff check / mdformat /
   yamllint + the default unit-test suite (no `ty` typecheck, no browser /
   schema-validation / integration tests), so it's not a substitute for Tier 2 if you've
   changed type-relevant code.
1. **Open PR** → `uv run poe check` (Tier 3) — **REQUIRED**.
1. **Request review** → `uv run poe full-check` (Tier 4) if docs changed.

CI runs Tier 3+ on every PR (format check, lint, type check, full test suite, security
scans). Don't rely solely on CI — the local Tier 3 catches issues earlier in the loop.

______________________________________________________________________

## Troubleshooting

### Tests fail locally but pass in CI

- Ensure you're using a supported Python version — `pyproject.toml` declares which.
- Run `uv sync --all-extras` to refresh dependencies.
- Check for environment-specific issues (`.env` file, API keys).

### Commands seem slow

- Normal for comprehensive validation — see the timeouts note above.
- Use lower tiers during development for faster feedback.
- Never cancel long-running commands.

### Pre-commit hook failures

- Network restrictions can cause package download timeouts.
- Run commands manually if hooks fail: `uv run poe agent-check`.
- The repo uses **local hooks** (run via `uv` with project deps) so download flakes are
  rare — see `.pre-commit-config.yaml`'s comment header for the rationale.

______________________________________________________________________

## Summary

Right tier for the right stage:

- **Tier 1** (`quick-check`) — fast development iterations
- **Tier 2** (`agent-check`) — before commits
- **Tier 3** (`check`) — **before PRs (REQUIRED)**
- **Tier 4** (`full-check`) — before reviews

This tiered approach balances development speed with code quality assurance.
