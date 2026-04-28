# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for
**shared/monorepo-level** decisions that affect the entire repository.

For package-specific ADRs, see:

- **[Client ADRs](../../katana_public_api_client/docs/adr/README.md)** -
  `katana-openapi-client` package decisions
- **[MCP Server ADRs](../../katana_mcp_server/docs/adr/README.md)** -
  `katana-mcp-server` package decisions

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important
architectural decision made along with its context and consequences.

## Format

We use the format proposed by Michael Nygard in his article
[Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

- **Title**: A short noun phrase describing the decision
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision?
- **Decision**: What is the change that we're proposing and/or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?

## ADR Lifecycle

1. **Proposed**: The ADR is proposed and under discussion
1. **Accepted**: The ADR has been accepted and is being implemented
1. **Deprecated**: The ADR is no longer recommended but still in use
1. **Superseded**: The ADR has been replaced by another ADR

## Index

### Accepted Shared/Monorepo Decisions

- [ADR-0009: Migrate from Poetry to uv Package Manager](0009-migrate-from-poetry-to-uv.md)
- [ADR-0013: Module-Local Documentation Structure](0013-module-local-documentation.md)
- [ADR-0014: GitHub Copilot Custom Agents with Three-Tier Architecture](0014-github-copilot-custom-agents.md) — **superseded** by harness-kit + `.claude/`

## Creating a New ADR

1. Copy the template:

   ```bash
   cp docs/adr/template.md docs/adr/NNNN-short-title.md
   ```

1. Update the number (NNNN) to be the next sequential number

1. Fill in the sections:

   - Title
   - Status (start with "Proposed")
   - Context (why is this decision needed?)
   - Decision (what are we doing?)
   - Consequences (what are the tradeoffs?)

1. Create a PR for discussion

1. After acceptance, update status to "Accepted"

## ADR Numbering

ADRs are numbered sequentially starting from 0001, with a **single shared sequence
across all three ADR directories**:

- `katana_public_api_client/docs/adr/` — client package decisions (0001-0008,
  0011-0012)
- `docs/adr/` — shared / monorepo-level decisions (0009, 0013-0014)
- `katana_mcp_server/docs/adr/` — MCP-server-specific decisions (0010,
  0016-0019)

The sequence interleaves across the three directories. When you write a new
ADR, take the next number across **all three** directories — don't restart per
package, and don't reuse historical numbers (0015 is a dead draft, but reusing
it would create ambiguous references). Leave gaps if needed; numbers are
monotonic.

## Related Documentation

- [Client ADRs](../../katana_public_api_client/docs/adr/README.md) - Client package ADRs
- [MCP Server ADRs](../../katana_mcp_server/docs/adr/README.md) - MCP server package
  ADRs
- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines
- [README](../../README.md) - Project overview and quick start
