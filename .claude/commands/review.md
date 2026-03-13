# Code Review

Review the current branch's changes against main for quality, correctness, and project
standards.

## Review Process

1. Identify the diff: `git diff main...HEAD`
1. Read every changed file in full context (not just the diff)
1. Run `uv run poe check` to verify everything passes
1. Produce the structured review below

## Output Format

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

- [ ] Generated files not manually edited; pydantic regenerated if client was
- [ ] Resilience at transport layer, not wrapping API methods (ADR-001)
- [ ] Full type annotations; UNSET/response handling per CLAUDE.md patterns
- [ ] New functionality has tests (success + error paths, 87%+ coverage)
- [ ] Public APIs have docstrings; ADR created for architectural decisions

## Verification

Before approving, confirm `uv run poe check` passes clean. If it doesn't, list the
failures as `[BLOCKING]` issues.

## Self-Improvement

If the review reveals a pattern worth codifying (new anti-pattern, missing convention,
or a pitfall that tripped up the author), update CLAUDE.md so future work benefits.
