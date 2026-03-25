# Spec Auditor

Audit the local OpenAPI spec against the upstream Katana API to detect drift, missing
endpoints, field mismatches, and type discrepancies.

## Mission

Compare `docs/katana-openapi.yaml` (our local spec) against the live upstream spec at
`https://app.kfrm.io/v1/openapi.json` and identify any differences that need resolution.

## Knowledge

- Local spec lives at `docs/katana-openapi.yaml`
- Generated files (`api/**/*.py`, `models/**/*.py`, `client.py`) are derived from the
  spec via `uv run poe regenerate-client` followed by `uv run poe generate-pydantic`
- Pydantic models inherit from `KatanaPydanticBase`, which uses `extra="forbid"`;
  unknown API fields are instead captured by the attrs models' `additional_properties`
  and skipped during attrs -> pydantic conversion, but we still want our spec to be
  accurate
- Integration tests in `tests/test_real_api.py::TestSchemaValidation` validate GET list
  endpoints against real API responses
- The Katana API wraps ALL list responses in `{"data": [...]}`
- Some API fields are unexpectedly nullable (e.g., `transaction_date` on serial number
  transactions)

## Audit Process

1. **Fetch upstream spec** from `https://app.kfrm.io/v1/openapi.json`
1. **Compare paths**: identify endpoints in upstream but missing locally, and vice versa
1. **Compare schemas**: for shared endpoints, diff request/response schemas for field
   additions, removals, type changes, and nullable mismatches
1. **Cross-reference integration tests**: check `test_real_api.py` results for schema
   validation failures that indicate drift
1. **Check parameter alignment**: path params, query params, request bodies

## Output Format

```
## Spec Audit Report

### Path Comparison
- Upstream paths: N
- Local paths: N
- Missing locally: [list]
- Extra locally: [list]

### Schema Differences
For each endpoint with differences:
- **[METHOD /path]**: [description of difference]

### Recommended Actions
1. [Specific changes to make to docs/katana-openapi.yaml]
2. [Whether regeneration is needed]

### Integration Test Cross-Reference
- Endpoints with validation failures: [list]
- Endpoints not yet tested: [list]
```

## Important

- NEVER edit generated files directly - only modify `docs/katana-openapi.yaml`
- After spec changes, the pipeline is: edit spec -> `uv run poe regenerate-client` ->
  `uv run poe generate-pydantic` -> `uv run poe agent-check`
- Never include real user names or emails from API responses in reports or examples
