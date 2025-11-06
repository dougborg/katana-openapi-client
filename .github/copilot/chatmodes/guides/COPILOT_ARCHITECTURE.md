# GitHub Copilot Agent Architecture

This document describes the three-tier architecture for GitHub Copilot agent
customizations in this project, based on patterns from
[GitHub's awesome-copilot repository](https://github.com/github/awesome-copilot).

## Overview

Our GitHub Copilot customizations are organized into three distinct layers, each serving
a specific purpose:

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 1: CHATMODES                                               │
│ Files: .github/copilot/chatmodes/*.chatmode.md                   │
│ Purpose: Define specialized agent roles and workflows            │
│ Format: YAML frontmatter + markdown                              │
│ Size: ~100-500 lines per agent                                   │
│ Examples: python-developer, tdd-specialist, task-planner         │
└──────────────────────────────────────────────────────────────────┘
                               ↓ references
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 2: INSTRUCTIONS                                            │
│ Files: .github/instructions/*.instructions.md                    │
│ Purpose: Auto-apply standards to matching file patterns          │
│ Format: YAML frontmatter + markdown (with applyTo)               │
│ Size: ~150-250 lines per instruction set                         │
│ Examples: python.instructions.md, pytest.instructions.md         │
└──────────────────────────────────────────────────────────────────┘
                               ↓ references
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 3: PROMPTS                                                 │
│ Files: .github/prompts/*.prompt.md                               │
│ Purpose: Reusable workflows that can be invoked                  │
│ Format: YAML frontmatter + markdown                              │
│ Size: ~70-200 lines per prompt                                   │
│ Examples: create-adr, regenerate-client, create-test             │
└──────────────────────────────────────────────────────────────────┘
```

## Layer 1: Chatmodes

**Purpose**: Define **HOW** specialized agents operate

### Structure

```yaml
---
description: 'Brief description of agent role and expertise'
tools: ['read', 'search', 'edit', 'shell']
---

# Agent Name

You are a specialized [role] agent...

## Mission
[Core responsibilities and goals]

## Your Expertise
[Areas of specialization]

## Workflow
[Step-by-step process for typical tasks]

## On-Demand Resources
Use the `read` tool to access:
- `.github/instructions/[tech].instructions.md` - Technology standards
- `.github/prompts/[task].prompt.md` - Reusable workflows
- `.github/copilot/chatmodes/guides/[topic].md` - Detailed guides

## Quality Gates
[Checklist before work is complete]

## Critical Reminders
[Key things agent must never forget]
```

### File Naming Convention

- Format: `[role].chatmode.md`
- Examples:
  - `python-developer.chatmode.md`
  - `tdd-specialist.chatmode.md`
  - `task-planner.chatmode.md`
  - `documentation-writer.chatmode.md`
  - `code-reviewer.chatmode.md`
  - `ci-cd-specialist.chatmode.md`
  - `project-coordinator.chatmode.md`

### Key Characteristics

- **Role-focused**: Each chatmode represents a specialized agent
- **Progressive disclosure**: Core instructions inline, detailed guides referenced
- **Tool access**: Specifies which tools the agent can use
- **Workflow-oriented**: Describes typical task flows
- **Size**: ~100-500 lines (comprehensive but not overwhelming)

### When to Create a Chatmode

Create a new chatmode when you need:

- A specialized agent with distinct responsibilities
- A specific workflow or process to follow
- Tool usage patterns unique to a role
- Quality gates specific to a type of work

## Layer 2: Instructions

**Purpose**: Define **STANDARDS** that auto-apply to file patterns

### Structure

```yaml
---
description: 'Technology or format standards'
applyTo: '**/*.ext'
---

# Technology Standards

Brief introduction to the technology and these standards.

## Core Principles
[Fundamental rules and best practices]

## Code Examples
[Working examples demonstrating standards]

## Common Patterns
[Frequently used patterns]

## Anti-Patterns
[What NOT to do]

## Tools and Commands
[Relevant commands for this technology]
```

### File Naming Convention

- Format: `[technology].instructions.md`
- Examples:
  - `python.instructions.md` (applies to `**/*.py`)
  - `pytest.instructions.md` (applies to `**/test_*.py`)
  - `markdown.instructions.md` (applies to `**/*.md`)
  - `python-mcp-server.instructions.md` (applies to `**/katana_mcp_server/**/*.py`)

### Key Characteristics

- **Auto-applying**: GitHub Copilot loads these when working on matching files
- **Technology-specific**: Focused on one technology or format
- **Standards-focused**: Conventions, not workflows
- **Size**: ~150-250 lines (comprehensive reference)
- **Pattern-based**: Uses glob patterns in `applyTo` field

### When to Create an Instruction

Create a new instruction when you have:

- Coding standards for a specific file type
- Conventions that apply broadly across the codebase
- Technology-specific best practices
- Formatting or style rules

### applyTo Pattern Examples

```yaml
# All Python files
applyTo: '**/*.py'

# Test files only
applyTo: '**/test_*.py'

# All Markdown files
applyTo: '**/*.md'

# Specific package directory
applyTo: '**/katana_mcp_server/**/*.py'

# Multiple patterns (if supported)
applyTo: ['**/*.py', '**/*.pyi']
```

## Layer 3: Prompts

**Purpose**: Define **REUSABLE TASKS** that can be invoked

### Structure

```yaml
---
description: 'Brief description of task or workflow'
---

# Task Name

Brief overview of what this task accomplishes and when to use it.

## Instructions

Step-by-step instructions for completing the task:

1. **Step 1**: [Action to take]
   - Detail 1
   - Detail 2

2. **Step 2**: [Next action]
   - Detail 1
   - Detail 2

...

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### File Naming Convention

- Format: `[action]-[noun].prompt.md`
- Examples:
  - `create-adr.prompt.md`
  - `regenerate-client.prompt.md`
  - `create-test.prompt.md`
  - `breakdown-feature.prompt.md`
  - `update-docs.prompt.md`

### Key Characteristics

- **Task-focused**: Each prompt defines a specific, repeatable task
- **Standalone**: Can be invoked without context
- **Action-oriented**: Clear steps to follow
- **Success criteria**: Explicit checklist
- **Size**: ~70-200 lines (enough detail to be self-contained)

### When to Create a Prompt

Create a new prompt when you have:

- A repeatable workflow (done more than once)
- A multi-step process that needs consistency
- A task that multiple agents might perform
- A workflow that should be standardized

## How the Layers Work Together

### Example: Python Developer Agent Writing Tests

**User request**: "Add comprehensive tests for the new inventory tool"

#### Step 1: Chatmode Loads

`python-developer.chatmode.md` loads, providing:

- Agent identity: "You are a Python development specialist"
- Core workflow: Development → Testing → Validation
- References to instructions and prompts

#### Step 2: Instructions Auto-Apply

When agent opens Python files:

- `python.instructions.md` auto-loads (for `**/*.py`)
- `python-mcp-server.instructions.md` auto-loads (for MCP server files)

When agent opens test files:

- `pytest.instructions.md` auto-loads (for `**/test_*.py`)

**Result**: Agent has all relevant standards without explicit loading

#### Step 3: Prompt Referenced

Agent references `create-test.prompt.md` for:

- Test structure (AAA pattern)
- Coverage requirements (87%+)
- Fixture patterns
- Success criteria

#### Step 4: Guides Referenced (On-Demand)

If agent needs more detail:

- Reads `guides/shared/VALIDATION_TIERS.md` for test commands
- Reads `guides/shared/FILE_ORGANIZATION.md` for test file location
- Reads `guides/shared/ARCHITECTURE_QUICK_REF.md` for patterns

### Example: Documentation Writer Agent Creating ADR

**User request**: "Document the decision to use FastMCP for the MCP server"

#### Step 1: Chatmode Loads

`documentation-writer.chatmode.md` loads, providing:

- Agent identity: "You are a documentation specialist"
- Documentation types: ADRs, guides, docstrings, README
- Quality standards

#### Step 2: Instructions Auto-Apply

When agent creates markdown file:

- `markdown.instructions.md` auto-loads (for `**/*.md`)
  - mdformat standards (88-char line length)
  - ATX-style headers
  - Code block language specification

#### Step 3: Prompt Invoked

Agent follows `create-adr.prompt.md`:

1. Find next ADR number
1. Copy template from `docs/adr/0000-template.md`
1. Fill out ADR structure
1. Update `docs/adr/README.md` index
1. Format with mdformat
1. Validate links

#### Step 4: Result

Agent creates properly formatted ADR following all standards without needing to remember
every detail.

## Progressive Disclosure in Practice

The three-tier architecture enables **true progressive disclosure**:

### Initial Context (Minimal)

When agent is invoked:

- **Chatmode**: ~150-500 lines
- **Instructions**: Auto-load only for files being edited
- **Prompts**: None (loaded on-demand)

**Total initial context**: ~200-800 lines

### On-Demand Loading

As agent works:

- **Instructions**: Auto-load when opening matching files
- **Prompts**: Load when specific task referenced
- **Guides**: Read specific sections when needed

**Total working context**: Grows only as needed

### Contrast with Old Approach

**Before (monolithic)**:

- Agent definition: 400-600 lines
- All standards embedded: +500 lines
- All workflows embedded: +300 lines
- **Total**: 1,200-1,400 lines upfront

**After (three-tier)**:

- Chatmode: 150-200 lines
- Instructions: Auto-load as needed
- Prompts: Load when referenced
- **Total initial**: 150-200 lines

**Savings**: ~85% reduction in initial context

## File Organization

```
.github/
├── copilot/
│   └── chatmodes/
│       ├── task-planner.chatmode.md
│       ├── python-developer.chatmode.md
│       ├── tdd-specialist.chatmode.md
│       ├── documentation-writer.chatmode.md
│       ├── code-reviewer.chatmode.md
│       ├── ci-cd-specialist.chatmode.md
│       ├── project-coordinator.chatmode.md
│       └── guides/
│           ├── README.md
│           ├── CONTEXT_INVESTIGATION.md
│           ├── REFACTORING_SUMMARY.md
│           ├── COPILOT_ARCHITECTURE.md (this file)
│           └── shared/
│               ├── VALIDATION_TIERS.md
│               ├── COMMIT_STANDARDS.md
│               ├── FILE_ORGANIZATION.md
│               └── ARCHITECTURE_QUICK_REF.md
├── instructions/
│   ├── python.instructions.md
│   ├── pytest.instructions.md
│   ├── markdown.instructions.md
│   └── python-mcp-server.instructions.md
└── prompts/
    ├── create-adr.prompt.md
    ├── regenerate-client.prompt.md
    ├── create-test.prompt.md
    ├── breakdown-feature.prompt.md
    └── update-docs.prompt.md
```

## Creating New Files

### Creating a New Chatmode

1. **Identify the need**: Is there a distinct agent role needed?
1. **Research patterns**: Review existing chatmodes in this project and awesome-copilot
1. **Define scope**:
   - Core responsibilities (2-5 bullet points)
   - Key workflows (step-by-step)
   - Tool access needed (read, search, edit, shell)
   - Quality gates
1. **Create file**: `.github/copilot/chatmodes/[role].chatmode.md`
1. **Use YAML frontmatter**: description + tools
1. **Structure content**: Mission → Workflow → Resources → Quality Gates
1. **Target size**: 100-500 lines (progressive disclosure)

### Creating a New Instruction

1. **Identify the technology**: Python, TypeScript, Markdown, etc.
1. **Define the pattern**: What files should this apply to?
1. **Document standards**:
   - Core principles
   - Code examples
   - Common patterns
   - Anti-patterns
1. **Create file**: `.github/instructions/[tech].instructions.md`
1. **Use YAML frontmatter**: description + applyTo (glob pattern)
1. **Target size**: 150-250 lines (comprehensive reference)

### Creating a New Prompt

1. **Identify the task**: What repeatable workflow needs standardization?
1. **Break down steps**: Clear, actionable instructions
1. **Define success criteria**: Checklist for completion
1. **Create file**: `.github/prompts/[action]-[noun].prompt.md`
1. **Use YAML frontmatter**: description
1. **Target size**: 70-200 lines (self-contained)

## Best Practices

### For Chatmodes

- **Be role-specific**: Define clear agent identity and responsibilities
- **Use progressive disclosure**: Core instructions inline, details in guides
- **Reference, don't duplicate**: Link to instructions and prompts
- **Include quality gates**: Clear completion criteria
- **Add critical reminders**: Things agent must never forget

### For Instructions

- **Focus on standards**: Conventions, not workflows
- **Use applyTo patterns**: Specific file patterns for auto-loading
- **Provide examples**: Show, don't just tell
- **Be technology-specific**: Deep focus on one tech
- **Avoid duplication**: One instruction per technology

### For Prompts

- **Be task-specific**: One clear task per prompt
- **Make it standalone**: No external context required
- **Use checklists**: Success criteria should be explicit
- **Number the steps**: Clear sequence
- **Be reusable**: Multiple agents should be able to invoke

### General Guidelines

- **DRY principle**: Don't Repeat Yourself across files
- **Single source of truth**: One place for each piece of information
- **Clear references**: Explicitly link related files
- **Maintain structure**: Consistent formatting across all files
- **Update documentation**: Keep this guide current as architecture evolves

## Migration from Old Structure

### Old Structure (Monolithic)

```yaml
# agent-dev.yml
name: agent-dev
description: Python development agent
instructions: |
  [2,000+ lines of inline instructions including:]
  - Agent role and responsibilities
  - Python standards and best practices
  - Testing patterns
  - Validation tiers
  - Commit standards
  - Architecture patterns
  - MCP server patterns
  - Workflows for common tasks
  - Quality gates
  - Critical reminders
```

**Problems**:

- All context loaded upfront
- Duplication across agents
- Hard to maintain
- No auto-applying standards

### New Structure (Three-Tier)

```yaml
# .github/copilot/chatmodes/python-developer.chatmode.md
---
description: 'Python development specialist for implementing features'
tools: ['read', 'search', 'edit', 'shell']
---

# Python Developer

You are a specialized Python development agent...

## Mission
[Core responsibilities - 50 lines]

## Workflow
[Development process - 80 lines]

## On-Demand Resources
Use the `read` tool to access:
- `.github/instructions/python.instructions.md` - Python standards
- `.github/instructions/pytest.instructions.md` - Testing standards
- `.github/prompts/create-test.prompt.md` - Test creation workflow
- `.github/copilot/chatmodes/guides/shared/VALIDATION_TIERS.md`

## Quality Gates
[Checklist - 20 lines]
```

**Benefits**:

- ~400 lines instead of 2,000+
- Python standards auto-load from `python.instructions.md`
- Test creation uses `create-test.prompt.md`
- Shared content in guides (no duplication)
- Progressive disclosure maintained

## Relationship to awesome-copilot

This architecture is based on patterns from
[GitHub's awesome-copilot repository](https://github.com/github/awesome-copilot).

### Patterns Adopted

1. **YAML frontmatter + markdown** (not pure YAML)
1. **Three-tier organization** (chatmodes/instructions/prompts)
1. **Auto-applying instructions** via `applyTo` glob patterns
1. **Reusable prompts** for common workflows
1. **Progressive disclosure** with on-demand guide loading
1. **Quality gates** and checkpoint patterns
1. **File naming conventions** (.chatmode.md, .instructions.md, .prompt.md)

### Collections Referenced

During Phase 5 implementation, we analyzed these awesome-copilot collections:

- **python-mcp-development**: Informed `python-mcp-server.instructions.md`
- **project-planning**: Informed `task-planner.chatmode.md`
- **testing-automation**: Informed `tdd-specialist.chatmode.md`

### Integration with Existing Guides

We retained our existing guide structure under `guides/`:

- `guides/shared/` - Project-specific shared content
- `guides/[agent]/` - Agent-specific detailed guides (planned)

These guides complement the three-tier architecture by providing detailed, project-
specific information that awesome-copilot patterns don't cover.

## Summary

The three-tier architecture provides:

1. **Chatmodes**: Specialized agent roles with workflows
1. **Instructions**: Auto-applying standards for file types
1. **Prompts**: Reusable tasks invoked on-demand

**Key benefits**:

- 85% reduction in initial context
- Single source of truth (DRY)
- Auto-applying standards (no manual loading)
- Reusable workflows
- Infinite scalability
- Progressive disclosure

**Result**: Comprehensive agent guidance in a well-organized, maintainable structure
that scales indefinitely.

______________________________________________________________________

**Document**: `.github/copilot/chatmodes/guides/COPILOT_ARCHITECTURE.md` **Created**:
2025-01-06 **Purpose**: Document three-tier architecture for GitHub Copilot agent
customizations
