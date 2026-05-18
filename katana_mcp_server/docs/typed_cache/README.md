# Typed Cache — Patterns and Pitfalls

The typed cache is a SQLite-backed mirror of Katana's wire state, with per-entity tables
(`product`, `material`, `supplier`, `manufacturing_order`, …) generated from the same
pydantic models the API client uses. It exists so MCP tools can serve queries without
round-tripping to Katana for every read, and so FTS5 fuzzy search has something to
index.

The rules below are about how the cache layer relates to the API layer (the spec, the
generated pydantic, the attrs models) — what belongs where, and what surprises bite when
those layers blur.

Related code:

- `katana_mcp_server/src/katana_mcp/typed_cache/sync.py` — attrs → API pydantic → cache
  pydantic conversion.
- `scripts/generate_pydantic_models.py` — emits both the API pydantic class and the
  sibling `Cached<Name>` class with `table=True` per entity. See
  `duplicate_cache_tables_as_cached_siblings`.

______________________________________________________________________

## Archive / deleted state — opt-in flags + derived booleans

Katana represents soft-state as nullable timestamps on the wire: `archived_at` (the
user-toggleable archive lifecycle — exposed on catalog items, inventory rows, and a few
other archivable entities) and `deleted_at` (soft-delete, exposed on most entities
including catalog items *and* transactional entities like POs, SOs, MOs, stock
transfers, stock adjustments). The two are independent — an entity can be both archived
and soft-deleted.

Two MCP-side conventions surface this; **keep them symmetric**:

### Query-param flags for opting into soft-state rows (default `False`)

Items use `include_archived` (`search_items`, catalog cache). After #472 Phase D the
canonical wiring is the typed cache's `CatalogQueries` adapter — `parent_archived_at` is
denormalized onto `CachedVariant` at sync time (via the variant `attrs_postprocess` hook
in `typed_cache/sync.py`) and the adapter's default `include_archived=False` /
`include_deleted=False` filters push the `archived_at IS NULL` / `deleted_at IS NULL`
predicates down to SQL.

Transactional entities use `include_deleted` on `list_purchase_orders` /
`list_sales_orders` / `list_manufacturing_orders` / `list_stock_adjustments`, filtering
at the same typed-cache query layer.

### Response-side derived booleans

Every response model that exposes `archived_at` / `deleted_at` should also expose a
convenience `is_archived` / `is_deleted` bool derived from `<timestamp> is not None`,
saving callers from the timestamp/null inspection.

**Note the asymmetry**: `is_archived` mirrors Katana's *write* convention
(`update_<entity>` request bodies accept `is_archived: bool`, so round-tripping through
`modify_<entity>` with `{"update_header": {"is_archived": false}}` works). `is_deleted`,
by contrast, is *read-side only* — Katana exposes deletion through DELETE endpoints, not
as a writable boolean on update bodies. Items expose `is_archived` on `ItemInfo` and
`ItemDetailsResponse` as of #526.

Don't add a new opt-in flag without the matching derived bool, and vice versa.

**Known gaps** (filed for follow-up):

- `list_stock_transfers` lacks `include_deleted` parity (#484).
- `check_inventory` lacks `include_archived` and the `is_archived` row field (#539).
- Transactional response models lack the `is_deleted` derived bool (#540).

______________________________________________________________________

## Cache IDs are not globally unique — never merge cross-entity maps by numeric ID alone

The typed cache stores each entity type in its own table (`product`, `material`,
`supplier`, …), so a product with `id=42` and a material with `id=42` are both legal.
When enriching a list of variants with parent context (or any other cross-entity batch
fetch), keep separate per-type maps (`products`, `materials`) and select based on which
ID the variant carries (`v.product_id` vs `v.material_id`).

Merging into a single dict via `{**products, **materials}` mis-attaches parents on
collision — Python dict-unpack iterates left-to-right and later keys win, so the
material entry silently overwrites the product entry on shared IDs. The bug is symmetric
in practice: every product variant whose ID also exists as a material ID looks up the
material's data instead (and vice versa if you reorder the unpack).

Caught in #542 (variant card redesign) by Copilot review; regression test pins the case
in `test_items.py::test_enrich_variants_keeps_product_and_material_maps_separate`.

______________________________________________________________________

## Don't pollute the API spec/models with cache-only fields

The OpenAPI spec at `docs/katana-openapi.yaml` and the generated pydantic models in
`katana_public_api_client/models_pydantic/_generated/*.py` reflect Katana's actual wire
contract. **Never** add fields to the spec or inject fields into the API pydantic
classes to satisfy cache-schema, MCP-tool, or other consumer needs.

Cache schemas live on sibling `Cached<Name>` classes emitted by the same generator pass
— the API class stays pure pydantic, the cache class carries `table=True`, foreign keys,
relationships, JSON columns, and any cache-only fields. See
`scripts/generate_pydantic_models.py::duplicate_cache_tables_as_cached_siblings` and
`katana_mcp_server/src/katana_mcp/typed_cache/sync.py::_attrs_<entity>_to_cached` for
the conversion pattern: attrs → API pydantic (via the registry) → cache pydantic (via
`model_dump`/`model_validate`), with relationship fields set after construction since
SQLModel `Relationship` descriptors don't accept input via `__init__`.

If a bug surfaces in `sync.py` but originates in generated client code (attrs, pydantic,
`from_attrs`, `Cached*` schemas), fix it at the generator/spec layer — not in `sync.py`.
See
[Fix bugs at the client/generator layer](../../../katana_public_api_client/docs/spec-authoring.md#fix-bugs-at-the-clientgenerator-layer-when-the-root-cause-lives-there)
in the spec-authoring guide.
