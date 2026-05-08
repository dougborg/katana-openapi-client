"""Decorators for MCP tool infrastructure.

Provides cache-aware decorators that handle sync and invalidation,
keeping tool implementations focused on business logic.

Usage::

    @cache_read(CachedVariant)
    async def _search_items_impl(request, context):
        services = get_services(context)
        return await services.cache.smart_search("variant", request.query)


    @cache_write("product", "variant")
    async def _create_item_impl(request, context):
        services = get_services(context)
        return await services.client.products.create(...)

The ``cache_read`` decorator now keys off the typed-cache ``Cached*``
classes (``CachedVariant``, ``CachedProduct``, …) instead of the legacy
``EntityType`` enum. During the #472 unification rollout the decorator
runs **both** the legacy ``cache_sync.ensure_*_synced`` helper and the
typed ``typed_cache.ensure_*_synced`` helper for each registered class
so tool bodies see fresh data on either path. Phase D drops the legacy
half along with the call sites that read from ``services.cache``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, cast

from katana_mcp.services import get_services

if TYPE_CHECKING:
    from sqlmodel import SQLModel

    from katana_mcp.services.dependencies import Services


# Lazy-initialized cache of sync functions (avoids circular imports).
# Keys are typed-cache ``Cached*`` classes; values are async wrappers
# that fan out to the legacy ``cache_sync.ensure_*_synced(services)``
# AND the typed ``typed_cache.ensure_*_synced(client, typed_cache)``
# helpers (#472 Phase C). Phase D drops the legacy half.
_sync_fns: dict[type[SQLModel], Callable[[Services], Awaitable[None]]] | None = None

# (Cached* class, ensure-helper stem) — both ``cache_sync`` and ``typed_cache``
# expose ``ensure_<stem>_synced``, differing only in argument shape (legacy
# takes ``services``; typed takes ``client, cache``). The dual wrapper in
# ``_get_sync_fns`` resolves the stem against both modules.
_DUAL_SYNC_REGISTRY: tuple[tuple[str, str], ...] = (
    ("CachedVariant", "variants"),
    ("CachedProduct", "products"),
    ("CachedMaterial", "materials"),
    ("CachedService", "services"),
    ("CachedSupplier", "suppliers"),
    ("CachedCustomer", "customers"),
    ("CachedLocation", "locations"),
    ("CachedTaxRate", "tax_rates"),
    ("CachedOperator", "operators"),
    ("CachedFactory", "factory"),
    ("CachedAdditionalCost", "additional_costs"),
)


def _get_sync_fns() -> dict[type[SQLModel], Callable[[Services], Awaitable[None]]]:
    """Get the ``Cached*`` class → dual-sync wrapper mapping (initialized once).

    Each wrapper runs the legacy ``cache_sync.ensure_<stem>_synced(services)``
    and the typed ``typed_cache.ensure_<stem>_synced(client, typed_cache)``
    concurrently via ``asyncio.gather`` so both caches stay populated during
    the Phase C → Phase D transition without serializing two API fetches.
    The registry is tiny on purpose — Phase D removes the legacy half.
    """
    global _sync_fns  # noqa: PLW0603
    if _sync_fns is None:
        from katana_mcp import cache_sync, typed_cache
        from katana_public_api_client.models_pydantic import _generated as cached_models

        def _dual(
            legacy: Callable[[Services], Awaitable[None]],
            typed: Callable[..., Awaitable[None]],
        ) -> Callable[[Services], Awaitable[None]]:
            async def _wrapped(services: Services) -> None:
                await asyncio.gather(
                    legacy(services),
                    typed(services.client, services.typed_cache),
                )

            return _wrapped

        _sync_fns = {
            getattr(cached_models, cls_name): _dual(
                getattr(cache_sync, f"ensure_{stem}_synced"),
                getattr(typed_cache, f"ensure_{stem}_synced"),
            )
            for cls_name, stem in _DUAL_SYNC_REGISTRY
        }
    return _sync_fns


def cache_read(*entity_classes: type[SQLModel]) -> Callable:
    """Sync cache for the given typed ``Cached*`` classes before running the tool.

    For each class the decorator looks up the registered sync wrapper in
    ``_get_sync_fns()`` and awaits it. Each wrapper currently fans out to
    BOTH the legacy ``CatalogCache`` sync helper AND the typed-cache
    ``ensure_*_synced`` helper so tool bodies see fresh data on either
    path during the #472 unification rollout. Phase D drops the legacy
    half along with the ``services.cache`` call sites.

    Unknown classes raise ``ValueError`` at decoration time so a typo
    fails at import, not silently as a stale-cache read at first call.

    Args:
        *entity_classes: Typed ``Cached*`` classes to sync (e.g.,
            ``CachedVariant``, ``CachedProduct``).
    """
    # Fail fast at decoration time so a typo blows up at import, not as
    # a silent stale-cache read on the first request. Tests that swap
    # ``decorators._sync_fns`` in autouse fixtures still get the live
    # mocks at call time — the wrapper re-resolves through
    # ``_get_sync_fns()``.
    registered = _get_sync_fns()
    unknown = [cls for cls in entity_classes if cls not in registered]
    if unknown:
        names = ", ".join(cls.__name__ for cls in unknown)
        known = ", ".join(sorted(c.__name__ for c in registered))
        raise ValueError(
            f"@cache_read: unregistered Cached* class(es): {names}. "
            f"Registered classes: {known}."
        )

    def decorator[F: Callable[..., Any]](fn: F) -> F:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            context = kwargs.get("context") or args[-1]
            services = get_services(context)

            sync_fns = _get_sync_fns()
            for cls in entity_classes:
                sync_fn = sync_fns.get(cls)
                if sync_fn is not None:
                    await sync_fn(services)

            return await fn(*args, **kwargs)

        return cast("F", wrapper)

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

        return cast("F", wrapper)

    return decorator
