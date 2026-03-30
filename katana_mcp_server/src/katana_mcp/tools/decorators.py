"""Decorators for MCP tool infrastructure.

Provides cache-aware decorators that handle sync and invalidation,
keeping tool implementations focused on business logic.

Usage::

    @cache_read("variant")
    async def _search_items_impl(request, context):
        services = get_services(context)
        return await services.cache.smart_search("variant", request.query)


    @cache_write("product", "variant")
    async def _create_item_impl(request, context):
        services = get_services(context)
        return await services.client.products.create(...)
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from katana_mcp.cache import EntityType
from katana_mcp.services import get_services

# Lazy-initialized cache of sync functions (avoids circular imports)
_sync_fns: dict[str, Any] | None = None


def _get_sync_fns() -> dict[str, Any]:
    """Get the entity-type → sync function mapping (initialized once)."""
    global _sync_fns  # noqa: PLW0603
    if _sync_fns is None:
        from katana_mcp.cache_sync import (
            ensure_customers_synced,
            ensure_factory_synced,
            ensure_locations_synced,
            ensure_materials_synced,
            ensure_operators_synced,
            ensure_products_synced,
            ensure_services_synced,
            ensure_suppliers_synced,
            ensure_tax_rates_synced,
            ensure_variants_synced,
        )

        _sync_fns = {
            EntityType.VARIANT: ensure_variants_synced,
            EntityType.PRODUCT: ensure_products_synced,
            EntityType.MATERIAL: ensure_materials_synced,
            EntityType.SERVICE: ensure_services_synced,
            EntityType.SUPPLIER: ensure_suppliers_synced,
            EntityType.CUSTOMER: ensure_customers_synced,
            EntityType.LOCATION: ensure_locations_synced,
            EntityType.TAX_RATE: ensure_tax_rates_synced,
            EntityType.OPERATOR: ensure_operators_synced,
            EntityType.FACTORY: ensure_factory_synced,
        }
    return _sync_fns


def cache_read(*entity_types: str) -> Callable:
    """Sync cache for entity types before executing the tool.

    Calls ``ensure_{type}_synced(services)`` for each entity type before
    running the decorated function. The function receives a context with
    a guaranteed-fresh cache.

    Args:
        *entity_types: Entity type names to sync (e.g., "variant", "product").
    """

    def decorator[F: Callable[..., Any]](fn: F) -> F:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            context = kwargs.get("context") or args[-1]
            services = get_services(context)

            sync_fns = _get_sync_fns()
            for et in entity_types:
                # EntityType is a StrEnum — normalize to ensure dict lookup works
                key = EntityType(et) if not isinstance(et, EntityType) else et
                sync_fn = sync_fns.get(key)
                if sync_fn:
                    await sync_fn(services)

            return await fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def cache_write(*entity_types: str) -> Callable:
    """Invalidate cache for entity types after a successful write.

    Runs the decorated function normally. On success, marks the specified
    entity types dirty so the next read triggers an incremental sync.
    On exception, does NOT invalidate (the write didn't succeed).

    Args:
        *entity_types: Entity type names to invalidate (e.g., "product", "variant").
    """

    def decorator[F: Callable[..., Any]](fn: F) -> F:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await fn(*args, **kwargs)

            # Invalidate on success
            context = kwargs.get("context") or args[-1]
            services = get_services(context)
            cache = getattr(services, "cache", None)
            if cache:
                for entity_type in entity_types:
                    await cache.mark_dirty(entity_type)

            return result

        return wrapper  # type: ignore[return-value]

    return decorator
