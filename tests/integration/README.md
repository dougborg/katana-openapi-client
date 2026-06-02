# Live-integration tests (`tests/integration/`)

These tests exercise the **Python client** end-to-end against a real Katana **test
tenant** — auth, transport-layer resilience, pagination, and response parsing against
live responses rather than mocks. They are the client-side counterpart to the MCP smoke
tests in `katana_mcp_server/tests/smoke/`.

Part of the live test-environment epic —
[#837](https://github.com/dougborg/katana-openapi-client/issues/837), Phase 2. Phase 1
([#854](https://github.com/dougborg/katana-openapi-client/issues/854)) shipped the
`make_test_client()` helper these tests build on.

## Running them

```bash
uv run poe test-integration-live      # selects `-m live` (every test in this dir)
```

The suite **skips entirely** unless `KATANA_TEST_API_KEY` is set — so a bare
`uv run poe test-integration-live` on a fork, in CI without the secret, or on a laptop
that's never been configured is a green no-op, not a failure.

Set the key in `.env` (see `.env.example`) or export it:

```bash
export KATANA_TEST_API_KEY=...                       # test tenant, NOT prod
export KATANA_TEST_BASE_URL=https://api.katanamrp.com/v1   # optional; this is the default
```

## Safety model — why this can't hit prod

- **No prod fallback.** The `live_client` fixture calls
  [`make_test_client()`](../../katana_public_api_client/testing.py), which reads
  `KATANA_TEST_API_KEY` and **never** falls back to `KATANA_API_KEY`. A misconfigured
  environment skips; it does not silently exercise production.
- **The skip lives in the fixture, not the helper.** `make_test_client()` fails loud
  (raises `RuntimeError`) so non-test callers can't misuse it; the `live_client` fixture
  is the one place that turns that into `pytest.skip`.
- **Same URL, different key.** The test tenant lives on the same `api.katanamrp.com/v1`
  base URL as production — it is distinguished *only* by the API key. This is why the
  no-fallback rule matters: the URL alone won't save you.

## Read-only vs. write tests

`test_smoke_readonly.py` only touches `GET` endpoints, so there is nothing to clean up.
**Any test that creates, updates, or deletes tenant data must follow the SDT-tagging +
cleanup contract below** — otherwise the test tenant slowly fills with orphaned
artifacts.

### The SDT-tagging + cleanup contract

Reuse the ledger machinery in
[`scripts/spec_drift_verify.py`](../../scripts/spec_drift_verify.py) — the same pattern
the spec-drift probes use:

1. **Tag every created artifact** with the date-stamped `SDT-<date>` prefix so it's
   greppable in the Katana UI and unambiguously test-owned:

   ```python
   from scripts.spec_drift_verify import SDT_PREFIX, tagged, record_artifact

   name = f"[{SDT_PREFIX}] Smoke Material"   # or tagged("WIDGET-001") for a SKU
   ```

1. **Record it to the ledger immediately after the create succeeds** so cleanup can find
   it even if the test later crashes:

   ```python
   record_artifact(endpoint="/materials", entity_id=created.id, issue="#837")
   ```

1. **Clean up** by walking the ledger in reverse and issuing the matching `DELETE`s:

   ```bash
   uv run python scripts/spec_drift_verify.py cleanup
   ```

   Re-running cleanup is safe — already-deleted rows are skipped.

> **Note:** the `spec_drift_verify.py` ledger client authenticates with
> `KATANA_API_KEY`, because it predates this suite and targets the spec-drift probe
> tenant. When wiring write tests against the **test** tenant, point the cleanup at the
> same tenant your test wrote to — don't mix `KATANA_API_KEY` and `KATANA_TEST_API_KEY`
> artifacts in one ledger run.

## Adding a test

- Mark the module `pytestmark = [pytest.mark.integration, pytest.mark.asyncio]`.
- Take the `live_client` fixture; call generated endpoints with
  `await <endpoint>.asyncio_detailed(client=live_client, ...)`.
- Assert **structurally**, not exactly: the test tenant's data drifts, so check
  "authenticated + parsed into the right model" (`is_success`, `unwrap_as`,
  `unwrap_data`), never "there are exactly N rows".
