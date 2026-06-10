"""Cache administration tools for Katana MCP Server.

Operational utilities for the typed cache (``katana_mcp.typed_cache``).

Currently provides ``rebuild_cache``: a destructive force-resync that
truncates the cache tables for a set of cached entity types, clears
their ``SyncState`` watermarks, and re-fetches the live state from
Katana — atomically under the entity's sync lock so concurrent
``list_*`` tools never see the empty intermediate state.

Why this exists: the steady-state sync path upserts via
``session.merge`` and never deletes — soft-deletes from Katana are
folded in correctly because the tombstone surfaces in the next
``updated_at_min`` delta, but rows that left Katana without a
tombstone in our watermarked window (hard deletes, partial syncs,
state predating cache initialization) persist locally as phantoms.
``list_*`` tools filter ``deleted_at IS NULL``, but phantom rows that
never received a soft-delete bump still leak. Rebuild is the manual
escape hatch.

Coverage: every key in ``katana_mcp.typed_cache.ENTITY_SPECS`` is
addressable — both the transactional entities (PO, SO, MO + recipe
rows, stock adjustments, stock transfers) and the catalog entities
(variants, products, materials, services, customers, suppliers,
locations, tax rates, operators, factories, additional costs).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import SQLModel, func, select

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import make_json_result
from katana_mcp.typed_cache import (
    ENTITY_SPECS,
    EntitySpec,
    SyncState,
    TypedCacheEngine,
    force_resync,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params

logger = get_logger(__name__)


# ``CacheEntityType`` mirrors the keys ``katana_mcp.typed_cache.ENTITY_SPECS``
# exposes — kept as a Pydantic ``Literal`` so FastMCP surfaces the closed set
# to clients (and any new entity added to ``ENTITY_SPECS`` shows up here as a
# pyright ``Literal`` mismatch until added below, catching the drift at
# review time rather than runtime).
CacheEntityType = Literal[
    # Transactional entities — parent + nested/related child rows.
    "purchase_order",
    "sales_order",
    "manufacturing_order",
    "stock_adjustment",
    "stock_transfer",
    "bin_transfer",
    # Catalog entities — flat tables, no inline child rows. ``variant``
    # carries denormalized parent-archive state; the rest are simple
    # name/id lookups against the corresponding Katana endpoints.
    "variant",
    "product",
    "material",
    "service",
    "customer",
    "supplier",
    "location",
    "tax_rate",
    "operator",
    "factory",
    "additional_cost",
]


# ============================================================================
# Pydantic models
# ============================================================================


class RebuildCacheRequest(BaseModel):
    """Request model for ``rebuild_cache``."""

    model_config = ConfigDict(extra="forbid")

    entity_types: list[CacheEntityType] = Field(
        ...,
        min_length=1,
        description=(
            "Entity types to rebuild. Each entry truncates the cache "
            "table(s) for that entity, clears its sync watermark, and "
            "re-fetches the live state from Katana. Covers transactional "
            "entities (purchase_order, sales_order, manufacturing_order, "
            "stock_adjustment, stock_transfer, bin_transfer) and catalog "
            "entities "
            "(variant, product, material, service, customer, supplier, "
            "location, tax_rate, operator, factory, additional_cost)."
        ),
    )
    preview: bool = Field(
        default=True,
        description=(
            "If true (default), reports current cache row counts and last-"
            "synced timestamps without modifying anything. If false, "
            "performs the destructive rebuild."
        ),
    )


class EntityRebuildResult(BaseModel):
    """Per-entity rebuild outcome."""

    entity_type: str
    parent_rows_before: int
    child_rows_before: int
    parent_rows_after: int
    child_rows_after: int
    last_synced_before: str | None
    sync_state_keys_cleared: list[str]


class RebuildCacheResponse(BaseModel):
    """Top-level response for ``rebuild_cache``."""

    is_preview: bool
    results: list[EntityRebuildResult]


# ============================================================================
# Implementation
# ============================================================================


def _child_classes(spec: EntitySpec) -> set[type[SQLModel]]:
    """Cache classes that should count as 'children' for one entity.

    Includes the parent's inline ``child_cls`` (PO/SO/MO/stock-adjustment/
    stock-transfer all have one) plus every related spec's ``cache_cls``
    (MO recipe rows, PO/SO row specs). PO/SO row specs share the same
    SQLModel as ``spec.child_cls``; the set dedupes the duplicate.
    """
    classes: set[type[SQLModel]] = set()
    if spec.child_cls is not None:
        classes.add(spec.child_cls)
    for related in spec.related_specs:
        classes.add(related.cache_cls)
    return classes


def _sync_state_keys(spec: EntitySpec) -> list[str]:
    """All ``SyncState`` keys ``force_resync`` clears for one entity."""
    return [spec.entity_key, *(r.entity_key for r in spec.related_specs)]


async def _count_rows(cache: TypedCacheEngine, cls: type[SQLModel]) -> int:
    """Return ``SELECT COUNT(*)`` for one cache table."""
    async with cache.session() as session:
        result = await session.exec(select(func.count()).select_from(cls))
        return int(result.one())


async def _count_child_rows(
    cache: TypedCacheEngine, classes: set[type[SQLModel]]
) -> int:
    """Sum ``COUNT(*)`` across one entity's child tables."""
    total = 0
    for cls in classes:
        total += await _count_rows(cache, cls)
    return total


async def _read_sync_state(cache: TypedCacheEngine, key: str) -> SyncState | None:
    async with cache.session() as session:
        return await session.get(SyncState, key)


async def _rebuild_one(
    client,
    cache: TypedCacheEngine,
    entity_type: str,
    *,
    preview: bool,
) -> EntityRebuildResult:
    """Rebuild a single entity. Counts before/after; runs the truncate +
    re-sync only when ``preview`` is false.

    Atomicity: ``force_resync`` holds the entity's sync lock(s) across both
    the truncate and the cold-start re-pull, so concurrent ``list_*`` calls
    block on the same lock and never observe the empty intermediate state.
    """
    spec = ENTITY_SPECS[entity_type]
    child_classes = _child_classes(spec)

    parent_before = await _count_rows(cache, spec.cache_cls)
    child_before = await _count_child_rows(cache, child_classes)
    state = await _read_sync_state(cache, spec.entity_key)
    last_synced = state.last_synced.isoformat() if state is not None else None

    if preview:
        return EntityRebuildResult(
            entity_type=entity_type,
            parent_rows_before=parent_before,
            child_rows_before=child_before,
            parent_rows_after=parent_before,
            child_rows_after=child_before,
            last_synced_before=last_synced,
            sync_state_keys_cleared=[],
        )

    await force_resync(client, cache, entity_type)

    logger.info(
        "rebuild_cache_resynced",
        entity_type=entity_type,
        parent_rows_before=parent_before,
        child_rows_before=child_before,
    )

    parent_after = await _count_rows(cache, spec.cache_cls)
    child_after = await _count_child_rows(cache, child_classes)

    return EntityRebuildResult(
        entity_type=entity_type,
        parent_rows_before=parent_before,
        child_rows_before=child_before,
        parent_rows_after=parent_after,
        child_rows_after=child_after,
        last_synced_before=last_synced,
        sync_state_keys_cleared=_sync_state_keys(spec),
    )


async def _rebuild_cache_impl(
    request: RebuildCacheRequest, context: Context
) -> RebuildCacheResponse:
    """Run the rebuild for each requested entity type."""
    services = get_services(context)
    results: list[EntityRebuildResult] = []
    for entity_type in request.entity_types:
        result = await _rebuild_one(
            # Bulk resync runs on the dedicated cache-sync client (its own
            # rate-limit budget) when ``KATANA_SYNC_API_KEY`` is configured,
            # mirroring the background warm-up; falls back to the foreground
            # client otherwise. See ``Services.sync_client``.
            services.sync_client,
            services.typed_cache,
            entity_type,
            preview=request.preview,
        )
        results.append(result)
    return RebuildCacheResponse(is_preview=request.preview, results=results)


# ============================================================================
# Public tool
# ============================================================================


@observe_tool
@unpack_pydantic_params
async def rebuild_cache(
    request: Annotated[RebuildCacheRequest, Unpack()], context: Context
) -> ToolResult:
    """Force-rebuild the local typed cache for one or more cached entity types.

    Use this when the local cache has drifted from Katana — the most
    common symptom is "phantom" rows (entities present in the cache
    that no longer exist in Katana). The steady-state sync path
    upserts and never deletes, so phantom rows accumulate when
    Katana drops an entity without a tombstone in our watermarked
    window (hard deletes, partial syncs, state from before the cache
    was initialized).

    For each entity type, the rebuild:
    1. Acquires the per-entity sync locks (parent + every related spec).
    2. Deletes every row in the cache table(s).
    3. Deletes the matching ``sync_state`` watermark row(s).
    4. Re-fetches everything from Katana via ``_sync_one_locked`` for
       the parent and each related spec — all under the still-held
       locks, so concurrent ``list_*`` tools block until the cache is
       repopulated and never see the empty intermediate state.

    **Supported entity types:**

    - Transactional: ``purchase_order``, ``sales_order``,
      ``manufacturing_order``, ``stock_adjustment``, ``stock_transfer``,
      ``bin_transfer`` (each rebuilds the parent table plus its
      child/related-spec tables, e.g. PO + PO rows, MO + MO recipe rows).
    - Catalog: ``variant``, ``product``, ``material``, ``service``,
      ``customer``, ``supplier``, ``location``, ``tax_rate``,
      ``operator``, ``factory``, ``additional_cost`` (flat tables,
      no inline child rows).

    **Two-step flow:**
    - ``preview=true`` (default) — reports current row counts and last-
      synced timestamps without modifying anything.
    - ``preview=false`` — performs the destructive rebuild. Bandwidth
      cost equals one full cold-start sync per entity type
      (paginated via the auto-pagination transport).

    **Caveats:**
    - Destructive: cache row count drops to zero between truncate and
      re-pull, but concurrent ``list_*`` calls block on the sync lock
      until the re-pull completes — they observe the rebuilt cache,
      not the empty intermediate.
    - Not transactional across entity types: each entity type is
      rebuilt sequentially. If the resync for entity B fails after
      entity A succeeded, A is already rebuilt.
    """
    response = await _rebuild_cache_impl(request, context)
    return make_json_result(response)


def register_tools(mcp: FastMCP) -> None:
    """Register cache administration tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"cache", "admin", "destructive"}, annotations=_destructive)(
        rebuild_cache
    )
