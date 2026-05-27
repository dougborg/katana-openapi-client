# OpenAPI Spec Authoring — Conventions and Pitfalls

The Katana client's source of truth is `docs/katana-openapi.yaml`. Two generator passes
turn the spec into Python:

1. `scripts/regenerate_client.py` — emits the attrs models, API methods, and `client.py`
   under `katana_public_api_client/`.
1. `scripts/generate_pydantic_models.py` — emits the pydantic mirrors (and the sibling
   `Cached<Name>` cache tables used by MCP).

A spec edit is therefore not just a doc change — it directly shapes the public client
surface and the cache schema. The rules below come from real failures where spec choices
broke downstream consumers.

Before editing the spec, audit upstream drift via the workflow in
[`docs/upstream-specs/README.md`](../../docs/upstream-specs/README.md):
`poe refresh-upstream-spec` → `poe audit-spec` → `poe validate-response-examples` →
`poe validate-examples`.

______________________________________________________________________

## The spec is OpenAPI 3.1 — use 3.1 conventions

`docs/katana-openapi.yaml` declares `openapi: 3.1.0`. Use 3.1 features rather than 3.0
work-arounds.

**`$ref` siblings are legal in 3.1.** Attach property metadata (especially
`description`) directly alongside `$ref`, **not** wrapped in `allOf: [{$ref: ...}]` (the
3.0 idiom — still legal but unnecessary; the spec has a few legacy cases).

Use `allOf` only for real composition (combining a `$ref` with additional properties),
not as a description-attacher.

______________________________________________________________________

## Property descriptions belong at the use-site, not the schema-definition site

When a property references a shared schema via `$ref`, put the property's `description`
as a sibling of the `$ref` so the description describes the *role of this field on this
object*. The shared schema's own `description` should describe the type/enum's general
meaning.

The two serve different audiences:

- **Schema-definition** describes what the type *is*.
- **Use-site** describes what the field's value *means in context*.

Example: `ManufacturingOrder.status` references `ManufacturingOrderStatus` and adds
"Current production status of the manufacturing order"; the schema itself just says
"Status of a manufacturing order."

The pydantic generator only emits `Annotated[..., Field(description=...)]` when the
description is at the use-site, so use-site descriptions are also what surfaces in the
generated client's IDE hovertext and generated docs. **A bare `$ref` drops the
description from generated pydantic** — avoid except when the schema's own description
is enough context for every caller (rare).

______________________________________________________________________

## List responses must use a `ListResponse` schema with a `data` array property

Katana wraps every GET list endpoint in `{"data": [...]}`. If the OpenAPI spec defines a
200 response as `type: array`, the generated parser iterates `response.json()` directly
— when the API returns the dict wrapper, iteration yields keys (strings) and
`Model.from_dict("data")` raises:

```
ValueError: dictionary update sequence element #0 has length 1; 2 is required
```

Always define a proper `MyListResponse` schema (`type: object`,
`properties.data: {type: array, items: {$ref: ...}}`) and reference it from the
operation. The only documented exception is `/user_info`, which returns a flat object,
not wrapped.

Test fixtures and mocks must also honor this — never put a raw array in a list mock.

______________________________________________________________________

## Generator/schema edits must commit the regen in the same PR

Whenever you edit a generator script (`scripts/generate_pydantic_models.py`,
`scripts/regenerate_client.py`) **or** the OpenAPI spec (`docs/katana-openapi.yaml`),
run the regen, run `uv run poe check` (or at minimum `agent-check` + `uv run poe test`),
and commit the regenerated output **in the same PR**. The input and its output stay
locked together at every commit so the cause-and-effect chain is reviewable.

- Pushing a generator/spec change without its regen leaves CI green-but-stale until the
  next time someone runs the generator.
- Pushing regen output without the input change drifts in the other direction.

Note the generated-file impact in the PR description (e.g., "byte-identical except X" or
list affected files).

### Breaking-change marker

When the regen drops a previously-public class (e.g., a `StrEnum` deduped into a
sibling) or narrows a field's type, the commit must use the breaking-change marker
(`feat(client)!:` / `fix(client)!:`) with a `BREAKING CHANGE:` footer naming the
affected symbol — see
[`.github/agents/guides/shared/COMMIT_STANDARDS.md`](../../.github/agents/guides/shared/COMMIT_STANDARDS.md)
"Schema and Generator Changes" for the full rule.

______________________________________________________________________

## Real names and emails from live API responses must never enter the repo

When testing against the live Katana API and incorporating response data into the spec,
examples, or test fixtures, replace real names/emails with generic placeholders
(`Jane Doe`, `jane.doe@example.com`, etc.). Privacy concern — real user data from
production accounts should not be committed.

______________________________________________________________________

## POST create endpoints return `200`, not `201`

Katana's convention across virtually every create endpoint is to return HTTP **200** on
success — not the REST-orthodox **201**. Authoring or copy-pasting `"201":` for a new
`post:` block is a recurring footgun: the generated `_parse_response` only handles the
documented status code, so when Katana actually returns 200 the parser falls through to
"unknown status", leaves `response.parsed = None`, and `unwrap_as` raises
`UnexpectedResponse` — *even though the mutation landed server-side*. The bug looks like
a failure to the caller and invites a destructive retry.

Verified live (`make_test_client()` probe, 2026-05-27):

- `POST /sales_order_fulfillments` → 200
- `POST /stock_transfers` → 200
- `POST /sales_return_rows` → 200
- `POST /inventory_reorder_points` → 200

Pinned by
`tests/test_openapi_specification.py::test_create_endpoint_success_status_codes`.

Not yet live-verified (test tenant has no fixtures to probe against; fix when verified):
`POST /outsourced_purchase_order_recipe_rows` still declares 201 and is almost certainly
the same drift.

If you genuinely encounter a Katana create endpoint that returns 201 (none confirmed to
date), accept *both* by declaring `"200"` and `"201"` in the same `responses:` map
pointing at the same schema — this future-proofs against Katana flipping the status code
and is what the generator handles cleanly.

______________________________________________________________________

## Fix bugs at the client/generator layer when the root cause lives there

The Katana client (`katana_public_api_client`) is a published, standalone package.
Third-party Python users hit the same bugs we hit in MCP. When a bug surfaces in
`katana_mcp_server/.../typed_cache/sync.py`, in a foundation tool, or in a helper but
originates in generated client code (attrs, pydantic, `from_attrs`, `Cached*` schemas),
apply the fix to the **generator or spec** — not the consumer.

Test: *"would a standalone client user hit this bug?"* If yes, fix it in the client.

Examples:

- `Pydantic*.from_attrs` raising on `{}` from Katana → fix `from_attrs` codegen, not
  `_attrs_*_to_cached`.
- `Column(JSON)` failing to serialize a pydantic instance → fix `inject_json_columns` in
  `scripts/generate_pydantic_models.py`, not `sync.py`.
- Missing enum value → patch spec + regenerate, not enum-tolerant deserialization
  downstream.
