# ADR-0014: GitHub Copilot Custom Agents with Three-Tier Architecture

## Status

Accepted

Date: 2025-01-06

## Context

As the katana-openapi-client project grew to include both a Python client library and an
MCP server, we needed a way to provide specialized AI assistance for different
development tasks. GitHub Copilot supports custom agents that can be tailored to
specific roles and workflows, but we needed to determine the optimal structure for
organizing these agents and their supporting materials.

### Forces at Play

**Technological:**

- GitHub Copilot supports custom agents via `.github/` directory configuration
- Official documentation specifies `.github/agents/*.agent.md` structure
- YAML frontmatter must follow specific format with `name`, `description`, `tools`
  properties
- Progressive disclosure is critical - agents should load minimal context initially
- Markdown formatters (mdformat) can break YAML frontmatter if not configured properly

**Project-Specific:**

- Monorepo structure with two packages (client + MCP server)
- Multiple specialized development roles needed (planning, coding, testing,
  documentation, review, DevOps, coordination)
- Complex architectural patterns that agents need to understand (transport-layer
  resilience, Pydantic domain models, MCP architecture)
- Need for consistent coding standards across file types (Python, pytest, markdown, MCP)
- Reusable workflow patterns for common tasks (create ADR, regenerate client, run tests)

**User Experience:**

- Developers should be able to invoke specialized agents for specific tasks
- Agents should have access to relevant context without being overwhelmed
- Instructions should auto-apply based on file type being edited
- Workflow prompts should be easily discoverable and reusable

## Decision

We will adopt a **three-tier architecture** for GitHub Copilot customization, following
official GitHub Copilot conventions while incorporating progressive disclosure patterns
from the awesome-copilot community repository.

### Architecture Components

**1. Agents (`.github/agents/*.agent.md`)**

Purpose: Define specialized agent roles with specific workflows and expertise

Structure:

```yaml
---
name: agent-name
description: 'Brief description of agent role and expertise'
tools: ['read', 'search', 'edit', 'shell']
---

# Agent Name

Agent instructions and behavioral guidance...
```

Agents created:

- `task-planner.agent.md` - Creates actionable implementation plans
- `python-developer.agent.md` - Implements features and fixes bugs
- `tdd-specialist.agent.md` - Writes comprehensive tests
- `documentation-writer.agent.md` - Maintains documentation
- `code-reviewer.agent.md` - Conducts thorough code reviews
- `ci-cd-specialist.agent.md` - Manages DevOps and releases
- `project-coordinator.agent.md` - Orchestrates multi-agent work

**2. Instructions (`.github/instructions/*.instructions.md`)**

Purpose: Define coding standards that auto-apply to specific file patterns

Structure:

```yaml
---
description: 'Technology or format standards'
applyTo: '**/*.py'
---

Standards and best practices...
```

Instructions created:

- `python.instructions.md` → applies to `**/*.py`
- `pytest.instructions.md` → applies to `**/test_*.py`
- `markdown.instructions.md` → applies to `**/*.md`
- `python-mcp-server.instructions.md` → applies to `**/katana_mcp_server/**/*.py`

**3. Prompts (`.github/prompts/*.prompt.md`)**

Purpose: Define reusable workflow templates for common tasks

Created prompts:

- `create-adr.prompt.md` - Generate Architecture Decision Records
- `regenerate-client.prompt.md` - Regenerate OpenAPI client
- `create-test.prompt.md` - Write comprehensive tests
- `breakdown-feature.prompt.md` - Break features into phases
- `update-docs.prompt.md` - Update documentation after changes

### Progressive Disclosure

Agent files (~150-250 lines) contain core instructions and references to on-demand
resources stored in `.github/agents/guides/`:

- `guides/plan/` - Planning methodology, issue templates, effort estimation
- `guides/devops/` - CI debugging, dependency updates, release process
- `guides/shared/` - Architecture quick reference, validation tiers, commit standards

Agents use the `read` tool to load these guides only when needed.

### Configuration Details

- **File extension**: `.agent.md` (distinguishes from regular markdown)
- **mdformat exclusion**: Agent files excluded from mdformat to preserve YAML
  frontmatter
- **CODEOWNERS**: `.github/CODEOWNERS` assigns ownership of Copilot configuration
- **Validation**: Pre-commit hooks validate YAML syntax with yamllint

## Consequences

### Positive Consequences

1. **Specialized expertise**: Each agent has focused knowledge and clear
   responsibilities
1. **Official compliance**: Structure follows GitHub Copilot official documentation
1. **Progressive disclosure**: Agents start small (~150 lines) and load context
   on-demand
1. **Auto-applying standards**: Instructions automatically enforce coding standards by
   file type
1. **Reusable workflows**: Prompts provide consistent task execution patterns
1. **Maintainability**: Clear separation of concerns makes updates easier
1. **Discoverability**: Developers can invoke agents by role (@python-developer,
   @tdd-specialist, etc.)
1. **Context preservation**: mdformat exclusion prevents YAML frontmatter corruption

### Negative Consequences

1. **Learning curve**: Developers need to learn which agent to invoke for which task
1. **Maintenance overhead**: Seven agents + four instructions + five prompts to maintain
1. **File proliferation**: 16 configuration files + extensive guide documentation
1. **Non-standard extension**: `.agent.md` extension is a project convention, not a
   GitHub standard

### Neutral Consequences

1. **Guide organization**: Extensive guide structure (plan/, devops/, shared/) adds
   complexity but provides organization
1. **Monorepo considerations**: Agents handle both client and MCP server, requiring
   awareness of both
1. **Documentation duplication**: Some content duplicated between CLAUDE.md,
   AGENT_WORKFLOW.md, and agent files

## Alternatives Considered

### Alternative 1: Single General-Purpose Agent

**Description**: Use one generic "assistant" agent with all knowledge combined

**Pros**:

- Simpler to maintain (one file vs seven)
- No need to decide which agent to invoke
- Easier for developers to use

**Cons**:

- Violates progressive disclosure (would be 2000+ lines)
- No role specialization - agent tries to do everything
- Harder to optimize for specific tasks
- Loses benefits of agent coordination

**Why rejected**: Would create a massive context dump and lose the benefits of
specialized expertise

### Alternative 2: awesome-copilot Structure Only

**Description**: Use `.github/copilot/chatmodes/*.chatmode.md` from awesome-copilot
repository

**Pros**:

- Follows community examples
- Three-tier architecture pattern proven

**Cons**:

- Not the official GitHub Copilot structure
- `.chatmode.md` extension is non-standard
- `chatmodes` directory not in official docs

**Why rejected**: Official GitHub documentation specifies `.github/agents/` - following
official conventions provides better long-term stability

### Alternative 3: No Custom Agents

**Description**: Rely on default GitHub Copilot behavior only

**Pros**:

- Zero maintenance overhead
- No custom configuration needed
- Simpler project structure

**Cons**:

- No project-specific knowledge
- No architectural pattern awareness
- No validation tier guidance
- No role-based specialization

**Why rejected**: Project complexity requires specialized assistance for different
development tasks

## References

- [GitHub Copilot Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Creating Custom Agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [GitHub Copilot Custom Instructions](https://docs.github.com/en/copilot/concepts/prompting/response-customization#about-repository-custom-instructions)
- [awesome-copilot Repository](https://github.com/github/awesome-copilot) - Community
  examples and patterns
- PR #145: Initial three-tier architecture migration
- PR #146: Adoption of official GitHub structure
- `.github/agents/guides/CONTEXT_INVESTIGATION.md` - Investigation findings
- `.github/agents/guides/COPILOT_ARCHITECTURE.md` - Architecture documentation
- `.github/agents/guides/REFACTORING_SUMMARY.md` - Implementation metrics
