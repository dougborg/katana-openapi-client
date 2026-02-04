______________________________________________________________________

## description: 'Break down a feature request into actionable implementation plan with phases and dependencies'

# Break Down Feature into Implementation Plan

Transform a complex feature request into an actionable, phased implementation plan with
effort estimates and dependencies.

## Instructions

1. **Understand the feature request**:

   - Read the issue description carefully
   - Identify the core requirements
   - Check for existing related work
   - Review relevant ADRs for architectural patterns

1. **Research existing patterns**:

   - Search codebase for similar implementations
   - Review `docs/adr/` for architectural guidance
   - Check existing tools/helpers for reusable patterns
   - Identify affected packages (client vs MCP server)

1. **Create 4-phase breakdown**:

   **Phase 1: Foundation** (Infrastructure & Setup)

   - Core infrastructure changes
   - Configuration updates
   - Database/API schema changes
   - ADR documentation if architectural

   **Phase 2: Core Implementation** (Primary Functionality)

   - Main feature functionality
   - Essential API endpoints or tools
   - Core business logic
   - Integration with existing systems

   **Phase 3: Enhancements** (Secondary Features)

   - Additional features
   - Helper utilities
   - Performance optimizations
   - Extended integrations

   **Phase 4: Documentation** (User-Facing Docs)

   - User documentation
   - Code examples
   - Cookbook recipes
   - README updates

1. **Estimate effort** using priority labels:

   - **p1-high**: 1-2 days (complex features, architectural changes)
   - **p2-medium**: 4-8 hours (standard features, integrations)
   - **p3-low**: 1-3 hours (small improvements, doc updates)

1. **Map dependencies**:

   - Identify blocking relationships between phases
   - Document required tools and prerequisites
   - Note cross-package dependencies
   - Flag breaking changes

1. **Assess risks**:

   - Technical risks (compatibility, performance, security)
   - Integration risks (API changes, breaking changes)
   - Timeline risks (complexity, unknowns)
   - Mitigation strategies for each

1. **Create GitHub issues** for each phase:

   ```markdown
   ## Phase 1: Foundation

   **Description**: Set up infrastructure for X feature

   **Tasks**:
   - [ ] Create domain models in `domain/`
   - [ ] Add API client methods
   - [ ] Write ADR-NNNN for architectural decision

   **Dependencies**: None

   **Effort**: p2-medium (4-8 hours)

   **Acceptance Criteria**:
   - [ ] Domain models created with Pydantic
   - [ ] API methods generated/added
   - [ ] ADR documented and reviewed
   ```

1. **Assign specialist agents**:

   - `@python-developer` - Implementation
   - `@tdd-specialist` - Testing
   - `@documentation-writer` - Documentation
   - `@code-reviewer` - Quality checks

## Planning Template

```markdown
# Implementation Plan: [Feature Name]

## Overview

[Brief description of the feature]

## Affected Components

- [ ] Client library (`katana-openapi-client`)
- [ ] MCP server (`katana-mcp-server`)
- [ ] Documentation
- [ ] Tests

## Architecture Review

**Relevant ADRs**:
- [Relevant ADRs from docs/adr/]

**Patterns to Follow**:
- [Pattern name from ADR]

## Phase Breakdown

### Phase 1: Foundation (p2-medium, 4-8 hours)

**Tasks**:
1. Create Pydantic models
2. Add API integration
3. Document architecture decision

**Dependencies**: None

**Risks**: None identified

### Phase 2: Core Implementation (p1-high, 1-2 days)

**Tasks**:
1. Implement main functionality
2. Add error handling
3. Write comprehensive tests

**Dependencies**: Phase 1 complete

**Risks**: API changes may require client regeneration

### Phase 3: Enhancements (p2-medium, 4-8 hours)

**Tasks**:
1. Add helper utilities
2. Performance optimization
3. Additional test coverage

**Dependencies**: Phase 2 complete

**Risks**: None identified

### Phase 4: Documentation (p3-low, 1-3 hours)

**Tasks**:
1. Update README
2. Add cookbook examples
3. Update API documentation

**Dependencies**: Phase 3 complete

**Risks**: None identified

## Overall Timeline

- **Total Effort**: 2-3 days
- **Phases**: 4 sequential phases
- **Team**: 1-2 developers

## Success Criteria

- [ ] All phases complete
- [ ] Tests pass with 87%+ coverage
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] No breaking changes (or documented if necessary)
```

## Success Criteria

- [ ] Feature broken into 4 clear phases
- [ ] Each phase has specific tasks
- [ ] Effort estimated with p1/p2/p3 labels
- [ ] Dependencies mapped
- [ ] Risks identified with mitigations
- [ ] GitHub issues created for each phase
- [ ] Specialist agents assigned
- [ ] ADRs referenced where relevant
