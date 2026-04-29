# CLAUDE.md

Guidance for Claude Code working with this repository.

## Quick Start

```bash
uv sync --all-extras         # Install dependencies
uv run pre-commit install    # Setup hooks
cp .env.example .env         # Add KATANA_API_KEY
```

## Essential Commands

| Command                  | Time   | When to Use              |
| ------------------------ | ------ | ------------------------ |
| `uv run poe quick-check` | ~5-10s | During development       |
| `uv run poe agent-check` | ~8-12s | Before committing        |
| `uv run poe check`       | ~30s   | **Before opening PR**    |
| `uv run poe full-check`  | ~40s   | Before requesting review |
| `uv run poe fix`         | ~5s    | Auto-fix lint issues     |
| `uv run poe test`        | ~16s   | Run tests (4 workers)    |

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
sub-agents). Provenance is tracked in `.harness-lock.json`. The
[harness-kit plugin](https://github.com/dougborg/harness-kit) is loaded — its skills
appear under the `harness-kit:` prefix and its meta-skill `/harness-kit:harness` runs
audits and updates.

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
  `/harness-kit:harness retro` to capture learnings.

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
