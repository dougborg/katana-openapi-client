# Verify Implementation

**Be skeptical.** Do not accept claims at face value. Do not trust that code works
because it looks right. Run every command. Read every file. Check every output. Trust
evidence, not assumptions. If something "should work," prove it.

## Verification Checklist

### 0. Exercise the Feature

Before checking infrastructure, actually use the feature that was implemented:

- If a new MCP tool was added: invoke it through the test harness or MCP inspector
- If a new API method was added: make a test call (or verify via integration test)
- If a bug was fixed: reproduce the original scenario and confirm it no longer fails
- If behavior changed: demonstrate both old and new behavior

This step catches "compiles but doesn't work" failures that test suites sometimes miss.

### 1. Code Exists

- [ ] All claimed files are present (not just planned or mentioned)
- [ ] No stub implementations or TODO placeholders left behind
- [ ] All imports resolve to real modules

### 2. Code Works

- [ ] `uv run poe agent-check` passes (format + lint + type check)
- [ ] `uv run poe test` passes (all tests green)
- [ ] No new warnings introduced

### 3. Code Is Complete

- [ ] All requirements from the issue/task are addressed
- [ ] Edge cases handled (empty inputs, error conditions, None/UNSET)
- [ ] Error handling is in place with appropriate exception types
- [ ] No partial implementations or "will do later" gaps

### 4. Code Is Integrated

- [ ] New code is imported and used where expected
- [ ] No broken references or dangling imports
- [ ] If new functions were added, they are called from the right places
- [ ] If tests were added, they test the actual implementation (not mocks of it)

**Use `LSP findReferences`** on each new public function/class to prove it is actually
wired up — not just imported and sitting there. Zero references to a new symbol means
something is unfinished. Grep can miss dynamic dispatch that the LSP catches via the
real type graph.

### 5. Generated Files Intact

- [ ] Generated files not manually edited (see CLAUDE.md "File Rules")
- [ ] If client was regenerated, pydantic models were also regenerated

### 6. Coverage Maintained

- [ ] Run `uv run poe test-coverage` and check core logic is at 87%+
- [ ] New code has test coverage for success and error paths

### 7. Regression Check

- [ ] Confirm the test output from step 2 ran the full suite (not a subset)
- [ ] Compare test count against expectations - no tests accidentally deleted or skipped
- [ ] If coverage decreased from step 6, identify what lost coverage and why

## Process

1. Read the task description or issue to understand what was supposed to be done
1. Walk through each checklist item, running real commands and reading real files
1. For each item, mark as VERIFIED or FAILED with evidence
1. Produce the report below

## Report Format

```
## Verification Report

### Status: [PASS | FAIL]

### Verified
- [item]: [evidence - command output, file contents, etc.]

### Failed
- [item]: [what's wrong and what needs to be fixed]

### Recommendations
- [any improvements noticed during verification]
```

## Key Principle

The skeptical framing at the top of this file IS the key principle. Every checklist item
must be verified with real evidence (command output, file contents, test results). A
claim without evidence is not verified.

## Self-Improvement

If verification reveals a gap in project instructions (CLAUDE.md, agent guides, or
command files), fix the instructions as part of your verification. The goal is that
future work doesn't produce the same kind of failure again.
