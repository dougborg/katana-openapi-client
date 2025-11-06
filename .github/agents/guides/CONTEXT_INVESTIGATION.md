# Context Property Investigation

## Summary

Investigation into the `context.files` and `context.patterns` properties used in our
GitHub Copilot custom agent definitions revealed these properties are **not documented**
in the official GitHub Copilot custom agents configuration reference.

## Official Documentation

**Source**:
[GitHub Copilot Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

**Documented YAML Properties**:

- `name` (required) - Agent name
- `description` (required) - Agent purpose
- `tools` (optional) - List of tools the agent can use
- `mcp-servers` (optional) - MCP server configurations (org/enterprise only)

**No mention of**:

- `context`
- `context.files`
- `context.patterns`

## Our Implementation

### Before (Undocumented)

```yaml
context:
  files:
    - .github/agents/guides/plan/*.md
    - .github/agents/guides/shared/*.md
  patterns:
    - "docs/adr/*.md"
```

**Status**: This property may be:

- Silently ignored by GitHub Copilot
- Undocumented internal feature
- Legacy/experimental configuration

### After (Documented Approach)

```yaml
tools: ["read", "edit", "search", "shell"]

## Related Files

Use the `read` tool to access these files when needed:
- `.github/copilot-instructions.md` - General Copilot instructions
- `CLAUDE.md` - Claude Code agent instructions
- `docs/adr/*.md` - Individual ADRs for architectural context
```

## Progressive Disclosure Still Works

Our strategy remains valid regardless of `context.files` behavior:

**Level 1: Agent Definition** (~125 lines)

- Loaded immediately when agent is invoked
- Contains core instructions and references

**Level 2: Specialized Guides** (loaded on-demand)

- Agent reads files using `read` tool when instructed
- Example: "Read `.github/agents/guides/plan/PLANNING_PROCESS.md`"

**Level 3: Codebase Documentation** (loaded on-demand)

- Agent reads ADRs, CLAUDE.md, etc. when needed
- Follows references in instructions

## Key Insight

The documented approach relies on:

1. **tools property** - Enables `read`, `edit`, `search`, `shell` capabilities
1. **Explicit instructions** - "Read X.md when you need Y"
1. **Agent following instructions** - Uses `read` tool to fetch content

This is **true progressive disclosure** - the agent only loads files when it actually
needs them by executing read operations.

## Tool Aliases

From official documentation:

| Primary  | Compatible                           | Purpose                  |
| -------- | ------------------------------------ | ------------------------ |
| `read`   | Read, NotebookRead                   | Read file contents       |
| `edit`   | Edit, MultiEdit, Write, NotebookEdit | Edit files               |
| `search` | Grep, Glob                           | Search for files or text |
| `shell`  | Bash, powershell                     | Execute shell commands   |

We use: `["read", "edit", "search", "shell"]`

## Recommendation

✅ **Use documented approach**:

- Specify `tools` property with needed tool aliases
- Include "Related Files" section in instructions
- Provide explicit "Read X when you need Y" guidance

❌ **Avoid undocumented properties**:

- Don't rely on `context.files` or `context.patterns`
- These may be ignored or removed in future updates

## References

- [GitHub Copilot Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Creating Custom Agents](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents)
- [Reddit: Progressive Disclosure Best Practices](https://www.reddit.com/r/github/comments/progressive_disclosure)

## Three-Tier Architecture

After adopting patterns from
[GitHub's awesome-copilot repository](https://github.com/github/awesome-copilot), we now
organize GitHub Copilot customizations into three distinct types:

### 1. Agents (`.md`)

**Purpose**: Define **HOW** the chat operates

**Location**: `.github/agents/*.md`

**Structure**:

```yaml
---
name: agent-name
description: 'Brief description of agent role and expertise'
tools: ['read', 'search', 'edit', 'shell']
---

# Agent Name

You are a specialized agent for [purpose]...

## Mission
[Core responsibilities]

## Workflow
[Step-by-step process]

## On-Demand Resources
Use the `read` tool to access:
- `.github/instructions/*.instructions.md` - Technology standards
- `.github/prompts/*.prompt.md` - Reusable workflows
```

**Key features**:

- YAML frontmatter + markdown content (NOT pure YAML)
- ~100-200 lines per agent (progressive disclosure)
- References to instructions and prompts
- Specific to agent role (planner, developer, tester, etc.)

**When to use**: Creating specialized agents with specific workflows and
responsibilities

### 2. Instructions (`.instructions.md`)

**Purpose**: Define **STANDARDS** that auto-apply to file patterns

**Location**: `.github/instructions/*.instructions.md`

**Structure**:

```yaml
---
description: 'Technology or format standards'
applyTo: '**/*.py'  # Glob pattern for auto-application
---

# Technology Standards

## Best Practices
[Standards that apply to all matching files]

## Examples
[Code examples following standards]
```

**Key features**:

- Auto-apply to files matching `applyTo` pattern
- Technology-specific (Python, pytest, markdown, MCP)
- Standards and conventions, not workflows
- Loaded automatically when working on matching files

**When to use**: Defining coding standards, formatting rules, or conventions that apply
across many files

**Examples in this project**:

- `python.instructions.md` → `**/*.py`
- `pytest.instructions.md` → `**/test_*.py`
- `markdown.instructions.md` → `**/*.md`
- `python-mcp-server.instructions.md` → `**/katana_mcp_server/**/*.py`

### 3. Prompts (`.prompt.md`)

**Purpose**: Define **REUSABLE TASKS** that can be invoked

**Location**: `.github/prompts/*.prompt.md`

**Structure**:

```yaml
---
description: 'Brief description of task'
---

# Task Name

[Detailed instructions for completing a specific task]

## Steps
1. [Step 1]
2. [Step 2]
...

## Success Criteria
- [ ] Checklist item 1
- [ ] Checklist item 2
```

**Key features**:

- Standalone, reusable workflows
- Can be invoked by name from any context
- Task-focused (not role-focused)
- Includes success criteria and checklists

**When to use**: Creating repeatable tasks like "create ADR", "regenerate client",
"update docs"

**Examples in this project**:

- `create-adr.prompt.md` - Create Architecture Decision Record
- `regenerate-client.prompt.md` - Regenerate OpenAPI client
- `create-test.prompt.md` - Write comprehensive tests
- `breakdown-feature.prompt.md` - Break feature into phases
- `update-docs.prompt.md` - Update documentation after changes

### When to Use Each Type

```
┌─────────────────────────────────────────────────────────────┐
│ AGENTS: Specialized agent roles with workflows             │
│ Example: python-developer.md                               │
│ Use for: Creating agents with specific expertise           │
└─────────────────────────────────────────────────────────────┘
                          ↓ references
┌─────────────────────────────────────────────────────────────┐
│ INSTRUCTIONS: Auto-applying standards for file types       │
│ Example: python.instructions.md → **/*.py                  │
│ Use for: Coding standards that apply broadly               │
└─────────────────────────────────────────────────────────────┘
                          ↓ references
┌─────────────────────────────────────────────────────────────┐
│ PROMPTS: Reusable tasks invoked on-demand                  │
│ Example: create-adr.prompt.md                              │
│ Use for: Repeatable workflows anyone can trigger           │
└─────────────────────────────────────────────────────────────┘
```

**Decision tree**:

- Need an agent with specific role? → **Agent**
- Need standards for a file type? → **Instruction**
- Need a reusable task? → **Prompt**

### Progressive Disclosure in Practice

The three-tier architecture enables true progressive disclosure:

**Level 1**: Agent file loaded (~150 lines)

- Core agent identity and workflow
- References to relevant instructions and prompts

**Level 2**: Instructions auto-loaded when working on matching files

- Python standards when editing `.py` files
- Markdown standards when editing `.md` files
- No manual loading required

**Level 3**: Prompts and guides loaded on-demand

- Agent reads specific guides when instructed
- User invokes specific prompts by name
- Only load what's needed, when it's needed

**Result**: Start with ~150 lines, load additional context as needed, never frontload
thousands of lines.

## Date

2025-01-06 (Updated with three-tier architecture: 2025-01-06)
