# Architecture Decision Records - Katana MCP Server

This directory contains Architecture Decision Records (ADRs) specific to the
`katana-mcp-server` package.

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

### Accepted Architecture Decisions

- [ADR-0010: Create Katana MCP Server for Claude Code Integration](0010-katana-mcp-server.md)
- [ADR-0016: Tool Interface Pattern](0016-tool-interface-pattern.md)
- [ADR-0017: Automated Tool Documentation](0017-automated-tool-documentation.md)
- [ADR-0018: SQLModel-backed Typed Cache for Transactional List Tools](0018-sqlmodel-typed-cache.md)
- [ADR-0019: MCP Tool Description and Batch-Field Conventions](0019-tool-description-batch-conventions.md)

### Proposed Architecture Decisions

- [ADR-0020: Consistent Tool Surface Across Entity Types + Cache Unification](0020-consistent-tool-surface-and-cache-unification.md)

## Creating a New ADR

1. Copy the template from the shared ADR directory:

   ```bash
   cp docs/adr/template.md katana_mcp_server/docs/adr/NNNN-your-title.md
   ```

1. Use the **next number across all three ADR directories** — the sequence is shared
   between `katana_public_api_client/docs/adr/` (client package), `docs/adr/`
   (monorepo-level), and this directory (MCP-server-specific), not per-package. Check
   the highest existing number across all three.

1. Decide which directory the ADR belongs in: client package decision →
   `katana_public_api_client/docs/adr/`; monorepo / build / process → `docs/adr/`;
   MCP-server-specific architecture → here.

1. Fill in the sections

1. Create a PR for discussion

1. After acceptance, update status to "Accepted"

## Related Documentation

- [Architecture Design](../architecture.md) - MCP architecture and patterns
- [Development Guide](../development.md) - Development workflow
- [Contributing Guide](../../../docs/CONTRIBUTING.md) - Contribution guidelines
- [Monorepo ADRs](../../../docs/adr/README.md) - Shared/monorepo-level ADRs
