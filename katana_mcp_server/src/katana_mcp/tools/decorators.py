"""Decorators for MCP tool infrastructure.

Provides cache-aware decorators that handle sync and invalidation,
keeping tool implementations focused on business logic.

Usage::

    @cache_read(CachedVariant)
    async def _search_items_impl(request, context):
        services = get_services(context)
        return await services.typed_cache.catalog.smart_search(
            CachedVariant, request.query
        )
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, cast

from katana_mcp.services import get_services

if TYPE_CHECKING:
    from sqlmodel import SQLModel

    from katana_mcp.services.dependencies import Services
    from katana_mcp.typed_cache import TypedCacheEngine
    from katana_public_api_client import KatanaClient


# Lazy-initialized registry: ``Cached*`` class → ``ensure_<entity>_synced``.
# The ``ensure_*`` helpers live in ``katana_mcp.typed_cache.sync``; importing
# them at module load time would force ``sqlmodel`` and friends in before
# the dependency-injection lifespan is wired up, so we defer the lookup
# until the decorator first runs.
_sync_fns: dict[type[Any], Any] | None = None


def _get_sync_fns() -> dict[type[Any], Any]:
    """Get the ``Cached*`` class → sync function mapping (initialized once).

    Indexed by class identity rather than ``StrEnum`` value because
    Phase D retired the ``EntityType`` enum in favor of the typed
    ``Cached*`` siblings — every catalog entity now has exactly one
    ``Cached*`` SQLModel class that doubles as its registry key.
    """
    global _sync_fns  # noqa: PLW0603
    if _sync_fns is None:
        from katana_mcp.typed_cache.sync import (
            ensure_additional_costs_synced,
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
        from katana_public_api_client.models_pydantic._generated import (
            CachedAdditionalCost,
            CachedCustomer,
            CachedFactory,
            CachedLocation,
            CachedMaterial,
            CachedOperator,
            CachedProduct,
            CachedService,
            CachedSupplier,
            CachedTaxRate,
            CachedVariant,
        )

        _sync_fns = {
            CachedVariant: ensure_variants_synced,
            CachedProduct: ensure_products_synced,
            CachedMaterial: ensure_materials_synced,
            CachedService: ensure_services_synced,
            CachedSupplier: ensure_suppliers_synced,
            CachedCustomer: ensure_customers_synced,
            CachedLocation: ensure_locations_synced,
            CachedTaxRate: ensure_tax_rates_synced,
            CachedOperator: ensure_operators_synced,
            CachedFactory: ensure_factory_synced,
            CachedAdditionalCost: ensure_additional_costs_synced,
        }
    return _sync_fns


async def _run_sync(
    services: Services, sync_fn: Callable[[KatanaClient, TypedCacheEngine], Any]
) -> None:
    """Invoke a typed-cache ``ensure_<entity>_synced`` helper.

    The typed-cache helpers take ``(client, cache)`` rather than the
    ``Services`` container so they're usable outside the MCP tool
    surface (cookbook recipes, ad-hoc scripts). The decorator bridges
    the two shapes here so call sites remain
    ``@cache_read(CachedVariant)`` without a ``services``-aware wrapper.
    """
    await sync_fn(services.client, services.typed_cache)


async def ensure_cache_synced(
    services: Services, *cached_classes: type[SQLModel]
) -> None:
    """Imperatively sync ``Cached*`` classes — the runtime twin of ``@cache_read``.

    For syncs a decorator can't express because the need is *conditional* on
    the tool's own results: ``search_items`` only needs the service table when
    a service actually appears in the result set, which it can't know until
    after the variant search runs. Routed through the same ``_get_sync_fns()``
    registry as the decorator, so tests that patch ``_sync_fns`` (e.g. the
    ``_patch_cache_sync`` fixture) neutralize it for free.

    Unlike ``@cache_read`` — which validates eagerly and raises ``ValueError``
    at decoration time for an unregistered ``Cached*`` class — this runtime
    helper silently skips classes absent from the registry. That difference is
    deliberate: the decorator's classes are import-time literals (a typo should
    fail loudly at import), whereas here a class can be legitimately absent at
    call time (the ``_patch_cache_sync`` fixture swaps in a registry that omits
    ``CachedService``), and skipping is exactly how that no-ops in tests.
    """
    sync_fns = _get_sync_fns()
    for cached_cls in cached_classes:
        sync_fn = sync_fns.get(cached_cls)
        if sync_fn is not None:
            await _run_sync(services, sync_fn)


def cache_read(*cached_classes: type[SQLModel]) -> Callable:
    """Sync the typed cache for given ``Cached*`` classes before the tool runs.

    Calls ``ensure_<entity>_synced(client, typed_cache)`` for each class
    before invoking the decorated function. The function receives a
    context with a guaranteed-fresh cache.

    Unknown classes raise ``ValueError`` at decoration time so a typo
    fails at import, not silently as a stale-cache read at first call.

    Args:
        *cached_classes: ``Cached*`` SQLModel classes to sync (e.g.,
            ``CachedVariant``, ``CachedProduct``).
    """
    # Fail fast at decoration time so a typo blows up at import, not as
    # a silent stale-cache read on the first request. Tests that swap
    # ``decorators._sync_fns`` in autouse fixtures still get the live
    # mocks at call time — the wrapper re-resolves through
    # ``_get_sync_fns()``.
    registered = _get_sync_fns()
    unknown = [cls for cls in cached_classes if cls not in registered]
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
            for cached_cls in cached_classes:
                sync_fn = sync_fns.get(cached_cls)
                if sync_fn is not None:
                    await _run_sync(services, sync_fn)

            return await fn(*args, **kwargs)

        return cast("F", wrapper)

    return decorator
