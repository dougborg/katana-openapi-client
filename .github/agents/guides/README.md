# Agent guides — shared reference material

This directory holds reference documentation that any contributor or agent (Claude
Code, Copilot, etc.) can pull from on demand. The split is deliberate: the active
agent harness lives at `.claude/skills/` (workflows) and `.claude/agents/`
(delegated sub-agents); these guides are evergreen reference content that several
of those agents share.

For the canonical entry points, see:

- **[CLAUDE.md](../../../CLAUDE.md)** — Claude Code's session-level guidance
- **`.claude/skills/`** — invokable workflows (`/pre-commit`, `/review`, `/open-pr`,
  …)
- **`.claude/agents/`** — delegated sub-agents (`code-reviewer`, `verifier`,
  `domain-advisor`, …)
- **[harness-kit](https://github.com/dougborg/harness-kit)** — the plugin powering
  the `harness-kit:*` skills

## Layout

### `shared/` — patterns referenced by everything

- **[VALIDATION_TIERS.md](shared/VALIDATION_TIERS.md)** — `quick-check` /
  `agent-check` / `check` / `full-check` poe tiers and when to use each
- **[COMMIT_STANDARDS.md](shared/COMMIT_STANDARDS.md)** — conventional-commit format,
  monorepo scopes (`feat(client):` / `feat(mcp):`), and the schema/generator
  breaking-change rule
- **[FILE_ORGANIZATION.md](shared/FILE_ORGANIZATION.md)** — generated vs editable
  files
- **[ARCHITECTURE_QUICK_REF.md](shared/ARCHITECTURE_QUICK_REF.md)** — ADR summaries
  and the transport-layer resilience pattern

### `devops/` — release / CI / dependency workflows

- **[CI_DEBUGGING.md](devops/CI_DEBUGGING.md)** — GitHub Actions troubleshooting
- **[DEPENDENCY_UPDATES.md](devops/DEPENDENCY_UPDATES.md)** — uv dependency
  management
- **[RELEASE_PROCESS.md](devops/RELEASE_PROCESS.md)** — semantic-release workflow
- **[CLIENT_REGENERATION.md](devops/CLIENT_REGENERATION.md)** — OpenAPI client
  regeneration

### `plan/` — issue and roadmap patterns

- **[PLANNING_PROCESS.md](plan/PLANNING_PROCESS.md)** — step-by-step planning
  methodology
- **[ISSUE_TEMPLATES.md](plan/ISSUE_TEMPLATES.md)** — structured issue format
- **[EFFORT_ESTIMATION.md](plan/EFFORT_ESTIMATION.md)** — complexity heuristics

## Maintenance

When the canonical reference for a topic moves into `CLAUDE.md` or a `harness-kit:*`
skill, delete the duplicate guide here rather than letting both drift. Git history
preserves what was removed.
