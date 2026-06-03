# CLAUDE.md

Guidance for Claude Code working with this repository.

## Quick Start

```bash
uv sync --all-extras                # Install dependencies
uv run pre-commit install           # Setup hooks (installs both pre-commit AND pre-push)
uv run playwright install chromium  # Headless browser for Prefab UI render tests
npm --prefix packages/katana-client ci  # TS client deps (needed for regenerate-all / generate-ts)
cp .env.example .env                # Add KATANA_API_KEY
```

**Worktrees: re-run `uv run pre-commit install` after `git worktree add`** — pre-commit
hooks aren't shared across worktrees. The `pre-push-guard.sh` that blocks unintended
pushes to `main` (see `Known Pitfalls`) only fires when the hook is installed in the
worktree's `.git/hooks/`.

**For ongoing work pickup, open the
[Rolling Backlog](https://github.com/users/dougborg/projects/5) board first — it's the
canonical answer to "what should I work on?"** See `Project Backlog` below for the
Priority / Workstream conventions and the issue-status contract.

## Essential Commands

| Command                   | Time   | When to Use                          |
| ------------------------- | ------ | ------------------------------------ |
| `uv run poe quick-check`  | ~5-10s | During development                   |
| `uv run poe agent-check`  | ~8-12s | Before committing                    |
| `uv run poe check`        | ~75s   | **Before opening PR** (incl browser) |
| `uv run poe full-check`   | ~85s   | Before requesting review             |
| `uv run poe fix`          | ~5s    | Auto-fix lint issues                 |
| `uv run poe test`         | ~16s   | Run tests (4 workers, no browser)    |
| `uv run poe test-browser` | ~60s   | Headless Prefab UI render tests      |

**NEVER CANCEL** long-running commands - they may appear to hang but are processing.

## CRITICAL: Zero Tolerance for Ignoring Errors

**FIX ALL ISSUES. NO EXCEPTIONS.**

- **NO** `noqa`, `type: ignore`, exclusions, or skips
- **NO** "pre-existing issues" or "unrelated to my changes" excuses
- **NO** `--no-verify` commits
- **ASK** for help if blocked - don't work around errors

**Proper fixes:**

- Too many parameters? → Create a dataclass
- Name shadows built-in? → Rename it
- Circular import? → Use `TYPE_CHECKING` block

## Verify Your Work

Always run the appropriate validation tier before considering work complete. See the
Essential Commands table above - use `quick-check` during development, `agent-check`
before committing, and `check` before opening a PR. Don't trust that code works just
because it looks right.

## Project Backlog

**Board:** [Katana MCP — Rolling Backlog](https://github.com/users/dougborg/projects/5)
(project #5) is the durable answer to "what's next?" — not `gh issue list`. The board
classifies every open issue across four dimensions (Priority / Effort / Workstream /
Umbrella) and surfaces them in three views (List, Board, Roadmap). Every new Issue and
PR auto-adds in the **Todo** column with unset Priority/Workstream until a human
triages.

### Session-start anchor

First thing in a session: glance at the Board view. Look at the **In Progress** column
(anything already running) and the top of **Todo** (P0 and P1). If the user asks "what
should I work on?", the answer is the top of Todo. **Do not re-derive the queue from
`gh issue list` — the board is the source of truth.**

### Priority bucket definitions

| Priority         | Definition                                                                                  | Examples                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| **P0-now**       | Breaks a workflow that's already shipped; user-visible failure; should not survive the day. | #527 (every PATCH raises), #547 (browser bail-out for serial-tracked)    |
| **P1-this-week** | Real value, no acute breakage, but compounding cost if deferred.                            | #500 (timeouts), #503 (silent drop), umbrella-driven workstream advances |
| **P2-soon**      | Worth doing; not blocking; has a path.                                                      | Card sub-issues, audits, secondary umbrellas                             |
| **P3-someday**   | Backlog parking; revisit on next groom; close if stale.                                     | Dead skill ideas, infrastructure ideas without a forcing function        |

### Workstream definitions

- **Cards** — Prefab UI builders + per-entity card design (driven by #537).
- **Cache** — typed cache, FTS5, sync, cold-cache recovery (driven by #472, #473).
- **Fulfillment** — `fulfill_order` / `receive_purchase_order` / order lifecycle.
  Orthogonal to umbrellas.
- **Spec-drift** — Katana API spec misalignment, codegen issues.
- **Custom-fields** — Custom-fields vertical: spec alignment, MCP tooling, definition
  CRUD, search-endpoint coverage. Spans both client and server.
- **Harness** — `.claude/`, harness-kit integration, skills, agents.
- **Process** — backlog hygiene, docs, ADRs, retros.
- **Other** — anything that doesn't fit above; usually means the schema needs a new
  bucket.

### Status contract

- Issue → **In Progress** when a linked PR opens. Use a GitHub closing keyword in the PR
  body to create the link: **`Closes #N`** is the canonical form for this repo
  (`Fixes #N` / `Resolves #N` also work — GitHub recognizes all three as closing
  keywords). `Refs #N` and `See #N` are *references*, not links — they don't trigger the
  auto-move workflow and won't auto-close the issue on merge.
- Issue → **Done** when the linked PR merges, regardless of whether the issue itself is
  closed — issues may stay open as parents to future sub-work.
- Status moves are driven by GitHub's built-in project workflows; the auto-add-workflow
  keeps new Issues + PRs on the board so nothing slips through.

### Adding to the board manually

If the auto-add workflow misses something (rare), or to retroactively classify a
pre-board issue, use the gh CLI:

```bash
gh project item-add 5 --owner @me --url <issue-or-pr-url>
# then set Priority + Workstream via gh project item-edit --single-select-option-id
```

The field IDs / option IDs are stable;
`gh project field-list 5 --owner @me --format json` prints them.

### Grooming the board

Use **`/groom`** to surface drift between issues and project state — closed issues still
in Todo, items in Done with open issues, P3 items stale for >90 days, P0/P1 sitting idle
\>21 days, items missing Priority or Workstream. The skill reads the board, classifies
items across five heuristic categories, and asks for per-category confirmation before
applying any mutation. **Destructive mutations (closures) require a second per-issue
confirmation** — category-level approval is enough for status moves and priority shifts,
but `/groom` won't bulk-close on a single OK. Don't re-derive the priority queue from
`gh issue list` — `/groom` evolves the board forward.

## Continuous Improvement

This file is meant to evolve. Update it when you learn something that would help future
sessions:

- **Fix a tricky bug?** Add the root cause to Known Pitfalls.
- **Discover a new anti-pattern?** Add it to Anti-Patterns to Avoid.
- **Find a command or workflow that's missing?** Add it to Essential Commands or
  Detailed Documentation.
- **Hit a confusing API behavior?** Document it so the next session doesn't waste time
  rediscovering it.

The same applies to all project documentation - if instructions are wrong, incomplete,
or misleading, fix them as part of your current work rather than leaving them for later.

## Known Pitfalls

**This is a living document.** When you discover a recurring mistake, add it where it
fits topically — to one of the linked docs below if it's subsystem-scoped, or to the
**Cross-cutting** list here if it's genuinely repo-wide.

### Cross-cutting

- **Variants can have null SKUs — never assume `Variant.sku` (or `ServiceVariant.sku`)
  is non-null.** Katana allows variants without SKUs (legacy NetSuite imports are a
  common source). The wire contract reflects this: `Variant.sku` **and**
  `ServiceVariant.sku` are `str | None` in both the attrs and pydantic models — the
  service vertical follows the exact same contract (a null-sku service variant nested in
  a `get_all_services` response previously crashed the typed-cache sync, emptying the
  catalog so every `search_items` call failed). **Downstream consumers must coalesce** —
  render with `variant.sku or ""`, score with `(variant.sku or "", weight)`. The
  `KatanaVariant` domain model and `CachedVariant` table both accept null SKU;
  `get_by_sku` won't match these rows (NULL ≠ string), so they're effectively
  unreachable by SKU lookup but still surface in ID-based reads and FTS fuzzy search.
  Both verticals are pinned by these tests — relaxing or re-tightening any SKU field
  must keep all four green:

  - `tests/test_models_pydantic.py::TestVariantNullSku`
  - `tests/test_models_pydantic.py::TestServiceVariantNullSku`
  - `katana_mcp_server/tests/test_typed_cache_catalog.py::TestVariantPostprocess::test_sync_tolerates_null_sku_in_nested_variants`
  - `katana_mcp_server/tests/test_typed_cache_catalog.py::TestCatalogSync::test_sync_tolerates_null_sku_in_service_variants`

- **Fake time in time-based tests — NEVER read the real wall clock.** Any test whose
  assertion depends on elapsed time, a current timestamp, or an expiry/freshness window
  must fake time. Real-clock reads (`time.time()`, `time.monotonic()`, `datetime.now()`,
  `date.today()`) make tests flaky on slow/loaded CI and force tolerance bands
  (`assert 3.5 <= elapsed <= 6.5`) that paper over non-determinism instead of fixing it.
  The tells: a tolerance band, an `abs(...) < 1` slop, or a `before <= x <= after`
  bracket around two clock reads. Two faking tools, picked by *what* time you're
  controlling:

  - **Asyncio time** (`asyncio.sleep`, `loop.call_later`, timeouts) → the **`looptime`**
    pytest plugin (`@pytest.mark.looptime`). It virtualizes the loop clock so
    `asyncio.sleep(5)` advances `loop.time()` by exactly 5 with zero real delay.
  - **Wall-clock reads** (`datetime.now()`, `time.time()`) → **`time_machine`**
    (`with time_machine.travel(fixed_instant, tick=False): ...`). It freezes
    `now()`/`time.time()` while keeping the real `datetime` class, so production
    `isinstance(x, datetime)` checks and constructors still work. **Do NOT** freeze time
    by monkeypatching the `datetime` *name* of the code under test (your own module) to
    a subclass — that swaps the class out from under that module's own
    `isinstance`/constructor calls and breaks them (cost us a debugging cycle here). Use
    `time_machine` for code you own. (Shimming a *third-party* library's `datetime` is a
    different, narrower move — see the looptime exception below.)
  - **Both in one test** → prefer NOT mixing `time_machine` + `looptime`. `time_machine`
    freezes `time.time` / `datetime.now` (it does **not** touch `time.monotonic` /
    `perf_counter`, which is what `looptime` builds its virtual clock on). The risk is
    the frozen `time.time`: asyncio reads it for some absolute timeout math, so a
    process-wide freeze can interact unpredictably with `looptime`'s virtual selector.
    So for a test that needs both faked async sleep AND a faked wall-clock read, patch
    only the narrow wall-clock seam the code reads — monkeypatch the third-party
    module's `datetime`, or freeze `time.time` alone — rather than reaching for
    `time_machine`. Examples:
    `tests/test_rate_limit_retry.py::...test_http_date_retry_after_paces_end_to_end`
    (shims `httpx_retries.retry.datetime`) and
    `tests/test_rate_limit_transport.py::...test_blocks_subsequent_request_until_gate_releases`
    (freezes `time.time`).

  **The one exception**: harness code that genuinely waits on a *real external process*
  (browser-render polling, a subprocess dev-server) legitimately uses real
  `time.monotonic()` + `time.sleep()` — that's real I/O, not a logic-time assertion.
  Keep those (e.g. `katana_mcp_server/tests/browser/conftest.py::_wait_http_ok`), but
  never copy that pattern into a unit test.

- **Editing generated files** — `api/**/*.py`, `models/**/*.py`, `client.py`,
  `models_pydantic/_generated/**`, and `models_pydantic/_auto_registry.py` are
  generated. Other modules in `models_pydantic/` (e.g. `_base.py`, `_mapped_shim.py`,
  `_pydantic_json.py`, `_registry.py`, `converters.py`) are hand-maintained. The
  **TypeScript** client's `packages/katana-client/src/generated/**` is generated too
  (via `@hey-api/openapi-ts`). All three clients regenerate from the same
  `docs/katana-openapi.yaml`, so a spec change must regenerate **all** of them — run
  **`uv run poe regenerate-all`** (which chains `regenerate-client` +
  `generate-pydantic` + `generate-ts`) instead of editing the generated paths directly.
  The CI `generated-files` job runs `regenerate-all` and fails on any drift under
  `katana_public_api_client/` **or** `packages/katana-client/src/generated/`, so a spec
  PR that skips a client's regen is caught before merge. `generate-ts` needs the TS
  package's `node_modules` (`npm ci` in `packages/katana-client`, pinned by its
  committed `package-lock.json`).

- **Raw list responses in tests** — Katana wraps every list endpoint in
  `{"data": [...]}`. Never put raw arrays in mocks. **Two documented exceptions** return
  a *bare* JSON array on the wire (no `data` envelope): `GET /bin_locations` (verified
  live 2026-06-03, #575) and `GET /user_info`. Their generated parsers return
  `list[StorageBinResponse]` / the bare model directly, so mock those two with a
  top-level array (`[ {...} ]`), not `{"data": [...]}`.

- **Always call functions with keyword arguments** — `func(param=value)`, not
  `func(value)`, for all calls. Especially `prefab_ui` components, which only accept
  kwargs.

- **Never delete `.claude/worktrees/`** — other agents may be working inside them. If a
  worktree causes tool noise (e.g., `ty` scanning into it), exclude the path in the
  tool's config — never `rm -rf`.

- **No hand-maintained drift-prone references in docs.** Versions, endpoint counts, tool
  counts, ADR enumerations, "coming soon" callouts, and dated footers all drift the
  moment they're written. Use shields.io badges for versions, link to the ADR index
  `README.md` files instead of listing ADRs by name, link to `katana://help/tools`
  instead of enumerating tools, and link to the
  [project board](https://github.com/users/dougborg/projects/5) instead of citing issue
  numbers as roadmap markers. Full rule + reasoning lives in
  [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) "No hand-maintained drift-prone
  references". This is the second time the README has gone significantly stale (#401
  sweep → #569 sweep) — the structural fix is to remove the drift surface, not to be
  more diligent about updating it.

### Topical — load the linked doc when working in that area

Each row keys the topic and lists the most-greppable terms inside, so a `grep` of this
file for "DataTable" or "archive" or "ListResponse" lands you on the right pointer. Open
the linked doc when you're working in that subsystem; agents loading CLAUDE.md don't
need to pay for the full content of every topic.

| Area                                            | Keywords inside                                                                                                                                                                                                                                                                                                            | Where to read                                                                                                  |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Prefab UI**                                   | DataTable mustache `{{ key }}`, browser-test wire shape via `make_tool_result`, `register_preview_tool` + `meta=UI_META` contract, help resource drift                                                                                                                                                                     | [katana_mcp_server/docs/prefab/README.md](katana_mcp_server/docs/prefab/README.md)                             |
| **Typed cache**                                 | archive/deleted opt-in flags (`include_archived` / `include_deleted`), `is_archived` / `is_deleted` derived bools, cross-entity ID collisions (per-type maps), `Cached<Name>` siblings (don't pollute API spec), cross-table cache-only columns (`post_sync` backfill + `preserve_columns_on_conflict`, e.g. `service_id`) | [katana_mcp_server/docs/typed_cache/README.md](katana_mcp_server/docs/typed_cache/README.md)                   |
| **OpenAPI spec authoring**                      | OpenAPI 3.1 (`$ref` siblings legal), use-site descriptions, `ListResponse` schema for arrays, generator/spec regen lockstep + breaking-change markers, privacy (no real names/emails), fix-at-source rule, **POST creates return 200 not 201** (else `unwrap_as` raises `UnexpectedResponse` on a successful mutation)     | [katana_public_api_client/docs/spec-authoring.md](katana_public_api_client/docs/spec-authoring.md)             |
| **API response handling**                       | `unwrap_as`, `unwrap_data`, `is_success`, `unwrap_unset`, `to_unset`, transport-layer retries, exception hierarchy (`AuthenticationError`, `ValidationError`, `RateLimitError`, `ServerError`, `APIError`)                                                                                                                 | [katana_public_api_client/docs/guide.md](katana_public_api_client/docs/guide.md) — "Response Handling" section |
| **Commit / push safety**                        | first-push `HEAD:refs/heads/<name>` form, `uv.lock` drift bundling, generator regen lockstep, breaking-change marker (`feat(client)!:` + `BREAKING CHANGE:` footer)                                                                                                                                                        | [.github/agents/guides/shared/COMMIT_STANDARDS.md](.github/agents/guides/shared/COMMIT_STANDARDS.md)           |
| **Rebase before PR / before addressing review** | `git fetch origin <base> && git log HEAD..origin/<base>`, `mergeStateStatus=BEHIND` auto-merge stall                                                                                                                                                                                                                       | Enforced by `/open-pr` and `/review-pr` CRITICAL sections — no separate doc needed                             |

## Using the LSP tool

Both Python (pyright) and TypeScript (typescript-language-server) LSPs are configured
and active. **Prefer LSP operations over `Read` + `Grep` for type and call-graph
questions** — they are faster, more accurate, and cross-reference the real type system
(including third-party libraries in `.venv`).

| When you need to…                                             | Use                  |
| ------------------------------------------------------------- | -------------------- |
| Understand a symbol's type/signature/docstring                | `LSP hover`          |
| Jump to where a function/class is defined (project code)      | `LSP goToDefinition` |
| Find every caller of a function before changing its signature | `LSP findReferences` |
| List all symbols in a file (skim without reading all of it)   | `LSP documentSymbol` |
| Trace callers of a function (who calls X?)                    | `LSP incomingCalls`  |
| Trace callees of a function (what does X call?)               | `LSP outgoingCalls`  |

**Project root must match workspace root**. The pyright config lives at
`pyrightconfig.json` (relative `venvPath: "."`). CLI pyright uses it automatically
(`npx pyright` or `uv run pyright`); the langserver reads it on startup.

### LSP known limitations

- `workspaceSymbol` returns nothing in this tooling — pyright only indexes *open* files,
  and the LSP tool doesn't expose the query parameter. Use `Grep` for project-wide
  symbol search instead (e.g., `Grep "def format_md_table"`).
- `goToImplementation` is not implemented by pyright — use `goToDefinition` instead.
- `goToDefinition` on external-library imports returns "no definition found" — use
  `hover` instead, which gives you the class signature + docstring.
- If `hover` returns `Unknown` for a *project-external* import (e.g., pydantic,
  fastmcp), the langserver is stale — flag to the user that Claude Code needs a restart
  to re-read `pyrightconfig.json`. All project-internal imports should always resolve.

### Handling `<new-diagnostics>` system reminders

After each edit, the harness may surface a `<new-diagnostics>` block listing
pyright/ruff diagnostics on the file. **Treat these as real until proven otherwise** —
both pyright and ty run in CI (`uv run poe lint`), so an LSP-flagged error will likely
break the build.

The protocol when a `<new-diagnostics>` block appears:

1. **Check pyright CLI on the affected file** — `uv run pyright <path>`. Pyright CLI is
   the source of truth; the LSP can be stale (especially after generator regen,
   stash/pop, or rebase).

1. **If pyright CLI agrees**, fix it. Don't push code with pending pyright errors — CI
   will fail.

1. **If pyright CLI disagrees**, the LSP is stale. **Note it explicitly in your reply to
   the user** ("LSP shows X but pyright CLI is clean — likely stale after regen") so
   they know whether their editor needs a restart. Do NOT silently move on without
   verifying.

1. **Stale-LSP common triggers** — running `uv run poe generate-pydantic`, rebasing onto
   main, or stashing & popping. Pyright re-indexes lazily; the system reminder may show
   pre-edit state until the next save.

1. **Cross-worktree LSP bleed** — when a sub-agent is operating in a sibling git
   worktree (e.g., the repo root `/Users/dougborg/Projects/katana-openapi-client/` while
   your session lives in `.claude/worktrees/<name>/`), the pyright LSP daemon stays
   rooted at the session's *original* primary cwd and never switches when other agents
   enter sibling worktrees. The daemon's snapshot reflects one branch's files; your
   edits target another branch's files. `<new-diagnostics>` reminders then surface
   phantom errors that complain about fields / params that exist on one branch but not
   the other. Symptom: `uv run pyright <path>` from your worktree is clean while LSP
   keeps flagging mismatches across a wide swath of files you didn't touch.

   **Workaround:** trust `uv run pyright <path>` from your worktree as ground truth;
   ignore the LSP diagnostics until the sub-agent's PR lands and you rebase. Don't try
   to "fix" the phantom diagnostics — the code is correct on your branch.

   **Why this isn't fixable here:** the pyright-lsp plugin can't accept a per-call
   `projectRoot` (Anthropic
   [claude-code#32230](https://github.com/anthropics/claude-code/issues/32230), closed
   as not planned). The LSP plugin layer doesn't even receive a workspace `rootUri`
   during init for per-project config discovery
   ([#27220](https://github.com/anthropics/claude-code/issues/27220)). Subagents resolve
   to the main repo root rather than their worktree
   ([#31546](https://github.com/anthropics/claude-code/issues/31546)); session worktrees
   go inside the repo root by default
   ([#49986](https://github.com/anthropics/claude-code/issues/49986)). All four upstream
   issues are closed without fix as of this writing.

The repo's house rule (no `# type: ignore` / `# noqa`) means **a real diagnostic is
always a fix, never a suppression**. If the diagnostic is wrong (third-party stub gap),
document the rationale and use a config-level rule override in `pyrightconfig.json`
(already done for `reportIncompatibleVariableOverride` and `reportAssignmentType` — see
`sync_state.py`).

## Architecture Overview

**Monorepo with 3 packages:**

- `katana_public_api_client/` - Python client with transport-layer resilience
- `katana_mcp_server/` - MCP server for AI assistants
- `packages/katana-client/` - TypeScript client

**Key pattern:** Resilience (retries, rate limiting, pagination) is implemented at the
httpx transport layer - ALL 100+ API endpoints get it automatically.

## File Rules

| Category      | Files                                        | Action          |
| ------------- | -------------------------------------------- | --------------- |
| **EDITABLE**  | `katana_client.py`, tests/, scripts/, docs/  | Can modify      |
| **GENERATED** | `api/**/*.py`, `models/**/*.py`, `client.py` | **DO NOT EDIT** |

Regenerate client: `uv run poe regenerate-client` (2+ min)

## Commit Standards

```bash
feat(client): add feature    # Client MINOR release
fix(mcp): fix bug            # MCP PATCH release
docs: update README          # No release
```

Use `!` for breaking changes: `feat(client)!: breaking change`

## Claude Code Harness

The harness lives in `.claude/skills/` (workflows) and `.claude/agents/` (delegated
sub-agents). Provenance is tracked in `.harness-lock.json`. The project's upstream is
configured in `.claude/harness-upstream`
([dougborg/harness-kit](https://github.com/dougborg/harness-kit)) — used by
`/harness-issue` (when the plugin is installed) to file Issues / PRs against the right
repo.

**Plugin baseline:** the project tracks harness-kit at the version recorded in
`.harness-lock.json` (`sources.harness-kit.version`). The `.claude/` files were
originally seeded via `/harness bootstrap` and the two upstream-sourced agents
(`code-reviewer`, `verifier`) are intentionally locally modified with Katana-specific
content — `/harness update` knows to leave them alone.

**To enable the plugin (one-time per developer):**

```bash
/plugin marketplace add dougborg/harness-kit
/plugin install harness-kit@harness-kit
```

`.claude/settings.json` already lists `harness-kit@harness-kit` under `enabledPlugins`,
so once installed locally the plugin auto-enables for this repo. The install itself
isn't auto-bootstrapped from a clone (Claude Code doesn't install plugins on clone) —
but the enable step is shared, so contributors only need to run the two `/plugin`
commands above once.

After install, the namespaced skills (`/harness-kit:harness`,
`/harness-kit:harness-issue`, `/harness-kit:standup`, `/harness-kit:feature-spec`,
`/harness-kit:skill-writer`, etc.) become available. To pull a newer baseline into
`.claude/` after upgrading the plugin, run `/harness update`.

Project-local skills below shadow / extend the plugin's generic versions where they
exist; both are valid (use the project-local `/open-pr` for the Katana flavor; use
`harness-kit:open-pr` for a generic fallback).

### Skills (slash commands)

| Skill            | Purpose                                                |
| ---------------- | ------------------------------------------------------ |
| `/pre-commit`    | Fast pre-flight before `git commit`                    |
| `/review`        | Branch review delegating to `code-reviewer` agent      |
| `/techdebt`      | Scan for tech debt and anti-patterns (reports only)    |
| `/write-tests`   | Write tests with AAA pattern + edge-case checklist     |
| `/generate-docs` | Generate or update docstrings, ADRs, READMEs           |
| `/verify`        | Skeptical end-to-end verification                      |
| `/open-pr`       | Open PR: validate, self-review, push, wait for CI      |
| `/review-pr`     | Address PR review comments: fix, push, reply in thread |

### Agents (delegated work)

Spawn via the `Agent` tool with `subagent_type` set to the agent name.

| Agent             | Model  | Purpose                                                       |
| ----------------- | ------ | ------------------------------------------------------------- |
| `code-reviewer`   | sonnet | Six-dimension read-only review of the current diff            |
| `verifier`        | haiku  | Mechanical pre-PR gate (validation, debug code, history)      |
| `domain-advisor`  | sonnet | Read-only Q&A on Katana conventions (UNSET, unwrap, helpers)  |
| `code-modernizer` | sonnet | Actively rewrites Katana-specific anti-patterns               |
| `pr-preparer`     | haiku  | Project-specific PR readiness (coverage, ADRs, help-resource) |
| `spec-auditor`    | sonnet | Audit local OpenAPI spec vs upstream Katana API               |

Recommended PR pipeline: `code-modernizer` → `verifier` → `pr-preparer` →
`code-reviewer` → `/open-pr`.

### Automation hooks

Configured in `.claude/settings.local.json` (gitignored):

- **PostToolUse / Edit|Write|MultiEdit** — runs `uv run poe fix` silently after any
  Python file is edited. Fixes lint/format issues before Claude reads the result.
- **Stop** — when the session touched more than 3 files, prints a reminder to run
  `/harness retro` to capture learnings. (When the harness-kit plugin is installed, also
  consider `/session-retro` — see harness-kit#30 — for project-side learnings.)

## Test environment

Anything that talks to a *live* Katana tenant from test code, probes, or CI smoke tests
goes through **`make_test_client()`** in
[`katana_public_api_client/testing.py`](katana_public_api_client/testing.py) — not
`KatanaClient()` directly. The helper reads `KATANA_TEST_API_KEY` (required) and
`KATANA_TEST_BASE_URL` (optional, defaults to the prod base URL — same Katana
deployment, different tenant).

**Safety rule: no silent fallback to `KATANA_API_KEY`.** If `KATANA_TEST_API_KEY` is
unset, the helper raises `RuntimeError`. Falling back to the prod key would let a
misconfigured CI run mutate production state — exactly the failure mode the helper
exists to prevent. Tests that want graceful skipping wire the skip in the fixture, not
in the helper.

Set the env vars in `.env` (uncommented in `.env.example`). Phase 1 landed the helper,
`.env` updates, and probe-script refactors. Phase 2 added the live client suite at
[`tests/integration/`](tests/integration/) — read-only smoke tests built on
`make_test_client()`, run via `uv run poe test-integration-live`, auto-skipping when
`KATANA_TEST_API_KEY` is unset (the skip lives in the `live_client` fixture, not the
helper). See [`tests/integration/README.md`](tests/integration/README.md) for the
SDT-tagging + cleanup contract any *write* test must follow. Phase 3 added the
[`live-integration.yml`](.github/workflows/live-integration.yml) workflow (nightly +
`workflow_dispatch` + `needs-live-test`-labeled PRs; soft-fail; needs the
`KATANA_TEST_API_KEY` repo secret). Phase 4 added live MCP-server smoke tests at
[`katana_mcp_server/tests/smoke/`](katana_mcp_server/tests/smoke/) — read-only MCP tool
impls exercised through a real `Services` (client + typed cache), run via
`uv run poe test-smoke-mcp` (marker `smoke`) and a parallel `mcp-smoke` job in the
workflow. Track further progress on the
[project board](https://github.com/users/dougborg/projects/5).

## Detailed Documentation

**Discover on-demand** - read these when working on specific areas:

| Topic                  | File                                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Validation tiers       | [.github/agents/guides/shared/VALIDATION_TIERS.md](.github/agents/guides/shared/VALIDATION_TIERS.md)             |
| Commit standards       | [.github/agents/guides/shared/COMMIT_STANDARDS.md](.github/agents/guides/shared/COMMIT_STANDARDS.md)             |
| File organization      | [.github/agents/guides/shared/FILE_ORGANIZATION.md](.github/agents/guides/shared/FILE_ORGANIZATION.md)           |
| Architecture           | [.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md](.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md) |
| Client guide           | [katana_public_api_client/docs/guide.md](katana_public_api_client/docs/guide.md)                                 |
| OpenAPI spec authoring | [katana_public_api_client/docs/spec-authoring.md](katana_public_api_client/docs/spec-authoring.md)               |
| Test environment       | [katana_public_api_client/testing.py](katana_public_api_client/testing.py) (`make_test_client()`)                |
| MCP docs               | [katana_mcp_server/docs/README.md](katana_mcp_server/docs/README.md)                                             |
| Modify-pipeline timing | [katana_mcp_server/docs/LOGGING.md](katana_mcp_server/docs/LOGGING.md) — "Modify-pipeline sub-step timing"       |
| Prefab UI pitfalls     | [katana_mcp_server/docs/prefab/README.md](katana_mcp_server/docs/prefab/README.md)                               |
| Typed cache patterns   | [katana_mcp_server/docs/typed_cache/README.md](katana_mcp_server/docs/typed_cache/README.md)                     |
| TypeScript client      | [packages/katana-client/README.md](packages/katana-client/README.md)                                             |
| ADRs                   | [docs/adr/README.md](docs/adr/README.md)                                                                         |
