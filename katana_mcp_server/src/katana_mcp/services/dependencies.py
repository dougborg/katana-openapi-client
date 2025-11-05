"""Dependency injection helpers for MCP tools.

This module provides a clean pattern for extracting services from the MCP context,
following the StockTrim architecture pattern.
"""

from dataclasses import dataclass

from fastmcp import Context

from katana_public_api_client import KatanaClient


@dataclass
class Services:
    """Container for services available to tools.

    This dataclass provides type-safe access to services that tools need.
    Currently contains only the KatanaClient, but can be extended with
    additional services as needed.

    Attributes:
        client: The KatanaClient instance for API operations
    """

    client: KatanaClient


def get_services(context: Context) -> Services:
    """Extract services from MCP context.

    This helper provides a single extraction point for all service dependencies,
    making tool implementations cleaner and more testable.

    Usage in tools:
        ```python
        services = get_services(context)

        # Use existing helpers (variants, products, materials, services, inventory)
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
        - inventory

        For other endpoints (purchase_orders, manufacturing_orders, sales_orders),
        you must use the generated API modules directly from katana_public_api_client.api.*
        or implement your own helper methods.

    Args:
        context: FastMCP context containing lifespan_context with ServerContext

    Returns:
        Services: Dataclass containing client and other services
    """
    server_context = context.request_context.lifespan_context
    return Services(client=server_context.client)
