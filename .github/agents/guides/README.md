# GitHub Copilot Agent Guides

This directory contains progressive disclosure documentation for our specialized GitHub
Copilot agents. Instead of loading all context upfront, agents reference these guides
on-demand to access detailed information only when needed.

## Progressive Disclosure Strategy

Agents follow a three-level information hierarchy:

1. **Level 1 - Agent Definition** (~100 lines) - Core role, responsibilities, quick
   reference
1. **Level 2 - Specialized Guides** (this directory) - Detailed processes, patterns,
   templates
1. **Level 3 - Codebase Documentation** (CLAUDE.md, ADRs, etc.) - Reference materials

This approach reduces initial context from 2,000+ lines to \<500 lines while maintaining
full capability through on-demand file access.

## Directory Structure

### Shared Resources (All Agents)

- **[shared/VALIDATION_TIERS.md](shared/VALIDATION_TIERS.md)** - Validation command
  hierarchy
- **[shared/COMMIT_STANDARDS.md](shared/COMMIT_STANDARDS.md)** - Semantic versioning and
  conventional commits
- **[shared/FILE_ORGANIZATION.md](shared/FILE_ORGANIZATION.md)** - Generated vs editable
  files
- **[shared/ARCHITECTURE_QUICK_REF.md](shared/ARCHITECTURE_QUICK_REF.md)** - ADR
  summaries and key patterns

### Agent-Specific Guides

#### Development Agent (agent-dev)

- **[dev/IMPLEMENTATION_PATTERNS.md](dev/IMPLEMENTATION_PATTERNS.md)** - Code patterns
  and best practices
- **[dev/CODE_EXAMPLES.md](dev/CODE_EXAMPLES.md)** - Common implementation examples
- **[dev/MCP_TOOL_TEMPLATE.py](dev/MCP_TOOL_TEMPLATE.py)** - MCP tool boilerplate

#### Documentation Agent (agent-docs)

- **[docs/ADR_WRITING_GUIDE.md](docs/ADR_WRITING_GUIDE.md)** - Architecture Decision
  Record format
- **[docs/MARKDOWN_STANDARDS.md](docs/MARKDOWN_STANDARDS.md)** - Markdown style guide
- **[docs/DOCUMENTATION_CHECKLIST.md](docs/DOCUMENTATION_CHECKLIST.md)** - Pre-publish
  validation

#### Testing Agent (agent-test)

- **[test/TESTING_PATTERNS.md](test/TESTING_PATTERNS.md)** - Test structure and
  organization
- **[test/FIXTURE_GUIDE.md](test/FIXTURE_GUIDE.md)** - Pytest fixtures and mocking
- **[test/COVERAGE_STRATEGIES.md](test/COVERAGE_STRATEGIES.md)** - Coverage targets and
  ratcheting

#### Planning Agent (agent-plan)

- **[plan/PLANNING_PROCESS.md](plan/PLANNING_PROCESS.md)** - Step-by-step planning
  methodology
- **[plan/ISSUE_TEMPLATES.md](plan/ISSUE_TEMPLATES.md)** - Structured issue format
- **[plan/EFFORT_ESTIMATION.md](plan/EFFORT_ESTIMATION.md)** - Complexity estimation
  guidelines

#### Review Agent (agent-review)

- **[review/REVIEW_CHECKLIST.md](review/REVIEW_CHECKLIST.md)** - Code review checklist
- **[review/COMMON_ISSUES.md](review/COMMON_ISSUES.md)** - Frequent problems to catch
- **[review/REVIEW_PATTERNS.md](review/REVIEW_PATTERNS.md)** - Review workflow patterns

#### Coordinator Agent (agent-coordinator)

- **[coordinator/PR_MANAGEMENT.md](coordinator/PR_MANAGEMENT.md)** - PR monitoring and
  routing
- **[coordinator/DELEGATION_PATTERNS.md](coordinator/DELEGATION_PATTERNS.md)** - Agent
  coordination strategies
- **[coordinator/STATUS_TEMPLATES.md](coordinator/STATUS_TEMPLATES.md)** - Status update
  formats

#### DevOps Agent (agent-devops)

- **[devops/CI_DEBUGGING.md](devops/CI_DEBUGGING.md)** - GitHub Actions troubleshooting
- **[devops/DEPENDENCY_UPDATES.md](devops/DEPENDENCY_UPDATES.md)** - uv dependency
  management
- **[devops/RELEASE_PROCESS.md](devops/RELEASE_PROCESS.md)** - Semantic-release workflow
- **[devops/CLIENT_REGENERATION.md](devops/CLIENT_REGENERATION.md)** - OpenAPI client
  regeneration

## Usage Pattern for Agents

When an agent needs detailed information, it reads the appropriate guide:

```yaml
# In agent definition
instructions: |
  ## When You Need Details

  **For validation commands:**
  Read guides/shared/VALIDATION_TIERS.md

  **For planning methodology:**
  Read guides/plan/PLANNING_PROCESS.md § "Epic Breakdown"

  **For code patterns:**
  Read guides/dev/IMPLEMENTATION_PATTERNS.md § "MCP Tool Pattern"
```

## Benefits

- **Scalability** - Support unlimited agents without context overload
- **Efficiency** - Minimal initial token consumption
- **Maintainability** - Single source of truth for shared content
- **Flexibility** - Deep content accessible only when needed
- **Cost** - Reduced token usage per agent invocation

## Maintenance

When updating agent capabilities:

1. Update the agent definition (agent-\*.yml) for core changes
1. Update the relevant guide for detailed process changes
1. Keep this README.md index up to date
1. Ensure cross-references remain accurate

______________________________________________________________________

*Based on Anthropic's progressive disclosure pattern for agent skills*
