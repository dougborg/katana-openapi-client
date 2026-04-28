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

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from katana_public_api_client.api.manufacturing_order import (
    get_all_manufacturing_orders,
)
from katana_public_api_client.api.manufacturing_order_recipe import (
    get_all_manufacturing_order_recipe_rows,
)
from katana_public_api_client.api.purchase_order import find_purchase_orders
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.api.stock_transfer import get_all_stock_transfers
from katana_public_api_client.models_pydantic._generated import (
    CachedManufacturingOrder,
    CachedManufacturingOrderRecipeRow,
    CachedPurchaseOrder,
    CachedPurchaseOrderRow,
    CachedSalesOrder,
    CachedSalesOrderRow,
    CachedStockAdjustment,
    CachedStockAdjustmentRow,
    CachedStockTransfer,
    CachedStockTransferRow,
    ManufacturingOrder as PydanticManufacturingOrder,
    ManufacturingOrderRecipeRow as PydanticManufacturingOrderRecipeRow,
    PurchaseOrderBase as PydanticPurchaseOrderBase,
    SalesOrder as PydanticSalesOrder,
    StockAdjustment as PydanticStockAdjustment,
    StockTransfer as PydanticStockTransfer,
)
from katana_public_api_client.models_pydantic._registry import get_pydantic_class
from katana_public_api_client.utils import unwrap_data

from .sync_state import SyncState

# Skip the API call when the cache was synced this recently. Mirrors the
# legacy ``cache_sync._NO_INCREMENTAL_DEBOUNCE`` so back-to-back tool
# calls don't each kick off an HTTP RTT for an empty delta.
_SYNC_DEBOUNCE = timedelta(seconds=300)


def _is_fresh(last_synced: datetime | None) -> bool:
    """True when the cache was synced within ``_SYNC_DEBOUNCE``."""
    if last_synced is None:
        return False
    return (datetime.now(tz=UTC).replace(tzinfo=None) - last_synced) < _SYNC_DEBOUNCE


if TYPE_CHECKING:
    from katana_public_api_client import KatanaClient

    from .engine import TypedCacheEngine


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
    """

    entity_key: str
    api_fn: Any
    cache_cls: type
    pydantic_cls: type
    child_cls: type | None = None
    rows_field: str | None = None
    fk_field: str | None = None
    pydantic_resolver: Callable[[Any], type] | None = None

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
    parent = spec.cache_cls.model_validate(api_obj.model_dump(exclude=exclude))

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

    return parent, children


async def _ensure_synced(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Pull updated rows for one entity from Katana and upsert into the cache.

    Cold-start fetches the full history (cost scales with row count);
    subsequent calls pass ``updated_at_min=<last_synced>`` and typically
    return zero rows. The per-entity lock guarantees only one sync runs
    at a time even if multiple tool calls land concurrently. The
    ``_SYNC_DEBOUNCE`` short-circuit avoids an HTTP RTT for back-to-back
    tool calls.
    """
    async with cache.lock_for(spec.entity_key):
        async with cache.session() as session:
            state = await session.get(SyncState, spec.entity_key)
            last_synced = state.last_synced if state is not None else None

        if _is_fresh(last_synced):
            return

        # ``last_synced`` is persisted as naive UTC (SQLite's default
        # DateTime column strips tzinfo). Re-attach UTC before sending to
        # the API so the generated client serializes an explicit offset.
        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await spec.api_fn.asyncio_detailed(client=client, **kwargs)
        attrs_objs = unwrap_data(response, default=[])

        cached_parents: list[Any] = []
        cached_children: list[Any] = []
        for attrs_obj in attrs_objs:
            parent, children = _convert(spec, attrs_obj)
            cached_parents.append(parent)
            cached_children.extend(children)

        async with cache.session() as session:
            # Parents first so child FK constraints resolve on insert.
            for parent in cached_parents:
                await session.merge(parent)
            for child in cached_children:
                await session.merge(child)
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


# ---------------------------------------------------------------------------
# Per-entity specs
# ---------------------------------------------------------------------------


_SALES_ORDER_SPEC = EntitySpec(
    entity_key="sales_order",
    api_fn=get_all_sales_orders,
    cache_cls=CachedSalesOrder,
    pydantic_cls=PydanticSalesOrder,
    child_cls=CachedSalesOrderRow,
    rows_field="sales_order_rows",
    fk_field="sales_order_id",
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


# Manufacturing orders: the list endpoint returns summary objects with no
# nested rows. Recipe rows live at ``/manufacturing_order_recipe_rows`` and
# aren't cached by this entity's sync — leave the child fields unset.
_MANUFACTURING_ORDER_SPEC = EntitySpec(
    entity_key="manufacturing_order",
    api_fn=get_all_manufacturing_orders,
    cache_cls=CachedManufacturingOrder,
    pydantic_cls=PydanticManufacturingOrder,
)


# Manufacturing-order recipe rows: fetched from the separate
# ``/manufacturing_order_recipe_rows`` endpoint, not nested under the MO
# parent — so they have their own ``updated_at_min`` watermark and sync
# lock. Direct conversion via the pydantic intermediary; ``batch_transactions``
# survives ``model_dump`` as a plain dict list and lands in the cache class's
# JSON column unchanged.
_MANUFACTURING_ORDER_RECIPE_ROW_SPEC = EntitySpec(
    entity_key="manufacturing_order_recipe_row",
    api_fn=get_all_manufacturing_order_recipe_rows,
    cache_cls=CachedManufacturingOrderRecipeRow,
    pydantic_cls=PydanticManufacturingOrderRecipeRow,
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
    await _ensure_synced(client, cache, _MANUFACTURING_ORDER_SPEC)


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
    ``/manufacturing_order_recipe_rows`` endpoint (not nested under the MO
    parent), so they have their own ``updated_at_min`` watermark and sync
    lock — distinct from the manufacturing-orders sync.
    """
    await _ensure_synced(client, cache, _MANUFACTURING_ORDER_RECIPE_ROW_SPEC)
