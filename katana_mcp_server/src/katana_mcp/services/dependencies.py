"""Dependency injection helpers for MCP tools.

This module provides a clean pattern for extracting services from the MCP context,
following the StockTrim architecture pattern.
"""

from dataclasses import dataclass

from fastmcp import Context

from katana_mcp.typed_cache import TypedCacheEngine
from katana_public_api_client import KatanaClient


@dataclass
class Services:
    """Container for services available to tools.

    This dataclass provides type-safe access to services that tools need.
    The same instance is used as the server lifespan context (yielded by
    the lifespan function in server.py) and returned by get_services().

    Attributes:
        client: The KatanaClient instance for foreground API operations
            (interactive tool calls + lazy on-demand cache syncs).
        typed_cache: ``TypedCacheEngine`` — SQLModel-backed per-entity tables
            covering both transactional types (sales orders, manufacturing
            orders, purchase orders, stock adjustments/transfers, MO recipe
            rows) and the catalog tier (variants, products, materials,
            services, suppliers, customers, locations, tax rates, operators,
            factories, additional costs). Powers cache-backed ``list_*``
            tools, the ``search_items`` / ``get_variant_details`` lookups
            via ``typed_cache.catalog`` (a :class:`CatalogQueries` adapter),
            and the FTS5 sidecar search.
        dedicated_sync_client: Optional client dedicated to *bulk* cache
            (re)build work — the background warm-up and the ``rebuild_cache``
            tool. Set from ``KATANA_SYNC_API_KEY`` so that work spends a
            separate per-key rate-limit budget (Katana meters per API key,
            not per tenant), keeping its bursty multi-page pagination — and
            the reset-gate stalls it triggers — off the foreground budget.
            ``None`` means no isolation was configured; :attr:`sync_client`
            then resolves to :attr:`client`. Consumers should read
            :attr:`sync_client`, never this field directly.

    The legacy ``CatalogCache`` (previously exposed here as ``cache``) was
    decommissioned in #472 Phase D once ``services.typed_cache.catalog``
    fully replaced its read API and the catalog ``EntitySpec`` pipeline
    fully replaced its sync helpers.
    """

    client: KatanaClient
    typed_cache: TypedCacheEngine
    dedicated_sync_client: KatanaClient | None = None

    @property
    def sync_client(self) -> KatanaClient:
        """Client for bulk cache (re)build work.

        Resolves to :attr:`dedicated_sync_client` when a ``KATANA_SYNC_API_KEY``
        was configured, otherwise falls back to the foreground :attr:`client`.
        Always returns a usable client, so callers never branch on ``None``.
        """
        return self.dedicated_sync_client or self.client


def get_services(context: Context) -> Services:
    """Extract services from MCP context.

    This helper provides a single extraction point for all service dependencies,
    making tool implementations cleaner and more testable.

    Usage in tools:
        ```python
        services = get_services(context)

        # Use existing helpers (variants, products, materials, services)
        products = await services.client.products.list()

        # For other endpoints (purchase_orders, sales_orders, etc), use generated API:
        from katana_public_api_client.api.purchase_order import (
            create_purchase_order,
        )

        po_response = await create_purchase_order.asyncio_detailed(
            client=services.client, json_body=...
        )
        ```

    Note:
        Only a limited set of helpers currently exist on KatanaClient:
        - variants
        - products
        - materials
        - services

        For inventory and all other endpoints (purchase_orders, manufacturing_orders,
        sales_orders), use the generated API modules directly from
        katana_public_api_client.api.* or implement your own helper methods.

    Args:
        context: FastMCP context containing lifespan_context with Services

    Returns:
        Services: The lifespan context containing client and other services
    """
    if context.request_context is None:
        raise RuntimeError(
            "get_services() called outside a request context — "
            "services are only available during tool/resource invocations"
        )
    return context.request_context.lifespan_context
