# Repository guidance

## Package boundaries

- `katana_public_api_client/`: Python API client. Keep retries, rate limiting, and
  pagination in the shared httpx transport layer rather than individual endpoints.
- `katana_mcp_server/`: MCP server, a separate Python workspace package with its own
  dependencies, tests, and documentation.
- `packages/katana-client/`: TypeScript client with its own npm tooling and lockfile.
- `docs/katana-openapi.yaml`: shared source for all generated clients.

## Setup

Use the Python version in `.python-version`; the project requires Python >=3.12. Run
Python commands from the repository root through `uv`.

```bash
uv sync --all-extras
uv run pre-commit install
uv run playwright install chromium  # Required for browser tests
```

Reinstall pre-commit hooks in each new worktree. For TypeScript changes or client
regeneration, use the Node requirements and the pnpm version pinned by `packageManager`
in `packages/katana-client/package.json`, then run:

```bash
pnpm --dir packages/katana-client install --frozen-lockfile
```

Local unit tests do not need live API credentials. Configure live-test credentials only
when needed, using `.env.example` as a reference; never overwrite an existing `.env` or
commit credentials.

## Validation

`[tool.poe.tasks]` in `pyproject.toml` is the source of truth for commands.

| Command                   | Use                                                                                                                             |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `uv run poe quick-check`  | During development: formatting and Ruff                                                                                         |
| `uv run poe agent-check`  | Before committing: quick checks plus ty                                                                                         |
| `uv run poe check`        | Before opening a PR: formatting, full lint (including ty and pyright), spec examples, strict spec audit, unit and browser tests |
| `uv run poe full-check`   | Before requesting review: PR checks plus docs build                                                                             |
| `uv run poe test`         | Default parallel tests; excludes docs, schema validation, integration, and browser tests                                        |
| `uv run poe test-browser` | Sequential browser rendering tests                                                                                              |
| `uv run poe test-schema`  | Schema validation tests                                                                                                         |

Run tests relevant to changed behavior alongside the appropriate validation tier. For
TypeScript changes, run `pnpm --dir packages/katana-client run lint`,
`pnpm --dir packages/katana-client run typecheck`, and
`pnpm --dir packages/katana-client test`.

Let regeneration and browser/docs checks finish; they can take minutes. Report
environment or network blockers explicitly. Fix failures rather than adding error
suppressions, exclusions, or skips to hide them, and do not bypass commit hooks.

## Generated files

Fix the spec or generator rather than hand-editing generated output. Under
`katana_public_api_client/`, generated paths include `api/`, `models/`, `client.py`,
`client_types.py`, `errors.py`, `py.typed`, `__init__.py`,
`models_pydantic/_generated/`, and `models_pydantic/_auto_registry.py`.
`packages/katana-client/src/generated/` is also generated. The remaining Pydantic
infrastructure is hand-maintained.

After changing the shared spec, run `uv run poe regenerate-all` and include all
generated changes. This requires the TypeScript dependencies above. Generator scripts
define the exact generated/preserved boundary when documentation disagrees. See
[spec authoring](katana_public_api_client/docs/spec-authoring.md) and
[contribution guidance](docs/CONTRIBUTING.md).

## Live-test safeguards

Tests and probes that contact a live tenant must use `make_test_client()` from
`katana_public_api_client/testing.py`. It requires `KATANA_TEST_API_KEY`, accepts
optional `KATANA_TEST_BASE_URL`, and must never fall back to `KATANA_API_KEY`. The test
tenant can share production's URL; the API key determines the tenant. Missing
credentials raise in the helper; fixtures handle graceful skipping.

Use `uv run poe test-integration-live` for live client tests and
`uv run poe test-smoke-mcp` for live MCP smoke tests. For tests that mutate tenant data,
follow the tagging, tenant verification, artifact recording, and cleanup contract in
[tests/integration/README.md](tests/integration/README.md). Use its test-only ledger
recovery command for failed cleanup.

## Further guidance

Read documentation relevant to the task:

- [Python client guide](katana_public_api_client/docs/guide.md): response handling and
  client usage.
- [MCP documentation](katana_mcp_server/docs/README.md),
  [Prefab UI](katana_mcp_server/docs/prefab/README.md), and
  [typed cache](katana_mcp_server/docs/typed_cache/README.md): server behavior.
- [Upstream specs](docs/upstream-specs/README.md): drift audits and override rules.
- [Contributing](docs/CONTRIBUTING.md) and [release process](docs/RELEASE.md): coding,
  documentation, and commit conventions. Use conventional commits such as
  `fix(client):`, `feat(mcp):`, and `docs:`; mark breaking changes with `!`.
