"""Per-entity cache sync against the Katana API.

One generic ``_ensure_synced(client, cache, spec)`` drives every entity's
sync via an :class:`EntitySpec` configuration object. Each spec wires up:

- the entity-key string (used for the per-entity lock and ``SyncState`` row),
- the ``asyncio_detailed`` API endpoint to call,
- the cache row class (``Cached<Entity>``) and the API pydantic class
  (used as the ``from_attrs`` intermediary so nested-row conversion stays
  in one well-tested place),
- optional child-rows configuration (class, parent-side field name, FK
  field name) for entities with nested rows on the wire,
- an optional ``pydantic_resolver`` that picks the API pydantic subclass
  from the attrs object (used by purchase orders, where Katana returns a
  discriminated union ``RegularPurchaseOrder | OutsourcedPurchaseOrder``).

Public ``ensure_<entity>_synced(client, cache)`` functions are thin
wrappers over ``_ensure_synced`` so existing call sites and tests don't
need to change.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import batched
from typing import TYPE_CHECKING, Any, Protocol

from sqlalchemy import inspect as sqla_inspect
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import SQLModel, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from katana_mcp.logging import get_logger
from katana_public_api_client.api.additional_costs import get_additional_costs
from katana_public_api_client.api.customer import get_all_customers
from katana_public_api_client.api.factory import get_factory
from katana_public_api_client.api.location import get_all_locations
from katana_public_api_client.api.manufacturing_order import (
    get_all_manufacturing_orders,
)
from katana_public_api_client.api.manufacturing_order_recipe import (
    get_all_manufacturing_order_recipe_rows,
)
from katana_public_api_client.api.material import get_all_materials
from katana_public_api_client.api.operator import get_all_operators
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.purchase_order import find_purchase_orders
from katana_public_api_client.api.purchase_order_row import (
    get_all_purchase_order_rows,
)
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.sales_order_row import get_all_sales_order_rows
from katana_public_api_client.api.services import get_all_services
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.api.stock_transfer import get_all_stock_transfers
from katana_public_api_client.api.supplier import get_all_suppliers
from katana_public_api_client.api.tax_rate import get_all_tax_rates
from katana_public_api_client.api.variant import get_all_variants
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models.get_all_variants_extend_item import (
    GetAllVariantsExtendItem,
)
from katana_public_api_client.models_pydantic._generated import (
    AdditionalCost as PydanticAdditionalCost,
    CachedAdditionalCost,
    CachedCustomer,
    CachedFactory,
    CachedLocation,
    CachedManufacturingOrder,
    CachedManufacturingOrderRecipeRow,
    CachedMaterial,
    CachedOperator,
    CachedProduct,
    CachedPurchaseOrder,
    CachedPurchaseOrderRow,
    CachedSalesOrder,
    CachedSalesOrderRow,
    CachedService,
    CachedStockAdjustment,
    CachedStockAdjustmentRow,
    CachedStockTransfer,
    CachedStockTransferRow,
    CachedSupplier,
    CachedTaxRate,
    CachedVariant,
    Customer as PydanticCustomer,
    Factory as PydanticFactory,
    Location1 as PydanticLocation,
    ManufacturingOrder as PydanticManufacturingOrder,
    ManufacturingOrderRecipeRow as PydanticManufacturingOrderRecipeRow,
    Material as PydanticMaterial,
    Operator as PydanticOperator,
    Product as PydanticProduct,
    PurchaseOrderBase as PydanticPurchaseOrderBase,
    PurchaseOrderRow as PydanticPurchaseOrderRow,
    SalesOrder as PydanticSalesOrder,
    SalesOrderRow as PydanticSalesOrderRow,
    Service as PydanticService,
    StockAdjustment as PydanticStockAdjustment,
    StockTransfer as PydanticStockTransfer,
    Supplier as PydanticSupplier,
    TaxRate as PydanticTaxRate,
    VariantResponse as PydanticVariantResponse,
)
from katana_public_api_client.models_pydantic._registry import get_pydantic_class
from katana_public_api_client.utils import unwrap, unwrap_data

from .sync_state import SyncState

if TYPE_CHECKING:
    from katana_public_api_client import KatanaClient

    from .engine import TypedCacheEngine


logger = get_logger(__name__)


class _FromAttrs(Protocol):
    """Protocol for the API pydantic classes consumed by ``EntitySpec``.

    Every ``Pydantic*`` class generated by
    :mod:`scripts.generate_pydantic_models` exposes a ``from_attrs``
    classmethod that builds the pydantic instance from its attrs sibling.
    Declaring the contract as a Protocol lets the static checker reach
    into ``api_cls.from_attrs(...)`` without accepting arbitrary ``type``
    instances. ``id`` and ``model_dump`` are deliberately absent — they
    appear on the resulting *instance*, not the class, and the consumer
    accesses them via ``Any`` after the ``from_attrs`` call.
    """

    @classmethod
    def from_attrs(cls, attrs_obj: Any) -> Any: ...


@dataclass(frozen=True)
class EntitySpec:
    """Per-entity sync configuration consumed by ``_ensure_synced``.

    Required: ``entity_key`` (the lock + SyncState key — repeated three
    times in the prior hand-rolled helpers, source of silent-desync bugs
    if a typo slipped through), ``api_fn`` (the ``asyncio_detailed``-
    bearing endpoint module), ``cache_cls`` (``Cached<Entity>``), and
    ``pydantic_cls`` (the API pydantic class — the ``from_attrs`` /
    ``model_dump`` intermediary).

    Optional: a ``child_cls`` + ``rows_field`` + ``fk_field`` triple when
    the entity has nested rows; without them the sync emits a parent-only
    row pair (the manufacturing-order list endpoint shape).
    ``pydantic_resolver`` overrides ``pydantic_cls`` per-row by dispatching
    on the attrs subclass — used by purchase orders, where the
    discriminated-union root would otherwise lose subclass-only fields.

    ``related_specs`` is for entities whose rows live at a *separate* API
    endpoint with their own watermark (manufacturing orders + recipe
    rows: rows aren't nested in the MO response, so the nested-rows
    triple above doesn't apply). Listing them here means
    ``_ensure_synced`` fans out to sync them in parallel, so consumers
    that join parent ↔ child in cache can call a single
    ``ensure_<parent>_synced`` and trust that both sides are fresh —
    no caller-side ``asyncio.gather`` to forget.

    Phase B (#472) additions:

    - ``depends_on`` — entity_keys this spec must sync after. Catalog
      example: ``CachedVariant`` has FK to ``CachedProduct`` /
      ``CachedMaterial`` and lifts ``parent_archived_at`` from the
      extended payload, so it must run after both. Today the only
      runtime use is the validator at ``engine.open()`` (cycles +
      unknown refs); the actual ordering is hand-coded inside
      ``ensure_variants_synced`` via ``asyncio.gather``. The field is
      retained so the dependency declaration lives next to the spec and
      a future scheduler can replace the hand-coded gather with a topo
      walk without churn.
    - ``attrs_postprocess`` — ``(attrs_obj, cache_row) -> None`` mutating
      hook called after ``_convert`` builds the cache row. Variant uses
      it to populate ``parent_archived_at`` / ``display_name`` /
      ``parent_name`` / ``supplier_item_codes_text`` from the extended
      ``product_or_material`` payload — keeps Variant-specific
      denormalization out of the generic ``_convert``.
    - ``extra_fetch_kwargs`` — kwargs always passed to ``api_fn``
      regardless of incremental state. Variant uses it to enable
      ``extend=[PRODUCT_OR_MATERIAL]`` so the postprocess hook can read
      the parent's archive timestamp.
    - ``supports_incremental`` — when False (operator, factory: no
      ``updated_at_min`` support), the cold-start fetch always runs;
      relies on the per-entity sync lock to debounce concurrent callers.
    - ``supports_include_deleted`` — when False (operator, tax_rate,
      factory: no ``include_deleted`` query parameter), drops the kwarg.
      Tombstones won't propagate for these — acceptable since they're
      reference data without practical soft-deletes.
    - ``single_record`` — when True, the endpoint returns one record
      directly (Factory) rather than a list-wrapped response. Bypasses
      ``unwrap_data`` and constructs a one-element list internally.
    """

    entity_key: str
    api_fn: Any
    cache_cls: type[SQLModel]
    pydantic_cls: type[_FromAttrs]
    child_cls: type[SQLModel] | None = None
    rows_field: str | None = None
    fk_field: str | None = None
    pydantic_resolver: Callable[[Any], type[_FromAttrs]] | None = None
    related_specs: tuple[EntitySpec, ...] = field(default_factory=tuple)
    depends_on: tuple[str, ...] = ()
    attrs_postprocess: Callable[[Any, Any], None] | None = None
    extra_fetch_kwargs: dict[str, Any] = field(default_factory=dict)
    supports_incremental: bool = True
    supports_include_deleted: bool = True
    single_record: bool = False

    def __post_init__(self) -> None:
        # Children are configured by a ``(child_cls, rows_field, fk_field)``
        # triple — a partial set would silently drop children at runtime
        # because ``_convert`` only iterates when all three are present.
        # Catch the typo at construction time instead.
        triple = (self.child_cls, self.rows_field, self.fk_field)
        n_set = sum(value is not None for value in triple)
        if n_set not in (0, 3):
            msg = (
                "EntitySpec child_cls/rows_field/fk_field must all be "
                "set together or all left as None"
            )
            raise ValueError(msg)


def _validate_dependency_graph(specs: Iterable[EntitySpec]) -> None:
    """Validate ``EntitySpec.depends_on`` references and detect cycles.

    Raises ``ValueError`` if any spec references an unknown ``entity_key``
    or if the dependency graph has a cycle. Run at ``engine.open()`` so
    misconfiguration surfaces eagerly — never at the first sync.

    Cycle detection uses a tri-state coloring (white/gray/black) DFS.
    Gray means "on the current DFS stack" — a back-edge to a gray node
    is a cycle.
    """
    spec_list = list(specs)
    by_key = {s.entity_key: s for s in spec_list}

    for spec in spec_list:
        for dep in spec.depends_on:
            if dep not in by_key:
                msg = (
                    f"EntitySpec {spec.entity_key!r} declares "
                    f"depends_on={dep!r} but no spec with that "
                    f"entity_key is registered"
                )
                raise ValueError(msg)

    visited: set[str] = set()
    on_stack: list[str] = []
    on_stack_set: set[str] = set()

    def dfs(key: str) -> None:
        if key in visited:
            return
        if key in on_stack_set:
            cycle_path = [*on_stack[on_stack.index(key) :], key]
            msg = f"EntitySpec dependency cycle detected: {' -> '.join(cycle_path)}"
            raise ValueError(msg)
        on_stack.append(key)
        on_stack_set.add(key)
        for dep in by_key[key].depends_on:
            dfs(dep)
        on_stack.pop()
        on_stack_set.discard(key)
        visited.add(key)

    for spec in spec_list:
        dfs(spec.entity_key)


def _resolve_purchase_order_class(attrs_po: Any) -> type:
    """Pick the right pydantic subclass for a purchase-order attrs object.

    ``RegularPurchaseOrder`` and ``OutsourcedPurchaseOrder`` share
    ``PurchaseOrderBase`` fields but differ in ``entity_type`` and the
    outsourced-only ``tracking_location_id`` / ``ingredient_*`` fields.
    Calling ``PydanticPurchaseOrderBase.from_attrs`` directly would lose
    those subclass-only fields; the registry keeps the subtype.
    """

    api_class = get_pydantic_class(type(attrs_po))
    if api_class is None:
        msg = (
            f"No pydantic class registered for attrs purchase order "
            f"type {type(attrs_po).__name__}"
        )
        raise RuntimeError(msg)
    return api_class


def _convert(spec: EntitySpec, attrs_obj: Any) -> tuple[Any, list[Any]]:
    """Convert one attrs API object to a ``(parent, children)`` cache pair.

    Two-step:
    1. The API pydantic class (resolved via ``pydantic_resolver`` or
       ``spec.pydantic_cls``) handles UNSET → None, enum extraction,
       datetime coercion, and registry-driven nested-row conversion via
       ``from_attrs``.
    2. ``model_dump`` exports a plain dict; the cache class's
       ``model_validate`` reconstructs the parent (excluding the rows
       relationship — SQLModel ``Relationship`` descriptors don't accept
       input via ``__init__`` / ``model_validate``). Children, if
       configured, are re-built as the cache row class with the FK set
       explicitly from the parent's ``id`` so SQLAlchemy can wire the
       link on insert.

    Re-asserting the FK from the parent guards against the wire shape
    silently changing on entities (sales orders, purchase orders) where
    Katana already returns the FK on rows; for entities where Katana
    nests rows under the parent without a back-pointer (stock adjustments,
    stock transfers), the FK is synthesized here.
    """
    api_cls = (
        spec.pydantic_resolver(attrs_obj)
        if spec.pydantic_resolver is not None
        else spec.pydantic_cls
    )
    api_obj = api_cls.from_attrs(attrs_obj)

    exclude = {spec.rows_field} if spec.rows_field else set()
    parent_data = api_obj.model_dump(exclude=exclude)
    # Singleton endpoints (Factory) don't ship an ``id`` on the wire,
    # but the cache class needs one as PK. Pin id=1 here so
    # ``model_validate`` succeeds; postprocess hooks can still mutate
    # the row downstream. Other entities are no-ops.
    if spec.single_record and "id" not in parent_data:
        parent_data["id"] = 1
    parent = spec.cache_cls.model_validate(parent_data)

    children: list[Any] = []
    if (
        spec.child_cls is not None
        and spec.rows_field is not None
        and spec.fk_field is not None
    ):
        api_rows = getattr(api_obj, spec.rows_field) or []
        for api_row in api_rows:
            row_data = api_row.model_dump()
            row_data[spec.fk_field] = api_obj.id
            children.append(spec.child_cls.model_validate(row_data))

    # The postprocess hook runs after the cache row is built so it can
    # populate cache-only fields from the original attrs object — fields
    # like ``parent_archived_at`` that aren't on the API pydantic class
    # and therefore never make it through the ``from_attrs`` /
    # ``model_dump`` path. The hook mutates ``parent`` in place; returning
    # ``None`` keeps the convention with the pre-#472 sync helpers.
    if spec.attrs_postprocess is not None:
        spec.attrs_postprocess(attrs_obj, parent)

    return parent, children


# SQLite caps each prepared statement at 999 bound parameters by default.
# Headroom (900) keeps us safe on older / embedded builds without sacrificing
# meaningful throughput. Wide schemas (``CachedSalesOrder`` at 33 cols) end up
# at chunks of ~27; narrow ones (recipe rows at ~13 cols) get ~69 — both
# orders of magnitude beyond the per-row ``session.merge`` round-trip.
_SQLITE_PARAM_BUDGET = 900


async def _bulk_upsert(
    session: AsyncSession, table_cls: type[SQLModel], rows: list[Any]
) -> None:
    """One ``INSERT ... ON CONFLICT(id) DO UPDATE`` per chunk; no-op on empty rows.

    Replaces a per-row ``session.merge`` loop (SELECT-then-INSERT-or-UPDATE
    each) with a chunked bulk upsert. Chunk size is derived from each cache
    class's column count so we stay under SQLite's bound-parameter cap on
    wide schemas; narrower tables get larger chunks for free.

    The include-set is driven from ``__table__.columns`` rather than a
    hardcoded exclude list, so adding a new ``Relationship`` field to a
    cache class can never silently leak into the values payload.
    """
    if not rows:
        return

    # ``__table__`` is set by the SQLModel metaclass on ``table=True``
    # classes; the static type ``type[SQLModel]`` doesn't expose it, so
    # reach in via SQLAlchemy's ``inspect`` to keep the type checker happy.
    mapper = sqla_inspect(table_cls)
    column_names = {col.name for col in mapper.columns}
    chunk_size = max(1, _SQLITE_PARAM_BUDGET // len(column_names))

    # ``model_dump`` per chunk (not eagerly across the whole batch) so a
    # cold sync of thousands of rows doesn't double-buffer the cache rows
    # *and* their dict projections in memory before the first INSERT.
    for chunk in batched(rows, chunk_size):
        values = [r.model_dump(include=column_names) for r in chunk]
        stmt = sqlite_insert(table_cls).values(values)
        update_cols = {c.name: c for c in stmt.excluded if c.name != "id"}
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_cols)
        await session.exec(stmt)


async def _ensure_synced(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Pull updated rows for one entity from Katana and upsert into the cache.

    Every call hits the API. Cold-start fetches the full history (cost
    scales with row count); subsequent calls pass
    ``updated_at_min=<last_synced>`` so the API returns only the delta
    since the previous sync — typically zero rows, ~100-200ms RTT for
    the empty response. The per-entity lock guarantees only one sync
    runs at a time even when multiple tool calls land concurrently
    (the second waits, then issues its own — also typically empty —
    delta fetch). We deliberately do not debounce: an explicit TTL
    layer hides MCP-driven mutations and out-of-band UI edits behind
    a stale window for no real saving, since the delta fetch is
    already cheap.

    Soft-deletes are folded in by passing ``include_deleted=True``: when
    a row is deleted in the Katana UI, the next incremental fetch returns
    it with ``deleted_at`` populated, and the upsert path naturally
    propagates that timestamp into the cache row. The cache classes all
    extend ``DeletableEntity`` (a ``deleted_at`` column ships natively),
    and every ``list_*`` query already filters ``deleted_at IS NULL``, so
    no ghost rows leak to callers and the historical record survives in
    the cache for any future audit/reporting need. We mirror Katana's own
    soft-delete model rather than hard-deleting locally.

    ``spec.related_specs`` triggers parallel sync of sibling entities
    (e.g. manufacturing-order recipe rows when MOs are synced) so a
    consumer joining parent ↔ child in cache only needs to call one
    ``ensure_<parent>_synced``.
    """
    if spec.related_specs:
        await asyncio.gather(
            _sync_one(client, cache, spec),
            *(_ensure_synced(client, cache, related) for related in spec.related_specs),
        )
        return
    await _sync_one(client, cache, spec)


async def _sync_one(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Sync exactly one entity (no related-spec fan-out).

    Split out from ``_ensure_synced`` so the related-spec gather doesn't
    re-enter the parent's lock recursively when a future child carries
    its own ``related_specs`` chain — each entity's sync runs under its
    own per-entity lock, no nesting.
    """
    async with cache.lock_for(spec.entity_key):
        await _sync_one_locked(client, cache, spec)


async def _sync_one_locked(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Same sync work as ``_sync_one``, but assumes the caller already holds
    ``cache.lock_for(spec.entity_key)``.

    Used by :func:`force_resync` so the truncate and the cold-start re-pull
    happen under one continuous lock acquisition — concurrent ``list_*``
    tools block on the same lock until both phases finish and never observe
    an empty cache. ``_sync_one`` itself is the lock-acquiring wrapper for
    the normal incremental-sync path; calling it from ``force_resync`` while
    the lock is held would deadlock (asyncio.Lock isn't reentrant).
    """
    async with cache.session() as session:
        state = await session.get(SyncState, spec.entity_key)
        last_synced = state.last_synced if state is not None else None

    # ``last_synced`` is persisted as naive UTC (SQLite's default
    # DateTime column strips tzinfo). Re-attach UTC before sending to
    # the API so the generated client serializes an explicit offset.
    # ``include_deleted=True`` is always sent so soft-deletes after
    # the watermark surface in the response (Katana bumps
    # ``updated_at`` when ``deleted_at`` is set), letting the upsert
    # propagate the tombstone into the cache row. A few catalog endpoints
    # (operator, factory, tax_rate) don't expose ``include_deleted`` —
    # spec.supports_include_deleted=False drops the kwarg there.
    kwargs: dict[str, Any] = dict(spec.extra_fetch_kwargs)
    if spec.supports_include_deleted:
        kwargs.setdefault("include_deleted", True)
    if last_synced is not None and spec.supports_incremental:
        kwargs["updated_at_min"] = last_synced.replace(tzinfo=UTC)
    response = await spec.api_fn.asyncio_detailed(client=client, **kwargs)
    if spec.single_record:
        # Endpoints like ``GET /factory`` return a bare object rather than
        # a list-wrapped ``{"data": [...]}``. Normalize to a one-element
        # list so the rest of the pipeline stays generic.
        single = unwrap(response)
        attrs_objs = [single] if single is not None else []
    else:
        attrs_objs = unwrap_data(response, default=[])

    cached_parents: list[Any] = []
    cached_children: list[Any] = []
    for attrs_obj in attrs_objs:
        parent, children = _convert(spec, attrs_obj)
        cached_parents.append(parent)
        cached_children.extend(children)

    async with cache.session() as session:
        # Parents first so child FK constraints resolve on insert.
        # ``_bulk_upsert`` issues Core ``INSERT ... ON CONFLICT``
        # statements via ``sqlalchemy.dialects.sqlite.insert``. SQLite
        # triggers (registered by ``_create_fts_tables_ddl`` on
        # engine.open()) keep the FTS5 inverted index in sync —
        # SQLAlchemy mapper events would silently miss this Core path,
        # but SQLite triggers fire for every write mode (ORM, Core,
        # raw SQL).
        await _bulk_upsert(session, spec.cache_cls, cached_parents)
        if spec.child_cls is not None:
            await _bulk_upsert(session, spec.child_cls, cached_children)
        # SQLite's DateTime column doesn't preserve tzinfo, so naive
        # UTC on the write side. ``row_count`` is the last-fetch size
        # (not a cumulative total, which would drift since a re-sync
        # that finds zero changed rows would otherwise reset the
        # count); consumers needing a true total run ``SELECT COUNT(*)``
        # on the entity table itself.
        await session.merge(
            SyncState(
                entity_type=spec.entity_key,
                last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                row_count=len(cached_parents),
            )
        )
        await session.commit()


async def merge_filtered_fetch(
    cache: TypedCacheEngine,
    spec: EntitySpec,
    attrs_objs: Iterable[Any],
) -> None:
    """Convert + merge filtered API results without advancing the watermark.

    Use when a tool needs a narrow predicate (e.g.,
    ``ingredient_availability=NOT_AVAILABLE``) that the API can answer
    server-side. Reuses the same ``_convert(spec, attrs_obj)`` parent/child
    conversion as ``_sync_one_locked`` and merges via ``session.merge``
    inside a single transaction.

    Critically: does NOT update ``SyncState.last_synced``. The watermark is
    a "I've seen everything ≥ this timestamp" claim; a filtered fetch only
    saw rows matching the predicate, not all rows that changed since the
    watermark. Advancing it would silently drift other tools' data.

    Does not acquire ``cache.lock_for(...)`` either: ``session.merge`` is
    PK-idempotent, SQLite serializes the transaction, and the per-entity
    lock exists to coordinate the watermark write with the API fetch
    (irrelevant here). Locking would also serialize concurrent tool calls,
    defeating the parallelism the rate limiter affords.

    Empty input is a no-op (no session opened, no merge issued).
    """
    cached_parents: list[Any] = []
    cached_children: list[Any] = []
    for attrs_obj in attrs_objs:
        parent, children = _convert(spec, attrs_obj)
        cached_parents.append(parent)
        cached_children.extend(children)

    if not cached_parents:
        return

    async with cache.session() as session:
        # Parents first so child FK constraints resolve on insert (mirrors
        # ``_sync_one_locked``'s order; redundant for entities without
        # children but harmless).
        for parent in cached_parents:
            await session.merge(parent)
        for child in cached_children:
            await session.merge(child)
        await session.commit()

    logger.info(
        "merge_filtered_fetch",
        entity=spec.entity_key,
        merged=len(cached_parents),
        children=len(cached_children),
    )


# ---------------------------------------------------------------------------
# Per-entity specs
# ---------------------------------------------------------------------------


# Sales-order rows: nested under their parent in the ``find_sales_orders``
# response, but the response *hides* soft-deleted rows even with
# ``include_deleted=True`` (that flag controls top-level inclusion only).
# Without an independent row sync, a row deleted via ``delete_sales_order_row``
# on a still-live parent stays in the cache as a ghost. The dedicated
# ``/sales_order_rows`` endpoint exposes ``include_deleted`` + the same
# ``updated_at_min`` watermark mechanism, so we can pick up tombstones the
# parent response omits. Defined before ``_SALES_ORDER_SPEC`` so the parent's
# ``related_specs`` can reference it (frozen dataclasses can't forward-ref).
_SALES_ORDER_ROW_SPEC = EntitySpec(
    entity_key="sales_order_row",
    api_fn=get_all_sales_order_rows,
    cache_cls=CachedSalesOrderRow,
    pydantic_cls=PydanticSalesOrderRow,
)


_SALES_ORDER_SPEC = EntitySpec(
    entity_key="sales_order",
    api_fn=get_all_sales_orders,
    cache_cls=CachedSalesOrder,
    pydantic_cls=PydanticSalesOrder,
    child_cls=CachedSalesOrderRow,
    rows_field="sales_order_rows",
    fk_field="sales_order_id",
    related_specs=(_SALES_ORDER_ROW_SPEC,),
)


_STOCK_ADJUSTMENT_SPEC = EntitySpec(
    entity_key="stock_adjustment",
    api_fn=get_all_stock_adjustments,
    cache_cls=CachedStockAdjustment,
    pydantic_cls=PydanticStockAdjustment,
    child_cls=CachedStockAdjustmentRow,
    rows_field="stock_adjustment_rows",
    fk_field="stock_adjustment_id",
)


# Manufacturing-order recipe rows: fetched from the separate
# ``/manufacturing_order_recipe_rows`` endpoint, not nested under the MO
# parent — so they have their own ``updated_at_min`` watermark and sync
# lock. Direct conversion via the pydantic intermediary; ``batch_transactions``
# survives ``model_dump`` as a plain dict list and lands in the cache class's
# JSON column unchanged. Defined before the MO spec because the MO spec
# references it via ``related_specs`` (frozen dataclasses can't forward-
# reference each other).
MANUFACTURING_ORDER_RECIPE_ROW_SPEC = EntitySpec(
    entity_key="manufacturing_order_recipe_row",
    api_fn=get_all_manufacturing_order_recipe_rows,
    cache_cls=CachedManufacturingOrderRecipeRow,
    pydantic_cls=PydanticManufacturingOrderRecipeRow,
)


# Manufacturing orders: the list endpoint returns summary objects with no
# nested rows. Recipe rows live at the sibling endpoint above and are
# pulled in via ``related_specs`` so any cache consumer that joins MO ↔
# recipe row (e.g. ``list_blocking_ingredients``) only needs to call
# ``ensure_manufacturing_orders_synced`` and trusts both watermarks have
# been advanced.
MANUFACTURING_ORDER_SPEC = EntitySpec(
    entity_key="manufacturing_order",
    api_fn=get_all_manufacturing_orders,
    cache_cls=CachedManufacturingOrder,
    pydantic_cls=PydanticManufacturingOrder,
    related_specs=(MANUFACTURING_ORDER_RECIPE_ROW_SPEC,),
)


# Purchase-order rows: like sales-order rows, ``find_purchase_orders``
# hides soft-deleted nested rows even with ``include_deleted=True`` set
# at the parent level. The ``/purchase_order_rows`` sibling endpoint
# (added to MCP via ``delete_purchase_order_row`` /
# ``update_purchase_order_row`` in #461) exposes ``include_deleted`` and
# its own watermark, so we sync rows independently to catch tombstones
# the parent response omits.
_PURCHASE_ORDER_ROW_SPEC = EntitySpec(
    entity_key="purchase_order_row",
    api_fn=get_all_purchase_order_rows,
    cache_cls=CachedPurchaseOrderRow,
    pydantic_cls=PydanticPurchaseOrderRow,
)


# Purchase orders: discriminated-union entity. The cache class shadows
# ``PurchaseOrderBase`` (renamed via ``CACHE_TABLE_RENAMES``) and carries
# an extra ``tracking_location_id`` column hoisted from the outsourced
# subclass via ``CACHE_EXTRA_FIELDS``. ``_resolve_purchase_order_class``
# picks the right subtype so ``model_dump`` captures the outsourced-only
# fields; ``CachedPurchaseOrder.model_validate`` ignores the
# unrecognized-by-the-cache extras automatically.
_PURCHASE_ORDER_SPEC = EntitySpec(
    entity_key="purchase_order",
    api_fn=find_purchase_orders,
    cache_cls=CachedPurchaseOrder,
    pydantic_cls=PydanticPurchaseOrderBase,
    child_cls=CachedPurchaseOrderRow,
    rows_field="purchase_order_rows",
    fk_field="purchase_order_id",
    pydantic_resolver=_resolve_purchase_order_class,
    related_specs=(_PURCHASE_ORDER_ROW_SPEC,),
)


_STOCK_TRANSFER_SPEC = EntitySpec(
    entity_key="stock_transfer",
    api_fn=get_all_stock_transfers,
    cache_cls=CachedStockTransfer,
    pydantic_cls=PydanticStockTransfer,
    child_cls=CachedStockTransferRow,
    rows_field="stock_transfer_rows",
    fk_field="stock_transfer_id",
)


# ---------------------------------------------------------------------------
# Catalog specs (#472 Phase B) — variant + product/material parents,
# service, customer, supplier, plus reference data.
# ---------------------------------------------------------------------------


def _variant_postprocess(attrs_obj: Any, cache_row: CachedVariant) -> None:
    """Populate cache-only Variant fields from the extended attrs payload.

    Variants don't carry their own archive lifecycle on the wire — Katana
    archives at the parent (Product / Material) level and cascades. We
    fetch each variant with ``extend=[PRODUCT_OR_MATERIAL]``, then lift
    ``parent.archived_at`` here so search can filter archived rows
    without re-joining at query time.

    Three more cache-only fields land here for FTS5 performance:

    - ``parent_name`` — direct lift, surfaces in result rendering.
    - ``display_name`` — synthesized from ``parent_name`` + each
      ``config_attribute.config_value`` joined by `` / ``. Falls back to
      the SKU when the parent name is empty (a defensive case the legacy
      cache also handled).
    - ``supplier_item_codes_text`` — space-joined ``supplier_item_codes``
      so the FTS5 tokenizer can index multi-token supplier codes without
      re-parsing JSON at query time.

    Mirrors the legacy ``_variant_to_cache_dict`` semantics in
    ``katana_mcp/cache_sync.py`` byte-for-byte; the only structural
    change is that the postprocess hook runs *after* the cache row is
    built rather than mutating a raw dict before it.
    """
    parent = unwrap_unset(getattr(attrs_obj, "product_or_material", None), None)

    # ``parent_archived_at`` + ``parent_name`` lift directly from the
    # extended payload. ``parent`` is an attrs object (Product/Material)
    # when the API returns it; UNSET means the caller didn't request the
    # extension or the row points at a non-existent parent.
    parent_name: str | None = None
    if parent is not None:
        cache_row.parent_archived_at = unwrap_unset(
            getattr(parent, "archived_at", None), None
        )
        parent_name = unwrap_unset(getattr(parent, "name", None), None)
        cache_row.parent_name = parent_name

    # ``display_name`` mirrors the legacy synthesis: parent name (or SKU
    # fallback) joined with each config attribute's value. The empty-
    # parent-name fallback to SKU is defensive — Katana always returns
    # a non-empty parent name in practice, but the legacy cache handled
    # the empty case so we preserve it.
    sku = unwrap_unset(getattr(attrs_obj, "sku", None), "") or ""
    display_parts: list[str] = [parent_name] if parent_name else [sku] if sku else []
    config_attrs = unwrap_unset(getattr(attrs_obj, "config_attributes", None), [])
    if config_attrs:
        for attr in config_attrs:
            value = unwrap_unset(getattr(attr, "config_value", None), None)
            if value:
                display_parts.append(value)
    cache_row.display_name = " / ".join(display_parts) if display_parts else None

    # ``supplier_item_codes_text``: FTS5's default tokenizer splits on
    # whitespace, so the cache-side text projection is a space-joined
    # version of the JSON-array column. ``None`` when there are no codes
    # so the FTS sidecar's NULL-safe handling stays simple.
    codes = unwrap_unset(getattr(attrs_obj, "supplier_item_codes", None), [])
    cache_row.supplier_item_codes_text = " ".join(codes) if codes else None


_PRODUCT_SPEC = EntitySpec(
    entity_key="product",
    api_fn=get_all_products,
    cache_cls=CachedProduct,
    pydantic_cls=PydanticProduct,
    extra_fetch_kwargs={"include_archived": True},
)


_MATERIAL_SPEC = EntitySpec(
    entity_key="material",
    api_fn=get_all_materials,
    cache_cls=CachedMaterial,
    pydantic_cls=PydanticMaterial,
    extra_fetch_kwargs={"include_archived": True},
)


# Variants depend on Product + Material for cache-completeness reasons:
# variants carry FK references to product/material IDs, and join-style
# queries against the cache (``v.product_id -> CachedProduct``) need
# both sides cached for results to land. The ``parent_archived_at`` /
# ``parent_name`` denormalization lives entirely on the variant
# postprocess hook — it reads from the *extended* attrs payload
# (``product_or_material`` set via ``extend=[PRODUCT_OR_MATERIAL]``),
# not from the cached parent row, so the dependency is a soft cache-
# completeness guarantee rather than a postprocess prerequisite. Today
# ``ensure_variants_synced`` enforces ordering via ``asyncio.gather``;
# the ``depends_on`` field is declarative metadata for a future
# topo-walking scheduler (validated at ``engine.open()``, not yet
# consulted at sync time).
_VARIANT_SPEC = EntitySpec(
    entity_key="variant",
    api_fn=get_all_variants,
    cache_cls=CachedVariant,
    pydantic_cls=PydanticVariantResponse,
    extra_fetch_kwargs={
        "extend": [GetAllVariantsExtendItem.PRODUCT_OR_MATERIAL],
        "include_archived": True,
    },
    depends_on=("product", "material"),
    attrs_postprocess=_variant_postprocess,
)


_SERVICE_SPEC = EntitySpec(
    entity_key="service",
    api_fn=get_all_services,
    cache_cls=CachedService,
    pydantic_cls=PydanticService,
    extra_fetch_kwargs={"include_archived": True},
)


_CUSTOMER_SPEC = EntitySpec(
    entity_key="customer",
    api_fn=get_all_customers,
    cache_cls=CachedCustomer,
    pydantic_cls=PydanticCustomer,
)


_SUPPLIER_SPEC = EntitySpec(
    entity_key="supplier",
    api_fn=get_all_suppliers,
    cache_cls=CachedSupplier,
    pydantic_cls=PydanticSupplier,
)


_LOCATION_SPEC = EntitySpec(
    entity_key="location",
    api_fn=get_all_locations,
    cache_cls=CachedLocation,
    pydantic_cls=PydanticLocation,
)


# Tax rates: ``GET /tax_rates`` supports ``updated_at_min`` but not
# ``include_deleted``, so we sync incrementally without the deletion
# flag. Tax rates have no soft-delete concept (no ``deleted_at``
# column on the cache class either), so dropping the flag is safe.
_TAX_RATE_SPEC = EntitySpec(
    entity_key="tax_rate",
    api_fn=get_all_tax_rates,
    cache_cls=CachedTaxRate,
    pydantic_cls=PydanticTaxRate,
    supports_include_deleted=False,
)


# Operators: ``GET /operators`` supports neither ``updated_at_min`` nor
# ``include_deleted`` (the API exposes the operator list as a stable
# snapshot tied to working_area). Each sync re-fetches the full list;
# the per-entity lock debounces concurrent callers.
_OPERATOR_SPEC = EntitySpec(
    entity_key="operator",
    api_fn=get_all_operators,
    cache_cls=CachedOperator,
    pydantic_cls=PydanticOperator,
    supports_incremental=False,
    supports_include_deleted=False,
)


_ADDITIONAL_COST_SPEC = EntitySpec(
    entity_key="additional_cost",
    api_fn=get_additional_costs,
    cache_cls=CachedAdditionalCost,
    pydantic_cls=PydanticAdditionalCost,
)


# Factory: ``GET /factory`` returns a single record (not a list-wrapped
# response). The endpoint also supports neither ``updated_at_min`` nor
# ``include_deleted``; ``single_record=True`` swaps ``unwrap_data`` for
# ``unwrap`` and wraps the result in a one-element list so the rest of
# the pipeline stays generic. The wire shape has no ``id`` field, so
# ``_convert`` synthesizes ``id=1`` for singleton specs (matches the
# legacy ``CatalogCache._fetch_factory`` convention).
_FACTORY_SPEC = EntitySpec(
    entity_key="factory",
    api_fn=get_factory,
    cache_cls=CachedFactory,
    pydantic_cls=PydanticFactory,
    supports_incremental=False,
    supports_include_deleted=False,
    single_record=True,
)


# ---------------------------------------------------------------------------
# Public per-entity wrappers
# ---------------------------------------------------------------------------


async def ensure_sales_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated sales orders from Katana and upsert into the typed cache."""
    await _ensure_synced(client, cache, _SALES_ORDER_SPEC)


async def ensure_stock_adjustments_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock adjustments from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _STOCK_ADJUSTMENT_SPEC)


async def ensure_manufacturing_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated manufacturing orders from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, MANUFACTURING_ORDER_SPEC)


async def ensure_purchase_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated purchase orders from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _PURCHASE_ORDER_SPEC)


async def ensure_stock_transfers_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock transfers from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _STOCK_TRANSFER_SPEC)


async def ensure_manufacturing_order_recipe_rows_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated MO recipe rows from Katana and upsert into the cache.

    Recipe rows are fetched from the separate
    ``/manufacturing_order_recipe_rows`` endpoint (not nested under the
    MO parent), so they have their own ``updated_at_min`` watermark and
    sync lock. ``ensure_manufacturing_orders_synced`` already fans out to
    this spec via ``related_specs``, so most callers don't need to call
    this helper directly — it's exposed for tools that specifically want
    only the recipe-row watermark advanced.
    """
    await _ensure_synced(client, cache, MANUFACTURING_ORDER_RECIPE_ROW_SPEC)


# Catalog wrappers (#472 Phase B). Variant explicitly syncs its parents
# first so any caller that joins variants to their cached parents sees
# both sides on a single ``ensure_variants_synced`` round trip — the
# postprocess hook itself reads ``parent_archived_at`` / ``parent_name``
# from the extended ``product_or_material`` attrs payload, not from the
# cached parent row, so it doesn't actually depend on the parent rows
# having landed first. After Phase D lands, these wrappers replace
# ``cache_sync.py``'s legacy ``ensure_*_synced`` helpers.


async def ensure_products_synced(client: KatanaClient, cache: TypedCacheEngine) -> None:
    """Pull updated products from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _PRODUCT_SPEC)


async def ensure_materials_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated materials from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _MATERIAL_SPEC)


async def ensure_variants_synced(client: KatanaClient, cache: TypedCacheEngine) -> None:
    """Pull updated variants from Katana and upsert into the cache.

    Syncs Product + Material parents in parallel first, then variants.
    The ordering exists for cache-completeness (downstream queries that
    join variants to their cached parents need both sides materialized);
    the variant postprocess hook itself reads ``parent_archived_at`` /
    ``parent_name`` from the *extended* ``product_or_material`` attrs
    payload set by ``extend=[PRODUCT_OR_MATERIAL]``, not from the cached
    parent row, so it works even if the parent sync hasn't run yet.
    Parents have no inter-dependency, so they sync in parallel; the
    variant sync then fans out under its own lock once both parent
    watermarks have advanced.
    """
    await asyncio.gather(
        _ensure_synced(client, cache, _PRODUCT_SPEC),
        _ensure_synced(client, cache, _MATERIAL_SPEC),
    )
    await _ensure_synced(client, cache, _VARIANT_SPEC)


async def ensure_services_synced(client: KatanaClient, cache: TypedCacheEngine) -> None:
    """Pull updated services from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _SERVICE_SPEC)


async def ensure_customers_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated customers from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _CUSTOMER_SPEC)


async def ensure_suppliers_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated suppliers from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _SUPPLIER_SPEC)


async def ensure_locations_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull locations from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _LOCATION_SPEC)


async def ensure_tax_rates_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated tax rates from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _TAX_RATE_SPEC)


async def ensure_operators_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull operators from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _OPERATOR_SPEC)


async def ensure_factory_synced(client: KatanaClient, cache: TypedCacheEngine) -> None:
    """Pull the (singleton) factory record from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _FACTORY_SPEC)


async def ensure_additional_costs_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated additional costs from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _ADDITIONAL_COST_SPEC)


# ---------------------------------------------------------------------------
# Force-resync (truncate + cold-start re-pull, atomically)
# ---------------------------------------------------------------------------


ENTITY_SPECS: dict[str, EntitySpec] = {
    "sales_order": _SALES_ORDER_SPEC,
    "stock_adjustment": _STOCK_ADJUSTMENT_SPEC,
    "manufacturing_order": MANUFACTURING_ORDER_SPEC,
    "purchase_order": _PURCHASE_ORDER_SPEC,
    "stock_transfer": _STOCK_TRANSFER_SPEC,
    "product": _PRODUCT_SPEC,
    "material": _MATERIAL_SPEC,
    "variant": _VARIANT_SPEC,
    "service": _SERVICE_SPEC,
    "customer": _CUSTOMER_SPEC,
    "supplier": _SUPPLIER_SPEC,
    "location": _LOCATION_SPEC,
    "tax_rate": _TAX_RATE_SPEC,
    "operator": _OPERATOR_SPEC,
    "factory": _FACTORY_SPEC,
    "additional_cost": _ADDITIONAL_COST_SPEC,
}
"""Public registry of top-level entity specs by user-facing key.

Used by the ``rebuild_cache`` MCP tool (``cache_admin``) to look up the
cache classes and watermark keys for any cached entity type. Sibling
row specs (PO rows, MO recipe rows) aren't keyed at the top level —
they're reachable via each spec's ``related_specs`` instead.
"""


async def force_resync(
    client: KatanaClient, cache: TypedCacheEngine, entity_key: str
) -> None:
    """Atomically truncate cache tables for one entity and re-fetch from Katana.

    Holds the entity's sync lock(s) — parent plus every related spec's lock
    — across both the truncate and the cold-start re-fetch. The normal
    ``ensure_<entity>_synced`` path acquires and releases its lock once per
    sync; this helper does not, so a concurrent ``list_<entity>`` blocks on
    the same locks until the re-fetch completes and never observes the
    intermediate empty state.

    Use case: the ``rebuild_cache`` MCP tool, when phantom rows have
    accumulated in the cache (entities present locally that no longer exist
    upstream because a hard-delete or partial sync left no tombstone for
    the incremental delta to pick up).
    """
    if entity_key not in ENTITY_SPECS:
        msg = (
            f"Unknown entity_key {entity_key!r}; expected one of {sorted(ENTITY_SPECS)}"
        )
        raise ValueError(msg)
    spec = ENTITY_SPECS[entity_key]
    all_specs: tuple[EntitySpec, ...] = (spec, *spec.related_specs)

    async with AsyncExitStack() as stack:
        for s in all_specs:
            await stack.enter_async_context(cache.lock_for(s.entity_key))
        # All locks held. Truncate child tables first to satisfy FK
        # constraints, then the parent. PO/SO row-spec ``cache_cls`` is the
        # same SQLModel as ``spec.child_cls``; the set dedupes.
        children_to_delete: set[type] = set()
        if spec.child_cls is not None:
            children_to_delete.add(spec.child_cls)
        for related in spec.related_specs:
            children_to_delete.add(related.cache_cls)
        async with cache.session() as session:
            # Core ``DELETE`` fires the per-row ``<entity>_ad`` trigger
            # for each row, which issues the FTS5 ``'delete'`` command
            # against the inverted index — so the FTS sidecar self-cleans
            # in the same transaction without an explicit truncate pass.
            for child_cls in children_to_delete:
                await session.exec(delete(child_cls))
            await session.exec(delete(spec.cache_cls))
            for s in all_specs:
                state_row = await session.get(SyncState, s.entity_key)
                if state_row is not None:
                    await session.delete(state_row)
            await session.commit()
        # Re-fetch under the still-held locks. Parent first so its inline
        # rows (PO/SO) land before the row spec's separate fetch picks up
        # row-level tombstones the parent payload omits.
        for s in all_specs:
            await _sync_one_locked(client, cache, s)
