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

The live-test deadline includes fixture cleanup and allows for Katana's minute-long
rate-limit windows. It is intentionally longer than the unit-test deadline so a valid
retry wait does not interrupt deletion of a temporary resource.

The suite **skips entirely** unless `KATANA_TEST_API_KEY` is set — so a bare
`uv run poe test-integration-live` on a fork, in CI without the secret, or on a laptop
that's never been configured is a green no-op, not a failure.

Set the key in `.env` (see `.env.example`) or export it:

```bash
export KATANA_TEST_API_KEY=...                       # test tenant, NOT prod
export KATANA_TEST_BASE_URL=https://api.katanamrp.com/v1   # optional; this is the default
```

## Running in CI

The [`live-integration.yml`](../../.github/workflows/live-integration.yml) workflow runs
this suite on a nightly schedule, on manual dispatch, and on any PR carrying the
`needs-live-test` label (no automatic live run on every PR). It is **soft-fail** — a red
suite surfaces in the job summary + an uploaded artifact but does not block.

One-time setup by a repo owner — the workflow is a green no-op until the secret exists:

```bash
gh secret set KATANA_TEST_API_KEY            # test-tenant key
gh variable set KATANA_TEST_BASE_URL --body 'https://api.katanamrp.com/v1'  # optional
```

> **CI safety net.** It's worth also setting the repo's `KATANA_API_KEY` secret to the
> **same test-tenant key**. Nothing maps it to an env var today, but if a workflow ever
> accidentally constructs a default `KatanaClient()` (which reads `KATANA_API_KEY`), it
> then lands on the *test* tenant instead of production. The trade-off: don't assume
> `KATANA_API_KEY` means "production" in CI — in this repo's CI it points at the test
> tenant by design.

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

Use the `live_artifacts` fixture alongside `live_client`. Give each created parent a
unique `live_artifacts.tag("NAME")` identity and call `live_artifacts.record(...)`
immediately after creation, before further assertions:

```python
async def test_write(live_client, live_artifacts):
    response = await live_client.get_async_httpx_client().post(
        "/customers", json={"name": live_artifacts.tag("CUSTOMER")}
    )
    response.raise_for_status()
    customer = response.json()
    live_artifacts.record(
        endpoint="/customers", entity_id=customer["id"], issue="#your-issue"
    )
    # Assertions or further operations on this test-owned customer go here.
```

The fixture verifies `/factory` before yielding, records each resource with its
`factory_id` and base URL, and deletes resources in reverse creation order in a
`finally` block. Record children separately only when they need their own DELETE;
children that disappear with a tracked parent are covered by that parent's cleanup. Do
not register pre-existing tenant records.

Each fixture has a separate persistent JSONL file using the spec-drift ledger row
format. The files contain resource IDs and tenant fingerprints, never credentials. Set
`KATANA_TEST_LEDGER_DIR` to choose a directory; otherwise they live under
`katana-test-ledgers` in the system temporary directory. Successful deletions are marked
in the ledger. Failed deletions remain pending, fail the test teardown, and can be
retried with:

```bash
uv run python -m katana_public_api_client.testing_artifacts
# Or recover downloaded CI ledgers:
uv run python -m katana_public_api_client.testing_artifacts --ledger-dir ./ledgers
```

Recovery uses `make_test_client()` and refuses missing or mismatched tenant fingerprints
before deleting anything from a ledger. It never falls back to the production key. The
nightly/opt-in CI job retries cleanup after the tests and uploads ledger files with its
report so failed cleanup remains inspectable and recoverable.

The older `scripts/spec_drift_verify.py cleanup` command uses `KATANA_API_KEY`; use the
test-only recovery command above for this suite.

## Adding a test

- Mark the module
  `pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]`. The
  `live` marker is what `poe test-integration-live` selects and what
  `poe test-integration` excludes — keep it on every test in this directory.
- Take the `live_client` fixture; call generated endpoints with
  `await <endpoint>.asyncio_detailed(client=live_client, ...)`.
- Assert **structurally**, not exactly: the test tenant's data drifts, so check
  "authenticated + parsed into the right model" (`is_success`, `unwrap_as`,
  `unwrap_data`), never "there are exactly N rows".

### Reusable batch fixture

The batch quantity regression uses `fixtures/reusable_batch.json`, which records the
single SDT-tagged product and batch explicitly approved for retention. Katana has no
batch-delete endpoint. The test never creates another batch or product, verifies the
factory and API URL before writing, and deletes its temporary sales order through
`live_artifacts`. These fixture IDs are test data, not credentials.

For another test tenant, set `KATANA_TEST_BATCH_FIXTURE` to a JSON file with the same
fields describing an approved fixture in that tenant. A tenant mismatch fails before
any write; the test never falls back to production credentials or creates a replacement.
