# CLAUDE.md

Guidance for Claude Code working with this repository.

## Quick Start

```bash
uv sync --all-extras                # Install dependencies
uv run pre-commit install           # Setup hooks (installs both pre-commit AND pre-push)
uv run playwright install chromium  # Headless browser for Prefab UI render tests
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

**This is a living document.** When you discover a new recurring mistake, surprising API
behavior, or gotcha during development, add it here so future sessions don't repeat it.

Common mistakes to avoid:

- **Variants can have null SKUs — never assume `Variant.sku` is non-null** - Katana
  allows users to create variants without a SKU (legacy NetSuite imports are a common
  source — items that came across with a "Display Name" but no Item Name). The wire
  contract reflects this: `Variant.sku` is `str | None` in both the attrs and pydantic
  models. The bug that prompted the spec relaxation was a typed-cache sync crash —
  `get_all_variants(extend=PRODUCT_OR_MATERIAL)` nests each parent's full `variants[]`
  array, and a single null-sku sibling raised pydantic `ValidationError` during
  `Variant.from_attrs` recursion, aborting the whole sync batch and leaving the cache
  empty. Pinned by tests in `tests/test_models_pydantic.py::TestVariantNullSku` and
  `katana_mcp_server/tests/test_typed_cache_catalog.py::TestVariantPostprocess::test_sync_tolerates_null_sku_in_nested_variants`.
  **Downstream consumers must coalesce** — render with `variant.sku or ""`, score with
  `(variant.sku or "", weight)`, etc. The `KatanaVariant` domain model and the typed
  cache's `CachedVariant` table both accept null SKU; `get_by_sku` won't match these
  rows (NULL ≠ string), so they're effectively unreachable by SKU lookup but still
  surface in ID-based reads and FTS fuzzy search.

- **Editing generated files** - `api/**/*.py`, `models/**/*.py`, and `client.py` are
  generated. Run `uv run poe regenerate-client` instead of editing them directly.

- **Forgetting pydantic regeneration** - After `uv run poe regenerate-client`, always
  run `uv run poe generate-pydantic` too. They must stay in sync.

- **uv.lock drift during pre-commit** - When `uv.lock` shows up modified but you didn't
  touch dependencies (e.g., a sibling-package release on `main` bumped a workspace
  version), `git add uv.lock` and bundle it into your current commit. Don't
  `git checkout -- uv.lock` to drop it: pre-commit's auto-stash/restore fights with the
  lockfile being regenerated mid-hook (pytest's `uv run` re-syncs it), producing
  confusing "files were modified by this hook" failures where nothing was actually wrong
  with the staged content. The lockfile must stay in sync with `pyproject.toml` at every
  commit anyway, so bundling is always the right call.

- **Generator/schema edits without committing the regen** - Whenever you edit a
  generator script (`scripts/generate_pydantic_models.py`,
  `scripts/regenerate_client.py`) **or** the OpenAPI spec (`docs/katana-openapi.yaml`),
  run the regen, run `uv run poe check` (or at minimum `agent-check` +
  `uv run poe test`), and commit the regenerated output **in the same PR**. The input
  and its output stay locked together at every commit so the cause-and-effect chain is
  reviewable. Pushing a generator/spec change without its regen leaves CI
  green-but-stale until the next time someone runs the generator; pushing regen output
  without the input change drifts in the other direction. Note the generated-file impact
  in the PR description (e.g., "byte-identical except X" or list affected files). When
  the regen drops a previously-public class (e.g., a `StrEnum` deduped into a sibling)
  or narrows a field's type, the commit must use the breaking-change marker
  (`feat(client)!:` / `fix(client)!:`) with a `BREAKING CHANGE:` footer naming the
  affected symbol — see
  [`.github/agents/guides/shared/COMMIT_STANDARDS.md`](.github/agents/guides/shared/COMMIT_STANDARDS.md)
  "Schema and Generator Changes" for the full rule. Before editing the spec, audit
  upstream drift via the workflow in
  [`docs/upstream-specs/README.md`](docs/upstream-specs/README.md)
  (`poe refresh-upstream-spec` → `poe audit-spec` → `poe validate-response-examples` →
  `poe validate-examples`).

- **OpenAPI spec is 3.1 — use 3.1 conventions** - `docs/katana-openapi.yaml` declares
  `openapi: 3.1.0`. Use 3.1 features rather than 3.0 work-arounds. Specifically:
  **`$ref` siblings are legal in 3.1**, so attach property metadata (especially
  `description`) directly alongside `$ref` rather than wrapping the ref in
  `allOf: [{$ref: ...}]` (the 3.0 idiom — usually unnecessary for new edits here, though
  the spec still has a few legacy cases). Use `allOf` only for real composition
  (combining a `$ref` with additional properties), not as a description-attacher.

- **Property descriptions live at the use-site, not the schema-definition site** - When
  a property references a shared schema via `$ref`, put the property's `description` as
  a sibling of the `$ref` so the description describes the *role of this field on this
  object*. The shared schema's own `description` should describe the type/enum's general
  meaning. The two serve different audiences: schema-definition describes what the type
  *is*; use-site describes what the field's value *means in context* (e.g.,
  `ManufacturingOrder.status` references `ManufacturingOrderStatus` and adds "Current
  production status of the manufacturing order"; the schema itself just says "Status of
  a manufacturing order"). The pydantic generator only emits
  `Annotated[..., Field(description=...)]` when the description is at the use-site, so
  use-site descriptions are also what surfaces in the generated client's IDE hovertext /
  generated docs. Bare `$ref` drops the description from generated pydantic — avoid
  except when the schema's own description is enough context for every caller (rare).

- **UNSET vs None confusion** - attrs model fields that are unset use a sentinel value,
  not `None`. Use `unwrap_unset(field, default)` from
  `katana_public_api_client.domain.converters`, not `isinstance` or `hasattr` checks.

- **Manual status code checks** - Don't write `if response.status_code == 200`. Use
  `unwrap_as()`, `unwrap_data()`, or `is_success()` from
  `katana_public_api_client.utils`.

- **Wrapping API methods for retries** - Resilience (retries, rate limiting) is at the
  transport layer. All 100+ endpoints get it automatically via `KatanaClient`.

- **Raw list responses in tests** - Katana wraps ALL list responses in
  `{"data": [...]}`. Never define raw arrays in mocks.

- **Help resource drift** - `katana_mcp_server/.../resources/help.py` contains hardcoded
  tool documentation. When adding or modifying tool parameters, also update the help
  resource content to stay in sync.

- **None-to-UNSET conversion** - When building attrs API request models from optional
  fields, use `to_unset(value)` from `katana_public_api_client.domain.converters`
  instead of `value if value is not None else UNSET`.

- **Archive / deleted state — opt-in flags + derived booleans** - Katana represents
  soft-state as nullable timestamps on the wire: `archived_at` (the user-toggleable
  archive lifecycle — exposed on catalog items, inventory rows, and a few other
  archivable entities) and `deleted_at` (soft-delete, exposed on most entities including
  catalog items *and* transactional entities like POs, SOs, MOs, stock transfers, stock
  adjustments). The two are independent — an entity can be both archived and
  soft-deleted. Two MCP-side conventions surface this; keep them symmetric:

  - **Query-param flags** for opting into surfacing soft-state rows. **Default
    `False`.** Items use `include_archived` (`search_items`, catalog cache); after #472
    Phase D the canonical wiring is the typed cache's `CatalogQueries` adapter —
    `parent_archived_at` is denormalized onto `CachedVariant` at sync time (via the
    variant `attrs_postprocess` hook in `typed_cache/sync.py`) and the adapter's default
    `include_archived=False` / `include_deleted=False` filters push the
    `archived_at IS NULL` / `deleted_at IS NULL` predicates down to SQL. Transactional
    entities use `include_deleted` on `list_purchase_orders` / `list_sales_orders` /
    `list_manufacturing_orders` / `list_stock_adjustments`, filtering at the same
    typed-cache query layer.
  - **Response-side derived booleans**: every response model that exposes `archived_at`
    / `deleted_at` should also expose a convenience `is_archived` / `is_deleted` bool
    derived from `<timestamp> is not None`, saving callers from the timestamp/null
    inspection. **Note the asymmetry**: `is_archived` mirrors Katana's *write*
    convention (`update_<entity>` request bodies accept `is_archived: bool`, so
    round-tripping through `modify_<entity>` with
    `{"update_header": {"is_archived": false}}` works). `is_deleted`, by contrast, is
    *read-side only* — Katana exposes deletion through DELETE endpoints, not as a
    writable boolean on update bodies. Items expose `is_archived` on `ItemInfo` and
    `ItemDetailsResponse` as of #526.

  Don't add a new opt-in flag without the matching derived bool, and vice versa. **Known
  gaps** (filed for follow-up): `list_stock_transfers` lacks `include_deleted` parity
  (#484); `check_inventory` and the inventory reporting tools lack `include_archived`
  and the `is_archived` row field (#539); transactional response models lack the
  `is_deleted` derived bool (#540).

- **Polluting the API spec/models with cache-only fields** - The OpenAPI spec at
  `docs/katana-openapi.yaml` and the generated pydantic models in
  `katana_public_api_client/models_pydantic/_generated/*.py` reflect Katana's actual
  wire contract. **Never** add fields to the spec or inject fields into the API pydantic
  classes to satisfy cache-schema, MCP-tool, or other consumer needs. Cache schemas live
  on sibling `Cached<Name>` classes emitted by the same generator pass — the API class
  stays pure pydantic, the cache class carries `table=True`, foreign keys,
  relationships, JSON columns, and any cache-only fields. See
  `scripts/generate_pydantic_models.py::duplicate_cache_tables_as_cached_siblings` and
  `katana_mcp_server/src/katana_mcp/typed_cache/sync.py::_attrs_<entity>_to_cached` for
  the conversion pattern: attrs → API pydantic (via the registry) → cache pydantic (via
  `model_dump`/`model_validate`), with relationship fields set after construction since
  SQLModel `Relationship` descriptors don't accept input via `__init__`.

- **Fix bugs at the client/generator layer when the root cause lives there** - The
  Katana client (`katana_public_api_client`) is a published, standalone package.
  Third-party Python users hit the same bugs we hit in MCP. When a bug surfaces in
  `katana_mcp_server/.../typed_cache/sync.py`, in a foundation tool, or in a helper but
  originates in generated client code (attrs, pydantic, `from_attrs`, `Cached*`
  schemas), apply the fix to the **generator or spec** — not the consumer. Test: *"would
  a standalone client user hit this bug?"* If yes, fix it in the client. Examples:
  `Pydantic*.from_attrs` raising on `{}` from Katana → fix `from_attrs` codegen, not
  `_attrs_*_to_cached`. `Column(JSON)` failing to serialize a pydantic instance → fix
  `inject_json_columns` in `scripts/generate_pydantic_models.py`, not `sync.py`. Missing
  enum value → patch spec + regenerate, not enum-tolerant deserialization downstream.

- **List responses must use a `ListResponse` schema with `data` array property** -
  Katana wraps every GET list endpoint in `{"data": [...]}`. If the OpenAPI spec defines
  a 200 response as `type: array`, the generated parser iterates `response.json()`
  directly — when the API returns the dict wrapper, iteration yields keys (strings) and
  `Model.from_dict("data")` raises
  `ValueError: dictionary update sequence element #0 has length 1; 2 is required`.
  Always define a proper `MyListResponse` schema (`type: object`,
  `properties.data: {type: array, items: {$ref: ...}}`) and reference it from the
  operation. The only documented exception is `/user_info`, which returns a flat object,
  not wrapped.

- **Real names and emails from live API responses must never enter the repo** - When
  testing against the live Katana API and incorporating response data into the spec,
  examples, or test fixtures, replace real names/emails with generic placeholders
  (`Jane Doe`, `jane.doe@example.com`, etc.). Privacy concern — real user data from
  production accounts should not be committed.

- **Always call functions with named/keyword arguments** - Use `func(param=value)`, not
  `func(value)`, for all calls — including third-party constructors (especially
  `prefab_ui` components, which only accept keyword args), API methods, and cache
  helpers. Caught by review when positional args caused runtime errors with
  `prefab_ui.Metric`. Explicitness > brevity.

- **Never delete `.claude/worktrees/` directories or their contents** - Other agents may
  be actively working inside them; deleting destroys their in-progress context. If a
  worktree causes downstream issues (e.g., `ty` type checker scanning into it),
  **exclude the path in tool config** — never `rm -rf` the directory. Treat
  `.claude/worktrees/` as off-limits for destructive operations.

- **Cache IDs are not globally unique — never merge cross-entity maps by numeric ID
  alone** - The typed cache stores each entity type in its own table (`product`,
  `material`, `supplier`, ...), so a product with `id=42` and a material with `id=42`
  are both legal. When enriching a list of variants with parent context (or any other
  cross-entity batch fetch), keep separate per-type maps (`products`, `materials`) and
  select based on which ID the variant carries (`v.product_id` vs `v.material_id`).
  Merging into a single dict via `{**products, **materials}` mis-attaches parents on
  collision — Python dict-unpack iterates left-to-right and later keys win, so the
  material entry silently overwrites the product entry on shared IDs. The bug is
  symmetric in practice: every product variant whose ID also exists as a material ID
  looks up the material's data instead (and vice versa if you reorder the unpack).
  Caught in #542 (variant card redesign) by Copilot review; regression test pins the
  case in
  `test_items.py::test_enrich_variants_keeps_product_and_material_maps_separate`.

- **First push of a feature branch — use `HEAD:refs/heads/<name>`, not bare branch
  name** - When a local branch was created via `git checkout -b <name> origin/main`, its
  upstream is set to `origin/main`. A subsequent `git push -u origin <name>` then
  resolves to its tracked upstream and pushes the local tip **straight to `main`** —
  bypassing PR review and triggering semantic-release. This actually happened: commit
  `30f3fd86` reached main + tagged `mcp-v0.44.1` + published to PyPI before we could
  cancel the pipeline. **Always use the explicit destination ref** for first-time
  pushes:

  ```bash
  # Wrong — pushes to whatever the local branch tracks (may be main)
  git push -u origin chore/foo

  # Right — explicit destination, creates the remote branch
  git push -u origin HEAD:refs/heads/chore/foo
  ```

  A `pre-push` hook at `.pre-commit-config.yaml`'s `pre-push` stage enforces this for
  contributors who run pre-commit; do not bypass with `--no-verify`. The `Protect Main`
  ruleset has `bypass_mode: always` for the Admin role (required by semantic-release's
  PAT-based pushes); tightening that bypass is tracked in #429 (GitHub App migration).
  Until #429 lands, the local hook is the only mechanical guardrail.

- **Prefab `DataTable.rows` requires mustache `{{ key }}` for state binding, not bare
  string** - The Python pydantic field type accepts `rows: str` either way, but the JS
  renderer crashes the entire iframe with `t.some is not a function` if it sees a bare
  state-key string — it treats the string as the rows array itself, calls `.some()` on a
  string, and the React tree never mounts. Use mustache form everywhere:
  `rows="{{ items }}"`, `rows="{{ stock.by_location }}"` (dotted paths supported).
  `_assert_state_bindings_resolve` in `katana_mcp_server/tests/test_prefab_ui.py`
  enforces this on every state-bound DataTable. The browser-render harness in
  `katana_mcp_server/tests/browser/` proves cards actually render in headless Chromium —
  the prior unit-test contract (`to_json()` returns a dict with `$prefab`) was
  insufficient because the wire envelope can be "valid but unrenderable." Discovered
  while investigating #629; bit every state-bound DataTable in the repo (search,
  inventory, verification, batch_recipe, modification card). Run
  `uv run poe test-browser` to exercise the JS renderer locally; needs one-time
  `uv run playwright install chromium`.

- **MCP tool stubs in browser tests must mirror production wire shape via
  `make_tool_result`** - When stubbing an MCP tool in
  `katana_mcp_server/tests/browser/render_test_server.py`, return
  `make_tool_result(response_pydantic, ui=ui_card)` exactly like real tool code in
  `katana_mcp_server/src/katana_mcp/tools/foundation/`. A hand-built
  `ToolResult(content="ok", structured_content=raw_dict)` silently passes browser tests
  but misses production-shape bugs: in particular, `$result` in the on_success Rx
  context resolves to the apply tool's `structured_content` (a PrefabApp wire envelope
  keyed by `$prefab` / `view` / `state` — **not** the raw `ModificationResponse` shape,
  so it has no `actions` field), not to the pydantic response model the stub might
  construct directly. A stub with the wrong-but-convenient shape gives false green: it
  looks like the apply rail's `Rx("$result.actions")` resolves correctly when in
  production it does not. Discovered via Copilot review on #634; the broken live-tick
  that "passed" against the bad stub is tracked for proper fix in #645. Rule: **a stub
  that doesn't match production wire shape is worse than no stub.**

- **A tool's docstring promises must match the UI it actually emits** -
  `register_preview_tool` auto-appends "Preview→apply: ... returns a Prefab card with
  Confirm/Cancel buttons" to the tool's docstring. Hosts (Claude Desktop, Cowork) read
  that promise and look for a widget. If the tool was registered with
  `register_preview_tool` but **without** `meta=UI_META` (or it returns via
  `make_simple_result` with no Prefab envelope), the host's widget-fetch fails — Claude
  Desktop crashes its internal `read_widget_context` with `tool_name=undefined` because
  no widget exists for the tool the host believed was emitting one. The actual tool
  result still returns successfully, but the iframe renders nothing. Rule: every
  `register_preview_tool` call must pair `meta=UI_META` with a real Prefab card (built
  via `make_tool_result(response, ui=...)`) — never the docstring without the card.
  Conversely, tools that emit no UI must use plain `mcp.tool(...)`, not
  `register_preview_tool`. Caught via a live Claude Desktop session against
  `create_stock_adjustment` (fixed in #649); the same misregistration still applies to
  `create_stock_transfer` — tracked in #639. (`fulfill_order` is correctly wired with
  `meta=UI_META`; its remaining work is the direct-apply rail migration in #638, not
  this misregistration.)

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

## API Response Handling Best Practices

Use the helper utilities in `katana_public_api_client/utils.py` for consistent response
handling:

### Response Unwrapping

```python
from katana_public_api_client.utils import unwrap, unwrap_as, unwrap_data, is_success
from katana_public_api_client.domain.converters import unwrap_unset

# For single-object responses (200 OK with parsed model)
order = unwrap_as(response, ManufacturingOrder)  # Type-safe with validation

# For list responses (200 OK with data array)
items = unwrap_data(response, default=[])  # Extracts .data field

# For success-only responses (201 Created, 204 No Content)
if is_success(response):
    # Handle success case

# For attrs model fields that may be UNSET
status = unwrap_unset(order.status, None)  # Returns None if UNSET
```

### When to Use Each Pattern

| Scenario            | Pattern                             | Example               |
| ------------------- | ----------------------------------- | --------------------- |
| Single object (200) | `unwrap_as(response, Type)`         | Get/update operations |
| List endpoint (200) | `unwrap_data(response, default=[])` | List operations       |
| Create (201)        | `is_success(response)`              | POST with no body     |
| Delete/action (204) | `is_success(response)`              | DELETE, fulfill       |
| attrs UNSET field   | `unwrap_unset(field, default)`      | Optional API fields   |

### Anti-Patterns to Avoid

```python
# ❌ DON'T: Manual status code checks
if response.status_code == 200:
    result = response.parsed
# ✅ DO: Use helpers
result = unwrap_as(response, ExpectedType)

# ❌ DON'T: isinstance with UNSET
if not isinstance(value, type(UNSET)):
    use(value)
# ✅ DO: Use unwrap_unset
use(unwrap_unset(value, default))

# ❌ DON'T: hasattr for attrs-defined fields
if hasattr(order, "status"):
    status = order.status
# ✅ DO: Use unwrap_unset (attrs fields always exist, may be UNSET)
status = unwrap_unset(order.status, None)
```

### Exception Hierarchy

`unwrap()` and `unwrap_as()` raise typed exceptions:

- `AuthenticationError` - 401 Unauthorized
- `ValidationError` - 422 Unprocessable Entity
- `RateLimitError` - 429 Too Many Requests
- `ServerError` - 5xx server errors
- `APIError` - Other errors (400, 403, 404, etc.)

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

## Detailed Documentation

**Discover on-demand** - read these when working on specific areas:

| Topic             | File                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| Validation tiers  | [.github/agents/guides/shared/VALIDATION_TIERS.md](.github/agents/guides/shared/VALIDATION_TIERS.md)             |
| Commit standards  | [.github/agents/guides/shared/COMMIT_STANDARDS.md](.github/agents/guides/shared/COMMIT_STANDARDS.md)             |
| File organization | [.github/agents/guides/shared/FILE_ORGANIZATION.md](.github/agents/guides/shared/FILE_ORGANIZATION.md)           |
| Architecture      | [.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md](.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md) |
| Client guide      | [katana_public_api_client/docs/guide.md](katana_public_api_client/docs/guide.md)                                 |
| MCP docs          | [katana_mcp_server/docs/README.md](katana_mcp_server/docs/README.md)                                             |
| TypeScript client | [packages/katana-client/README.md](packages/katana-client/README.md)                                             |
| ADRs              | [docs/adr/README.md](docs/adr/README.md)                                                                         |
