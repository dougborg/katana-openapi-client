# Code Review

Review the current branch's changes against main for quality, correctness, and project
standards.

## Review Process

### Step 1: Initial Classification

Before diving into details, classify the change:

- **Type**: Feature / Bug Fix / Refactor / Spec Change / Config / Docs
- **Risk**: Low (cosmetic, docs) / Medium (new feature, test changes) / High (spec
  changes, transport layer, auth, breaking changes)
- **Affected packages**: client / mcp / typescript / cross-cutting

This classification guides where to focus review attention.

### Step 2: Full Context Review

1. Identify the diff: `git diff main...HEAD`
1. Read every changed file in full context (not just the diff lines)
1. Check surrounding code for broken assumptions - changes may invalidate logic in
   adjacent functions or callers that aren't in the diff
1. For every function whose signature or behavior changed, run `LSP findReferences` (or
   `LSP incomingCalls`) to enumerate callers. Read each caller and confirm it still
   works with the new semantics. This catches ripple effects that a diff-only review
   misses — a diff only shows what changed, not what depends on it.
1. Run `uv run poe check` to verify everything passes
1. Produce the structured review below

## Review Dimensions (Priority Order)

Focus review effort in this order - higher priorities get more scrutiny:

1. **Correctness** - Does the code do what it claims? Edge cases handled? Bugs?
1. **Security** - Input validation, auth checks, no secrets in code, safe API handling
1. **Architecture** - Respects generated file boundaries, transport-layer resilience
   pattern, UNSET/response helper conventions
1. **Completeness** - All requirements met, tests cover success + error paths, docs
   updated
1. **Readability** - Clear naming, appropriate abstractions, maintainable
1. **Performance** - Efficient patterns, no N+1 queries, appropriate pagination

## Output Format

### Classification

Type, risk level, and affected packages (from Step 1).

### Summary

One paragraph describing what the changes do, their scope, and overall assessment.

### Strengths

Bullet list of things done well - good patterns, clean code, thorough tests.

### Issues

Each issue gets a severity tag:

- **[BLOCKING]** - Must fix before merge. Bugs, security issues, broken tests,
  architecture violations.
- **[SUGGESTION]** - Recommended improvement. Better patterns, missing edge cases,
  unclear naming.
- **[NITPICK]** - Minor style or preference. Take it or leave it.

Format each issue as:

```
**[SEVERITY]** `file:line` - Brief description
Explanation of the problem and suggested fix.
```

### Questions

Anything unclear about intent, design choices, or missing context. Questions are not
criticisms.

## Project-Specific Checklist

Verify these for every review (see CLAUDE.md for details on each):

- [ ] Generated files not manually edited; pydantic models regenerated if the OpenAPI
  client was regenerated
- [ ] Resilience at transport layer, not wrapping API methods
  ([ADR-001](katana_public_api_client/docs/adr/0001-transport-layer-resilience.md))
- [ ] Full type annotations; UNSET/response handling per CLAUDE.md patterns
- [ ] New functionality has tests (success + error paths, 87%+ coverage)
- [ ] Public APIs have docstrings; ADR created for architectural decisions

## Verification

Before approving, confirm `uv run poe check` passes clean. If it doesn't, list the
failures as `[BLOCKING]` issues.

## Self-Improvement

If the review reveals a pattern worth codifying (new anti-pattern, missing convention,
or a pitfall that tripped up the author), update CLAUDE.md so future work benefits.
