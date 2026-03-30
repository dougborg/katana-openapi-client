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

from katana_mcp.services import get_services


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
            # Find context in args (it's always the last positional or 'context' kwarg)
            context = kwargs.get("context") or args[-1]
            services = get_services(context)

            # Import sync functions lazily to avoid circular imports
            from katana_mcp.cache_sync import (
                ensure_customers_synced,
                ensure_locations_synced,
                ensure_materials_synced,
                ensure_operators_synced,
                ensure_products_synced,
                ensure_services_synced,
                ensure_suppliers_synced,
                ensure_tax_rates_synced,
                ensure_variants_synced,
            )

            sync_fns = {
                "variant": ensure_variants_synced,
                "product": ensure_products_synced,
                "material": ensure_materials_synced,
                "service": ensure_services_synced,
                "supplier": ensure_suppliers_synced,
                "customer": ensure_customers_synced,
                "location": ensure_locations_synced,
                "tax_rate": ensure_tax_rates_synced,
                "operator": ensure_operators_synced,
            }

            for entity_type in entity_types:
                sync_fn = sync_fns.get(entity_type)
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
