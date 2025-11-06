# Planning Process Guide

This guide provides the step-by-step methodology for breaking down complex tasks into
actionable implementation plans.

## Table of Contents

1. [Understanding the Request](#1-understand-the-request) (§1)
1. [Creating Phased Plans](#2-create-phased-implementation-plan) (§2)
1. [Estimating Effort](#3-estimate-effort) (§3)
1. [Identifying Dependencies](#4-identify-dependencies) (§4)
1. [Creating Issues](#5-create-issues) (§5)
1. [Risk Assessment](#6-risk-assessment) (§6)
1. [Agent Coordination](#7-coordination-with-other-agents) (§7)

______________________________________________________________________

## 1. Understand the Request

Before creating any plan, thoroughly understand what's being asked.

### Steps

**Read Full Context:**

- Review the complete request or issue description
- Understand user goals and use cases
- Identify pain points being addressed

**Check Related Work:**

```bash
# Search for related issues
gh issue list --search "keyword" --state all

# Check recent PRs
gh pr list --search "keyword" --state all

# View specific issue/PR
gh issue view 123
gh pr view 456
```

**Review Relevant ADRs:**

- Check [ADR index](../../../../docs/adr/README.md)
- Understand existing architectural patterns
- Identify constraints or requirements
- Look for similar past decisions

**Identify Affected Packages:**

- `katana-openapi-client` - Python SDK
- `katana-mcp-server` - MCP server
- Both (monorepo-wide changes)

**Key Questions to Answer:**

- What problem are we solving?
- Who will use this feature?
- What's the expected behavior?
- Are there breaking changes?
- What's the urgency/priority?

______________________________________________________________________

## 2. Create Phased Implementation Plan

Break work into logical, sequential phases that build on each other.

### Standard Phase Structure

#### Phase 1: Foundation

**Focus:** Core infrastructure and setup

**Typical work:**

- Breaking changes (if any)
- Dependencies and setup
- Core data structures
- Base infrastructure
- ADR creation (for major decisions)

**Why first:**

- Establishes foundation
- Minimizes rework
- Clarifies architecture early

#### Phase 2: Core Features

**Focus:** Main functionality implementation

**Typical work:**

- Primary API endpoints/tools
- Core domain models
- Essential business logic
- Basic error handling

**Why second:**

- Builds on foundation
- Delivers primary value
- Enables testing

#### Phase 3: Enhancements

**Focus:** Improvements and conveniences

**Typical work:**

- Helper utilities
- Convenience methods
- Performance optimizations
- Advanced features
- Edge case handling

**Why third:**

- Requires core features
- Adds polish
- Not blocking for basic use

#### Phase 4: Documentation & Polish

**Focus:** User-facing deliverables

**Typical work:**

- User guides
- API documentation
- Examples and cookbook entries
- ADR updates
- Migration guides (if needed)

**Why last:**

- Requires complete implementation
- Captures final design
- Enables user adoption

### Phase Examples

**Example: New MCP Tool**

```markdown
Phase 1: Foundation (p2-medium)
- Create tool file following existing pattern
- Add basic list operation
- Setup test structure

Phase 2: Core Operations (p2-medium)
- Implement create/update tools
- Add preview/confirm pattern
- Comprehensive error handling

Phase 3: Advanced Features (p3-low)
- Workflow helpers
- Bulk operations
- Optimization

Phase 4: Documentation (p3-low)
- Cookbook examples
- README updates
- Tutorial
```

**Example: Breaking Change**

```markdown
Phase 1: Foundation & ADR (p2-medium)
- Create ADR documenting decision
- Outline migration strategy
- Identify all breaking changes
- Plan deprecation timeline

Phase 2: Incremental Migration (p1-high)
- Migrate module 1 with backward compat
- Migrate module 2 with backward compat
- Migrate remaining modules
- Add migration guide

Phase 3: Testing & Validation (p2-medium)
- End-to-end integration tests
- Performance benchmarks
- Edge case validation

Phase 4: Documentation & Release (p3-low)
- Update migration guide
- Create release notes
- Coordinate major version release
```

______________________________________________________________________

## 3. Estimate Effort

Use consistent effort labels based on time and complexity.

### Effort Labels

| Label         | Time      | Complexity | Typical Work                                   |
| ------------- | --------- | ---------- | ---------------------------------------------- |
| **p1-high**   | 1-2 days  | High       | Large features, refactoring, breaking changes  |
| **p2-medium** | 4-8 hours | Moderate   | New tools, moderate features, bug fixes        |
| **p3-low**    | 1-3 hours | Low        | Small utilities, documentation, simple updates |

### Estimation Factors

**Code Complexity:**

- Lines of code expected
- Number of files affected
- Integration points
- Error handling requirements

**Testing Requirements:**

- Unit test coverage needed
- Integration tests required
- Manual testing scenarios
- Edge cases to cover

**Documentation Needs:**

- User-facing docs
- API reference
- Examples/cookbook
- ADR creation/updates

**Review and Iteration:**

- Expected review rounds
- Potential rework
- Testing iterations
- Feedback incorporation

### Estimation Guidelines

**p1-high (1-2 days):**

- 500+ lines of code
- 5+ files affected
- Complex business logic
- Comprehensive test suite
- Significant documentation
- Multiple review rounds

**p2-medium (4-8 hours):**

- 200-500 lines of code
- 2-5 files affected
- Moderate complexity
- Standard test coverage
- Basic documentation
- 1-2 review rounds

**p3-low (1-3 hours):**

- \<200 lines of code
- 1-2 files affected
- Simple logic
- Minimal testing
- Light documentation
- Single review pass

### When in Doubt

- **Start with p2-medium** and adjust
- **Ask for clarification** if scope unclear
- **Break into smaller pieces** if > 2 days
- **Factor in unknowns** - add buffer for research/learning

______________________________________________________________________

## 4. Identify Dependencies

Map relationships between tasks to determine sequencing.

### Dependency Types

**Blocking Dependencies (Must Complete First):**

```markdown
Issue #123: Create base infrastructure
└─> Issue #124: Build feature on infrastructure  [BLOCKED]
    └─> Issue #125: Add convenience methods     [BLOCKED]
```

**Related Work (Should Be Aware Of):**

```markdown
Issue #123: Add product search
Issue #124: Add order search  [RELATED - similar pattern]
```

**Future Work (Can Build On Later):**

```markdown
Issue #123: Basic MCP tools
Issue #456: Advanced workflows  [FUTURE - builds on #123]
```

### Dependency Mapping Process

**Step 1: List All Tasks** Write out all issues/tasks from your phased plan.

**Step 2: Identify Prerequisites** For each task, ask:

- What must exist before this can start?
- What does this task build upon?
- Are there shared resources?

**Step 3: Draw Dependency Graph**

```markdown
Phase 1
  ├─ #101: Foundation

Phase 2 (depends on #101)
  ├─ #102: Core Feature A
  └─ #103: Core Feature B   [can run parallel with #102]

Phase 3 (depends on #102, #103)
  └─ #104: Enhancements

Phase 4 (depends on #104)
  └─ #105: Documentation
```

**Step 4: Identify Parallelization Opportunities**

- Tasks in same phase with no shared dependencies
- Can assign to multiple agents simultaneously
- Reduces overall timeline

### Documenting Dependencies

In each issue, include:

```markdown
## Dependencies

**Blocks:**
- Issue #124 - Feature requires this infrastructure
- Issue #125 - Enhancement depends on core feature

**Depends On:**
- Issue #101 - Needs base infrastructure first
- PR #202 - Requires merged changes

**Related:**
- Issue #98 - Similar pattern, reference for consistency
- ADR-007 - Architectural guidance
```

______________________________________________________________________

## 5. Create Issues

Transform your plan into well-structured, actionable GitHub issues.

### Issue Creation Checklist

- [ ] Clear, action-oriented title
- [ ] Comprehensive background/context
- [ ] Specific implementation steps
- [ ] Testing strategy defined
- [ ] Success criteria measurable
- [ ] References to ADRs/docs
- [ ] Proper labels applied
- [ ] Dependencies documented
- [ ] Effort estimated

### Using the Issue Template

See [ISSUE_TEMPLATES.md](ISSUE_TEMPLATES.md) for complete template and examples.

### Issue Creation Commands

```bash
# Create issue from template
gh issue create \
  --title "feat(mcp): add sales order tools" \
  --label "scope:mcp,p2-medium,enhancement" \
  --body-file .github/ISSUE_TEMPLATE/feature.md

# Create issue interactively
gh issue create --web

# Bulk create issues from plan
for title in "${titles[@]}"; do
  gh issue create --title "$title" --label "$labels" --body "$body"
done
```

### Issue Numbering and Tracking

**Reference format:**

- Use issue numbers: `#123`
- Cross-reference: `Depends on #122`
- Link PRs: `Closes #123`

**Project organization:**

```bash
# Add to project board
gh project item-add <project-id> --url <issue-url>

# View project items
gh project item-list <project-id>
```

______________________________________________________________________

## 6. Risk Assessment

Identify and mitigate potential risks in your plan.

### Technical Risks

**Breaking Changes:**

- Impact on existing users
- Migration effort required
- Backward compatibility concerns

**Performance Impacts:**

- Slower response times
- Increased resource usage
- Scalability concerns

**Compatibility Issues:**

- Python version requirements
- Dependency conflicts
- API version changes

**Complex Refactoring:**

- High touch areas
- Many interdependencies
- Difficult to test

### Process Risks

**Large Scope (> 1 week):**

- Hard to estimate accurately
- Increased coordination overhead
- Higher chance of mid-course changes

**Multiple Dependencies:**

- Coordination challenges
- Blocking cascades
- Integration complexity

**External Blockers:**

- Waiting on upstream fixes
- API changes
- Third-party service issues

**Team Coordination:**

- Multiple agents needed
- Communication overhead
- Merge conflicts

### Mitigation Strategies

**For Breaking Changes:**

```markdown
Mitigation:
- Create deprecation warnings first
- Maintain backward compatibility layer
- Provide migration guide
- Version bump appropriately (major)
```

**For Large Scope:**

```markdown
Mitigation:
- Break into smaller, deliverable phases
- Set intermediate milestones
- Enable incremental releases
- Use feature flags
```

**For Performance:**

```markdown
Mitigation:
- Add performance benchmarks
- Set SLO targets
- Monitor in production
- Have rollback plan
```

**For Dependencies:**

```markdown
Mitigation:
- Clearly document all dependencies
- Parallel work where possible
- Regular sync-ups between agents
- Shared progress tracking
```

### Risk Documentation

Include in plan summary:

```markdown
## Risks and Mitigation

### High Risk: Breaking API Changes
**Risk:** Existing users' code will break
**Mitigation:**
- Implement backward compatibility layer
- 3-month deprecation period
- Comprehensive migration guide
- Major version bump (v2.0.0)

### Medium Risk: Performance Impact
**Risk:** New retry logic may slow requests
**Mitigation:**
- Benchmark before/after
- Make retries configurable
- Document performance characteristics
```

______________________________________________________________________

## 7. Coordination with Other Agents

Plan which agents will execute each phase of work.

### Agent Specializations

**@agent-dev** - Development and Implementation

- New features
- Bug fixes
- Refactoring
- Integration work

**@agent-test** - Testing and Quality

- Test coverage improvements
- Debugging test failures
- Performance testing
- Coverage analysis

**@agent-docs** - Documentation

- User guides
- API reference
- ADR creation
- Examples/tutorials

**@agent-review** - Code Review

- PR reviews
- Quality checks
- Architecture validation
- Security review

**@agent-coordinator** - Orchestration

- Multi-agent coordination
- PR management
- Cross-cutting concerns
- Status tracking

**@agent-devops** - Infrastructure and Automation

- CI/CD management
- Dependency updates
- Release coordination
- Build optimization

### Agent Assignment in Plans

**Example: MCP Tool Implementation**

```markdown
Phase 1: Foundation (p2-medium) → @agent-dev
- Create tool structure
- Basic implementation
- Initial tests

Phase 2: Core Features (p2-medium) → @agent-dev
- Complete tool implementation
- Comprehensive error handling

Phase 3: Testing (p3-low) → @agent-test
- Expand test coverage
- Integration testing
- Edge cases

Phase 4: Documentation (p3-low) → @agent-docs
- User guide
- Cookbook examples
- API reference

Final Review → @agent-review
- Code quality check
- Architecture review
```

### Coordination Patterns

**Sequential Handoff:**

```markdown
@agent-dev implements → @agent-test validates → @agent-docs documents → @agent-review approves
```

**Parallel Work:**

```markdown
@agent-dev: Core feature A
@agent-dev: Core feature B  (parallel)
Both complete → @agent-test validates both
```

**Iterative:**

```markdown
@agent-dev: Initial implementation
@agent-review: Feedback
@agent-dev: Address feedback  (repeat)
@agent-test: Final validation
```

### Coordination in Issue Body

```markdown
## Agent Assignment

**Primary:** @agent-dev
**Testing:** @agent-test (after core implementation)
**Review:** @agent-review (final quality check)

**Coordination Notes:**
- @agent-dev: Complete implementation and open PR
- @agent-test: Run comprehensive test suite
- @agent-review: Perform architecture review
- All: Use #xyz channel for questions
```

______________________________________________________________________

## Complete Planning Workflow

### End-to-End Example

**Request:** "Add inventory management tools to MCP server"

**Step 1: Understand (30 min)**

- Review ADR-010 (MCP architecture)
- Check existing tool patterns
- Understand inventory API endpoints
- Identify user workflows

**Step 2: Create Plan (1 hour)**

```markdown
Phase 1: Foundation (p2-medium, 4-6h)
- Create inventory_tools.py following pattern
- Add search_inventory_items tool
- Setup test structure

Phase 2: Core Operations (p2-medium, 4-6h)
- Add get_stock_level tool
- Add adjust_stock tool with preview
- Comprehensive error handling

Phase 3: Advanced Features (p3-low, 2-3h)
- Add batch_stock_check tool
- Optimize for common queries
- Workflow helpers

Phase 4: Documentation (p3-low, 2-3h)
- Cookbook examples
- README updates
- Tutorial for inventory workflows
```

**Step 3: Estimate (15 min)**

- Total: 12-18 hours (~2-3 days)
- Risk: Low (similar to existing tools)
- Confidence: High (clear pattern to follow)

**Step 4: Dependencies (15 min)**

```markdown
Dependencies:
- None (builds on existing MCP infrastructure)

Related:
- purchase_orders.py - similar pattern
- ADR-010 - architecture guidance
```

**Step 5: Create Issues (30 min)** Create 4 issues following template:

- Issue #201: Phase 1 (p2-medium, @agent-dev)
- Issue #202: Phase 2 (p2-medium, @agent-dev)
- Issue #203: Phase 3 (p3-low, @agent-dev)
- Issue #204: Phase 4 (p3-low, @agent-docs)

**Step 6: Risk Assessment (15 min)**

```markdown
Risks:
- Low risk: well-established pattern
- Medium risk: inventory API complexity
  Mitigation: Start with simple operations

No blocking concerns.
```

**Step 7: Coordinate (15 min)**

```markdown
Agent Assignments:
- #201, #202, #203 → @agent-dev
- #204 → @agent-docs
- Final review → @agent-review

Timeline: ~2-3 days
```

**Total Planning Time:** ~3 hours for comprehensive plan

______________________________________________________________________

## Best Practices

### DO ✅

- **Start with research** - Understand before planning
- **Break into phases** - Make work manageable
- **Be specific** - Clear, actionable steps
- **Reference ADRs** - Maintain consistency
- **Estimate honestly** - Include buffer time
- **Document dependencies** - Prevent blocking
- **Assign agents** - Clear ownership
- **Track progress** - Use issues/projects

### DON'T ❌

- **Skip research** - Don't plan blind
- **Create monolithic issues** - Break down large work
- **Be vague** - "Add feature" isn't actionable
- **Ignore architecture** - Check ADRs first
- **Underestimate** - Factor in testing, docs, review
- **Ignore dependencies** - Will cause delays
- **Leave unassigned** - Clear ownership matters
- **Plan and forget** - Monitor execution

______________________________________________________________________

## Summary

**Planning Process:**

1. ✅ Understand → Research thoroughly
1. ✅ Plan → Break into phases
1. ✅ Estimate → Be realistic
1. ✅ Dependencies → Map relationships
1. ✅ Create → Write detailed issues
1. ✅ Assess → Identify risks
1. ✅ Coordinate → Assign agents

**Key Principles:**

- 🎯 **Clarity** - Make work obvious
- 📊 **Measurability** - Define success criteria
- 🔗 **Traceability** - Link related work
- ⚡ **Actionability** - Enable execution
- 🤝 **Collaboration** - Coordinate agents

For templates and examples, see [ISSUE_TEMPLATES.md](ISSUE_TEMPLATES.md). For effort
estimation details, see [EFFORT_ESTIMATION.md](EFFORT_ESTIMATION.md).
