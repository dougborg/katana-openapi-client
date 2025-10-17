# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Katana OpenAPI
Client project.

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

- [ADR-001: Use Transport-Layer Resilience Pattern](0001-transport-layer-resilience.md)
- [ADR-002: Generate Client from OpenAPI Specification](0002-openapi-code-generation.md)
- [ADR-003: Transparent Automatic Pagination](0003-transparent-pagination.md)
- [ADR-004: Defer Observability to httpx](0004-defer-observability-to-httpx.md)
- [ADR-005: Provide Both Sync and Async APIs](0005-sync-async-apis.md)
- [ADR-006: Use Utility Functions for Response Unwrapping](0006-response-unwrapping-utilities.md)

### Proposed Architecture Decisions

- [ADR-007: Generate Domain Helper Classes](0007-domain-helper-classes.md) -
  **PROPOSED**
- [ADR-008: Avoid Traditional Builder Pattern](0008-avoid-builder-pattern.md) -
  **PROPOSED**
- [ADR-009: Migrate from Poetry to uv Package Manager](0009-migrate-from-poetry-to-uv.md)
  \- **PROPOSED**

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

- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - Test coverage analysis and testing strategy
- [KATANA_CLIENT_GUIDE.md](../KATANA_CLIENT_GUIDE.md) - User guide for the client
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [README.md](../../README.md) - Project overview and quick start
