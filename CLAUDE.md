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

## Claude Code Commands

Project slash commands in `.claude/commands/` and skills in `.claude/skills/`:

| Command          | Purpose                                      |
| ---------------- | -------------------------------------------- |
| `/techdebt`      | Scan for tech debt and anti-patterns         |
| `/review`        | Structured code review of current branch     |
| `/write-tests`   | Write comprehensive tests for target code    |
| `/generate-docs` | Generate or update documentation             |
| `/verify`        | Skeptically validate implementation quality  |
| `/pre-commit`    | Quick pre-flight check before committing     |
| `/review-pr`     | Address PR review comments, fix, push, reply |
| `/open-pr`       | Open PR with self-review, CI wait, feedback  |

## Claude Code Agents

Sub-agents in `.claude/agents/` that can be spawned for delegated work during complex
tasks:

| Agent             | Purpose                                              |
| ----------------- | ---------------------------------------------------- |
| `spec-auditor`    | Audit local OpenAPI spec against upstream for drift  |
| `code-modernizer` | Simplify code using repo-specific patterns and rules |
| `pr-preparer`     | Validate branch readiness for pull request           |

## Detailed Documentation

**Discover on-demand** - read these when working on specific areas:

| Topic             | File                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------- |
| Agent workflows   | [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md)                                                                           |
| Validation tiers  | [.github/agents/guides/shared/VALIDATION_TIERS.md](.github/agents/guides/shared/VALIDATION_TIERS.md)             |
| Commit standards  | [.github/agents/guides/shared/COMMIT_STANDARDS.md](.github/agents/guides/shared/COMMIT_STANDARDS.md)             |
| File organization | [.github/agents/guides/shared/FILE_ORGANIZATION.md](.github/agents/guides/shared/FILE_ORGANIZATION.md)           |
| Architecture      | [.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md](.github/agents/guides/shared/ARCHITECTURE_QUICK_REF.md) |
| Client guide      | [katana_public_api_client/docs/guide.md](katana_public_api_client/docs/guide.md)                                 |
| MCP docs          | [katana_mcp_server/docs/README.md](katana_mcp_server/docs/README.md)                                             |
| TypeScript client | [packages/katana-client/README.md](packages/katana-client/README.md)                                             |
| ADRs              | [docs/adr/README.md](docs/adr/README.md)                                                                         |
