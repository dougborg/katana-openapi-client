______________________________________________________________________

## description: 'Generate a new Architecture Decision Record (ADR) for documenting architectural choices'

# Create Architecture Decision Record

Generate a comprehensive Architecture Decision Record (ADR) following the project
template and standards.

## Instructions

1. **Find the next ADR number**:

   ```bash
   ls docs/adr/*.md | grep -o '[0-9]\{4\}' | sort -n | tail -1
   # Add 1 to get next number
   ```

1. **Copy the template**:

   ```bash
   NEXT_NUM=$(printf "%04d" $(($(ls docs/adr/*.md | grep -o '[0-9]\{4\}' | sort -n | tail -1) + 1)))
   cp docs/adr/template.md docs/adr/${NEXT_NUM}-{decision-title}.md
   ```

1. **Fill out the ADR** with:

   - **Status**: Proposed (or Accepted if already decided)
   - **Date**: Today's date (YYYY-MM-DD)
   - **Context**: Problem description and forces at play
   - **Decision**: What was decided and why
   - **Consequences**: Positive, negative, and neutral impacts
   - **Alternatives Considered**: Other options and why they weren't chosen
   - **References**: Related ADRs, documentation, code examples

1. **Update the ADR index**:

   - Edit `docs/adr/README.md`
   - Add entry to the index with title and brief description

1. **Format the files**:

   ```bash
   uv run poe format
   ```

## Template Structure

```markdown
# ADR-NNNN: [Decision Title in Title Case]

## Status

Proposed

Date: YYYY-MM-DD

## Context

[Describe the problem, background, and forces at play]

### Forces at Play

**Technological:**
- [Technical constraint or opportunity]

**User Experience:**
- [UX consideration]

**Project Goals:**
- [Project objective]

## Decision

[State the decision clearly and specifically]

### Implementation Details

[How this will be implemented]

## Consequences

### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Tradeoff 1]
- [Tradeoff 2]

### Neutral
- [Implication 1]

## Alternatives Considered

### Alternative 1: [Name]

**Pros:**
- [Pro 1]

**Cons:**
- [Con 1]

**Why not chosen:**
- [Reason]

## References

- [Related ADR or documentation]
```

## Success Criteria

- [ ] ADR number is sequential (no gaps)
- [ ] Status is set appropriately
- [ ] Context clearly explains the problem
- [ ] Decision is specific and actionable
- [ ] Consequences are realistic
- [ ] Alternatives are documented
- [ ] Index is updated
- [ ] Files are formatted with mdformat
