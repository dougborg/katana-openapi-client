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

## Architecture Overview

**Monorepo with 3 packages:**

- `katana_public_api_client/` - Python client with transport-layer resilience
- `katana_mcp_server/` - MCP server for AI assistants
- `packages/katana-client/` - TypeScript client

**Key pattern:** Resilience (retries, rate limiting, pagination) is implemented at the
httpx transport layer - ALL 76+ API endpoints get it automatically.

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
