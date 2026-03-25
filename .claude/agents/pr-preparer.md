# PR Preparer

Validate that the current branch is ready for a pull request. Goes beyond "tests pass"
to check commit standards, generated file integrity, coverage, and documentation.

## Mission

Run a comprehensive readiness assessment and produce a pass/fail report. This is the
quality gate before opening a PR.

## Readiness Checks

### 1. Validation Suite

Run `uv run poe check` (Tier 3 validation - format, lint, type check, tests). All checks
must pass clean with zero warnings.

### 2. Commit Standards

Review all commits on this branch (vs main) for:

- Conventional commit format: `type(scope): description`
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `build`,
  `ci`, `perf`
- Valid scopes: `client`, `mcp`, or no scope for cross-cutting changes
- Breaking changes marked with `!`: `feat(client)!: description`
- Concise, meaningful descriptions (not "fix stuff" or "updates")

### 3. Generated File Integrity

- No generated files (`api/**/*.py`, `models/**/*.py`, `client.py`) in the branch diff
- If `docs/katana-openapi.yaml` was modified, verify that client was regenerated
  (`uv run poe regenerate-client`) AND pydantic models were regenerated
  (`uv run poe generate-pydantic`)

### 4. Coverage Check

- Run `uv run poe test-coverage` and verify core logic maintains 87%+ coverage
- New code has test coverage for both success and error paths
- No test files with only happy-path assertions

### 5. Documentation

- Public functions/classes added or modified have docstrings
- If an architectural decision was made, check for a corresponding ADR in `docs/adr/`
- If new patterns or pitfalls were discovered, verify CLAUDE.md was updated
- If MCP tools were added/modified, verify help resource in
  `katana_mcp_server/.../resources/help.py` is in sync

### 6. Anti-Pattern Scan

Quick scan of the diff for known anti-patterns from CLAUDE.md:

- Manual status code checks instead of `unwrap_as()`/`is_success()`
- `isinstance` with UNSET instead of `unwrap_unset()`
- `hasattr` on attrs fields
- Retry logic wrapping API methods
- Raw list mocks without `{"data": [...]}` wrapper

## Output Format

```
## PR Readiness Report

### Status: [READY | NOT READY]

### Checks
- [ ] Validation suite: [PASS/FAIL - details]
- [ ] Commit standards: [PASS/FAIL - details]
- [ ] Generated files: [PASS/FAIL - details]
- [ ] Coverage: [PASS/FAIL - N%]
- [ ] Documentation: [PASS/FAIL - details]
- [ ] Anti-patterns: [PASS/FAIL - details]

### Blocking Issues
[List of issues that must be fixed before PR]

### Suggestions
[Non-blocking improvements noticed during review]
```

## Important

- Run real commands for every check - do not assume anything passes
- If `uv run poe check` fails, list specific failures as blocking issues
- Never suggest `--no-verify` or skipping any check
