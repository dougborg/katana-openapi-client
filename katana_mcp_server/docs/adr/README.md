# Architecture Decision Records - Katana MCP Server

This directory contains Architecture Decision Records (ADRs) specific to the `katana-mcp-server` package.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## Format

We use the format proposed by Michael Nygard in his article [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

- **Title**: A short noun phrase describing the decision
- **Status**: Proposed | Accepted | Deprecated | Superseded
- **Context**: What is the issue that we're seeing that is motivating this decision?
- **Decision**: What is the change that we're proposing and/or doing?
- **Consequences**: What becomes easier or more difficult to do because of this change?

## ADR Lifecycle

1. **Proposed**: The ADR is proposed and under discussion
2. **Accepted**: The ADR has been accepted and is being implemented
3. **Deprecated**: The ADR is no longer recommended but still in use
4. **Superseded**: The ADR has been replaced by another ADR

## Index

### Accepted Architecture Decisions

- [ADR-010: Create Katana MCP Server for Claude Code Integration](0010-katana-mcp-server.md)

## Creating a New ADR

1. Copy the template from the shared ADR directory
2. Update the number (NNNN) to be the next sequential number
3. Fill in the sections
4. Create a PR for discussion
5. After acceptance, update status to "Accepted"

## Related Documentation

- [Architecture Design](../architecture.md) - MCP architecture and patterns
- [Implementation Plan](../implementation-plan.md) - MCP v0.1.0 roadmap
- [Development Guide](../development.md) - Development workflow
- [Contributing Guide](../../../docs/CONTRIBUTING.md) - Contribution guidelines
- [Monorepo ADRs](../../../docs/adr/README.md) - Shared/monorepo-level ADRs
