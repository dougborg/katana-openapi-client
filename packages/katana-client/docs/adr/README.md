# Architecture Decision Records - TypeScript Client

This directory contains Architecture Decision Records (ADRs) specific to the
`katana-openapi-client` TypeScript package.

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

## Index

### Accepted Architecture Decisions

- [ADR-TS-001: Composable Fetch Wrappers](0001-composable-fetch-wrappers.md) - Transport
  layer architecture using composable fetch functions
- [ADR-TS-002: Hey API Code Generation](0002-hey-api-code-generation.md) - Use
  @hey-api/openapi-ts for SDK generation
- [ADR-TS-003: Biome for Linting](0003-biome-for-linting.md) - Use Biome instead of
  ESLint

## Creating a New ADR

1. Copy an existing ADR as a template
1. Update the number (NNNN) to be the next sequential number
1. Fill in the sections
1. Create a PR for discussion
1. After acceptance, update status to "Accepted"

## Related Documentation

- [Client Guide](../guide.md) - User guide for the TypeScript client
- [Cookbook](../cookbook.md) - Common usage patterns
- [Testing Guide](../testing.md) - Testing strategy and patterns
- [Python Client ADRs](../../../katana_public_api_client/docs/adr/README.md) - Python
  client decisions
