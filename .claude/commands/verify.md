# Verify Implementation

Skeptically validate the current state of the codebase. Do not accept claims at face
value - run commands, read files, and confirm everything works.

## Verification Checklist

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

### 5. Generated Files Intact

- [ ] Generated files not manually edited (see CLAUDE.md "File Rules")
- [ ] If client was regenerated, pydantic models were also regenerated

### 6. Coverage Maintained

- [ ] Run `uv run poe test-coverage` and check core logic is at 87%+
- [ ] New code has test coverage for success and error paths

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

**Be skeptical.** If something "should work," verify it actually does. Run the command.
Read the file. Check the output. Trust evidence, not assumptions.

## Self-Improvement

If verification reveals a gap in project instructions (CLAUDE.md, agent guides, or
command files), fix the instructions as part of your verification. The goal is that
future work doesn't produce the same kind of failure again.
