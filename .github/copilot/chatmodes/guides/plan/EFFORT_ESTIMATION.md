# Effort Estimation Guide

This guide provides detailed guidance on estimating effort for tasks using our
three-tier priority system.

## Quick Reference

| Label         | Time      | Complexity | When to Use                                   |
| ------------- | --------- | ---------- | --------------------------------------------- |
| **p1-high**   | 1-2 days  | High       | Large features, refactoring, breaking changes |
| **p2-medium** | 4-8 hours | Moderate   | New tools, moderate features, standard bugs   |
| **p3-low**    | 1-3 hours | Low        | Small utilities, docs, simple fixes           |

______________________________________________________________________

## p1-high (1-2 Days)

### Time: 8-16 hours of focused work

### Characteristics

**Code Volume:**

- 500+ lines of new/changed code
- 5+ files affected
- Multiple modules touched

**Complexity:**

- Complex business logic
- Multi-step workflows
- Integration across components
- Error handling for many cases

**Testing:**

- Comprehensive test suite
- Unit + integration tests
- Edge case coverage
- Manual testing scenarios

**Documentation:**

- Significant user docs
- API reference updates
- Examples/cookbook
- ADR creation (if architectural)

**Review:**

- Multiple review rounds expected
- Architectural considerations
- Performance implications
- Security review

### Examples

**Large Features:**

```markdown
feat(client): implement domain helper classes

Scope:
- Base domain class pattern
- Products domain (5 methods)
- Orders domain (7 methods)
- Inventory domain (4 methods)
- Comprehensive test suite
- User guide with examples

Estimate: p1-high (12-16 hours)
```

**Breaking Changes:**

```markdown
feat(client)!: migrate from attrs to Pydantic

Scope:
- Convert 15+ model classes
- Update all imports
- Maintain backward compatibility
- Migration guide
- ADR documentation
- Extensive testing

Estimate: p1-high (16+ hours, split into phases)
```

**Complex Refactoring:**

```markdown
refactor(mcp): restructure tool organization

Scope:
- Move 10 tools to new structure
- Update all imports
- Refactor tests
- Update documentation
- Ensure no regressions

Estimate: p1-high (10-12 hours)
```

### Estimation Factors

**Add time for:**

- 🔴 Unfamiliar territory (+25%)
- 🔴 Cross-package changes (+20%)
- 🔴 Breaking changes (+30%)
- 🔴 Performance critical (+25%)
- 🔴 Security sensitive (+30%)

**Reduce time for:**

- 🟢 Clear pattern to follow (-20%)
- 🟢 Similar work done before (-15%)
- 🟢 Well-documented area (-10%)

______________________________________________________________________

## p2-medium (4-8 Hours)

### Time: Half day to full day of work

### Characteristics

**Code Volume:**

- 200-500 lines of new/changed code
- 2-5 files affected
- Single module or feature area

**Complexity:**

- Moderate business logic
- Standard patterns
- Some edge cases
- Typical error handling

**Testing:**

- Standard test coverage
- Unit tests required
- Integration test (1-2 scenarios)
- Basic manual testing

**Documentation:**

- Function/method docstrings
- README updates
- Simple examples
- No major doc overhaul

**Review:**

- 1-2 review rounds
- Standard code review
- No major architecture changes

### Examples

**New MCP Tools:**

```markdown
feat(mcp): add sales order creation tool

Scope:
- 1 new tool with preview/confirm
- Input validation
- Error handling
- Unit + integration tests
- Docstring with examples

Estimate: p2-medium (5-6 hours)
```

**Standard Bug Fixes:**

```markdown
fix(client): handle network timeout errors

Scope:
- Add timeout handling
- Retry logic for timeouts
- Test timeout scenarios
- Update error messages

Estimate: p2-medium (4-5 hours)
```

**Moderate Features:**

```markdown
feat(client): add batch operations helper

Scope:
- BatchOperations class
- 3-4 helper methods
- Error aggregation
- Tests for each method
- Usage examples

Estimate: p2-medium (6-8 hours)
```

### Estimation Factors

**Add time for:**

- 🟡 New pattern (not used before) (+20%)
- 🟡 External API integration (+25%)
- 🟡 Complex validation (+15%)

**Reduce time for:**

- 🟢 Copy from existing pattern (-25%)
- 🟢 Simple CRUD operation (-20%)
- 🟢 Well-tested area (-15%)

______________________________________________________________________

## p3-low (1-3 Hours)

### Time: Quick task, can complete in one sitting

### Characteristics

**Code Volume:**

- \<200 lines of new/changed code
- 1-2 files affected
- Localized changes

**Complexity:**

- Simple, straightforward logic
- Clear pattern to follow
- Minimal edge cases
- Basic error handling

**Testing:**

- Minimal tests
- 1-2 unit tests
- Manual verification
- No integration tests needed

**Documentation:**

- Docstring updates
- Minor README changes
- Quick examples

**Review:**

- Single review pass
- Straightforward approval
- No controversy expected

### Examples

**Documentation:**

```markdown
docs(mcp): add inventory tool cookbook entry

Scope:
- 1 new cookbook entry
- 2-3 usage examples
- Update table of contents
- Review for clarity

Estimate: p3-low (2 hours)
```

**Simple Utilities:**

```markdown
feat(client): add is_success() helper

Scope:
- 1 small utility function
- 2-3 unit tests
- Docstring
- Update utilities docs

Estimate: p3-low (1-2 hours)
```

**Minor Fixes:**

```markdown
fix(mcp): typo in error message

Scope:
- Fix typo in 1 error message
- Update corresponding test
- Verify error still raised correctly

Estimate: p3-low (30 min)
```

### Estimation Factors

**Add time for:**

- 🟡 Unfamiliar codebase area (+30%)
- 🟡 Needs research (+50%)

**Reduce time for:**

- 🟢 Trivial change (-50%)
- 🟢 Copy-paste with tweaks (-40%)

______________________________________________________________________

## Estimation Process

### Step 1: Understand Scope

Ask yourself:

- How many files will I touch?
- How many lines of code?
- What's the complexity level?
- Are there similar examples?

### Step 2: Break Down Work

List all activities:

```markdown
Implementation:
- Write core logic (2h)
- Add error handling (1h)
- Input validation (30m)

Testing:
- Unit tests (1h)
- Integration test (1h)
- Manual testing (30m)

Documentation:
- Docstrings (30m)
- README update (30m)
- Examples (30m)

Review & Iteration:
- Address feedback (1h)
- Polish and cleanup (30m)

Total: ~8 hours → p2-medium
```

### Step 3: Apply Factors

```markdown
Base estimate: 8 hours
+ Unfamiliar pattern: +1.5h
+ Cross-package changes: +1h
- Clear examples exist: -1h
= Final: 9.5 hours → p1-high (bump up)
```

### Step 4: Add Buffer

General rule: Add 20-30% buffer for unknowns

- Research time
- Unexpected issues
- Review iterations
- Documentation polish

### Step 5: Round to Label

```markdown
Calculated: 9.5 hours
Buffer (25%): +2.4 hours
Total: ~12 hours
→ p1-high (1-2 days)
```

______________________________________________________________________

## Common Estimation Mistakes

### ⚠️ Underestimating Testing

**Mistake:**

```markdown
Implementation: 4h
Testing: 30m  ← Too low!
Total: 4.5h → p2-medium
```

**Reality:**

```markdown
Implementation: 4h
Testing:
- Write tests: 1.5h
- Debug failures: 1h
- Edge cases: 1h
Total: 7.5h → still p2-medium but more accurate
```

**Rule:** Testing usually takes 30-50% of implementation time.

### ⚠️ Forgetting Documentation

**Mistake:**

```markdown
Code: 6h
Tests: 2h
Total: 8h → p2-medium
(Forgot docs!)
```

**Reality:**

```markdown
Code: 6h
Tests: 2h
Docs:
- Docstrings: 30m
- README: 30m
- Examples: 1h
Total: 10h → p1-high
```

**Rule:** Always include documentation time.

### ⚠️ Ignoring Review Iterations

**Mistake:**

```markdown
First-pass implementation: 8h
→ p2-medium
(Assumes perfect first try!)
```

**Reality:**

```markdown
Implementation: 8h
First review: feedback
Address feedback: 2h
Second review: minor changes
Polish: 1h
Total: 11h → p1-high
```

**Rule:** Add 20-30% for review and iteration.

### ⚠️ Not Accounting for Context Switching

**Mistake:**

```markdown
Pure coding time: 4h
→ p2-medium
```

**Reality:**

```markdown
Set up environment: 30m
Understand existing code: 1h
Actual coding: 4h
Debug issues: 1h
Final validation: 30m
Total: 7h → p2-medium (but fuller estimate)
```

**Rule:** Include ramp-up and validation time.

______________________________________________________________________

## Calibration Examples

### Example 1: New MCP Tool

**Initial estimate:**

- Code: 3h
- Tests: 1h
- Docs: 30m
- Total: 4.5h → p2-medium

**Factors:**

- Similar to existing tool (-20%): -54m
- New API endpoint (+15%): +41m
- Adjusted: 4.6h → p2-medium ✓

**Actual:** 5h → Good estimate!

______________________________________________________________________

### Example 2: Refactoring

**Initial estimate:**

- Refactor: 4h
- Update tests: 1h
- Total: 5h → p2-medium

**Factors:**

- 8 files affected (more than thought)
- Add 50%: +2.5h
- Adjusted: 7.5h → p2-medium (high end)

**Reality check:**

- Should this be p1-high? (borderline)
- Decision: Keep p2-medium but note it's high end

**Actual:** 8h → Accurate!

______________________________________________________________________

### Example 3: Breaking Change

**Initial estimate:**

- Implementation: 8h → p1-high

**Reality check:**

- Need ADR: +2h
- Need migration guide: +2h
- Need backward compat: +3h
- Multiple review rounds: +2h
- Adjusted: 17h → p1-high (split into 2 issues!)

**Better approach:**

```markdown
Issue #1: Foundation + ADR (p2-medium, 6h)
Issue #2: Implementation (p1-high, 8h)
Issue #3: Migration + docs (p2-medium, 4h)
```

______________________________________________________________________

## Estimation Checklist

Before finalizing estimate, check:

- [ ] Counted all files to be touched?
- [ ] Included test writing time?
- [ ] Included test debugging time?
- [ ] Included documentation time?
- [ ] Included review iteration time?
- [ ] Applied complexity factors?
- [ ] Added buffer for unknowns (20-30%)?
- [ ] Rounded to appropriate label?
- [ ] Considered splitting if > 2 days?

______________________________________________________________________

## When to Split

### Too Large (> 2 Days / > 16 Hours)

**Split by phases:**

```markdown
Original: p1-high (24h) - TOO BIG!

Split:
- Phase 1: Foundation (p1-high, 8h)
- Phase 2: Core (p1-high, 10h)
- Phase 3: Polish (p2-medium, 6h)
```

**Split by component:**

```markdown
Original: Implement 5 new tools (p1-high, 30h) - TOO BIG!

Split:
- Tool 1 + 2 (p1-high, 12h)
- Tool 3 + 4 (p1-high, 12h)
- Tool 5 + docs (p2-medium, 6h)
```

### Rule of Thumb

- p1-high: Max 16 hours (2 days)
- p2-medium: Max 8 hours (1 day)
- p3-low: Max 3 hours

If exceeds max → Split into multiple issues.

______________________________________________________________________

## Summary

**Estimation formula:**

```
Time = Implementation + Testing + Docs + Review + Buffer

Implementation: Core coding time
Testing: 30-50% of implementation
Docs: 10-20% of implementation
Review: 20-30% of total
Buffer: 20-30% for unknowns
```

**Quick decision tree:**

```
> 8 hours? → p1-high
4-8 hours? → p2-medium
< 4 hours? → p3-low
```

**Key principles:**

1. ✅ Be realistic, not optimistic
1. ✅ Include all activities (code, test, doc, review)
1. ✅ Apply complexity factors
1. ✅ Add buffer for unknowns
1. ✅ Split large work (> 2 days)
1. ✅ Learn from past estimates

**Remember:** It's better to overestimate and finish early than underestimate and miss
deadlines!
