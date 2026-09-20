# Custom-field read contracts

Issue [#782](https://github.com/dougborg/katana-openapi-client/issues/782) reported
list/detail differences in May 2026. The September 20, 2026 audit found that the
current schema already accepts omitted fields; no list/detail DTO split or
requiredness change is needed.

## Effective local contracts

The audit follows local `$ref` and `allOf` inheritance in
[`docs/katana-openapi.yaml`](../../docs/katana-openapi.yaml), including required
properties inherited from base schemas.

| Read schema                              | Top-level `custom_fields`                                                       |
| ---------------------------------------- | ------------------------------------------------------------------------------- |
| Product, Material, Service               | Undeclared, not required; the schema permits additional properties              |
| Variant, VariantResponse, ServiceVariant | Optional `array \| null`, containing legacy `{field_name, field_value}` objects |

Product and Material contain nested Variant records; Service contains nested
ServiceVariant records. The variant members use the typed legacy array contract.
Sales-order UUID/value maps are a separate contract and do not establish
map-valued variant responses.

Generated Python attrs models retain omitted variant fields as `UNSET`, explicit
null as `None`, and empty/nonempty arrays as lists. `to_dict()` preserves each
state. Undeclared top-level item fields, if returned, survive in attrs
`additional_properties` and serialize back unchanged.

Generated Pydantic variant models accept the same nullable arrays. Omitted and
explicit-null values both read as `None`, but `model_fields_set` distinguishes
them; `model_dump(exclude_unset=True)` preserves omission. The default dump
materializes defaults. Product, Material, and Service Pydantic models ignore
undeclared extra fields, including a hypothetical top-level `custom_fields`;
this audit does not claim those extras survive Pydantic conversion.

Generated TypeScript Variant, VariantResponse, and ServiceVariant types declare
`custom_fields?` with `Array<...> | null`, accepting absence, null, and legacy
arrays. Product, Material, and Service have no top-level member. These are compile
time types, not response validators. Strict TypeScript compilation of optionality
assertions and undefined/null/array assignments passed during the audit.

## Bounded live observation

The September 20, 2026 test-tenant probe used `make_test_client()` and GET requests
only. It requested the first page with `limit=50, page=1`, then one detail for
each populated entity. Automatic pagination was explicitly disabled.

| Endpoint  | First page                    | One detail                      |
| --------- | ----------------------------- | ------------------------------- |
| products  | 12 records, field absent      | Field absent                    |
| materials | 11 records, field absent      | Field absent                    |
| services  | Empty                         | Not probed; no record available |
| variants  | 28 records, field `[]` on all | Field `[]`                      |

No custom-field schema violation was observed. This tenant did not supply null
or populated-array examples, so those shapes are covered by local contract tests,
not verified by this live sample. The observations do not establish account feature
availability or universal list/detail behavior. The earlier issue's product-detail
null observation may describe different tenant data; the current schema permits
that undeclared property.

## MCP variant detail

`get_variant_details` preserves null versus an empty array in its
`custom_fields` result. It no longer converts both to `[]`. Populated legacy
arrays still retain their field names and values.

The existing `CachedVariant` column stores both an omitted wire field and explicit
null as `None`; therefore a cached detail result cannot recover that distinction.
The MCP response reports null for either state. This bounded correction adds no
presence column and does not claim exact omission preservation through the cache.

## Repeat the probe

From a checkout with test credentials configured:

```sh
uv run python scripts/probe_custom_field_reads.py --limit 50
```

The probe makes at most eight GET requests, never prints record IDs or field
values, reports empty-list limitations, and validates only the custom-field
projection so unrelated schema drift does not obscure this audit. It exits
nonzero for request failures or violations of a declared custom-field shape.
An undeclared field is reported separately and is not claimed to have a typed
contract. Missing `KATANA_TEST_API_KEY` fails through the shared helper; there is
no production-key fallback.

[`tests/test_custom_field_read_contracts.py`](../../tests/test_custom_field_read_contracts.py)
pins schema requiredness, attrs/Pydantic round trips, undeclared-field behavior,
and the probe's request bounds using mocks.
