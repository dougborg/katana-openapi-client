# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for **shared/monorepo-level** decisions that affect the entire repository.

For package-specific ADRs, see:

- **[Client ADRs](../../katana_public_api_client/docs/adr/README.md)** - `katana-openapi-client` package decisions
- **[MCP Server ADRs](../../katana_mcp_server/docs/adr/README.md)** - `katana-mcp-server` package decisions

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

- [ADR-009: Migrate from Poetry to uv Package Manager](0009-migrate-from-poetry-to-uv.md)
- [ADR-013: Module-Local Documentation Structure](0013-module-local-documentation.md)

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

ADRs are numbered sequentially starting from 0001. The number is part of the filename to
ensure ordering.

## Related Documentation

- [Client ADRs](../../katana_public_api_client/docs/adr/README.md) - Client package ADRs
- [MCP Server ADRs](../../katana_mcp_server/docs/adr/README.md) - MCP server package ADRs
- [Contributing Guide](../CONTRIBUTING.md) - Contribution guidelines
- [README](../../README.md) - Project overview and quick start
