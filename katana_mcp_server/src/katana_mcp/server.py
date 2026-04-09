"""Katana MCP Server - FastMCP server with environment-based authentication.

This module implements the core MCP server for Katana Manufacturing ERP,
providing tools, resources, and prompts for interacting with the Katana API.

Features:
- Environment-based authentication (KATANA_API_KEY)
- Automatic client initialization with error handling
- Lifespan management for KatanaClient context
- Production-ready with transport-layer resilience
- Structured logging with observability
- Response caching for improved performance (FastMCP 2.13+)
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.middleware.caching import (
    CallToolSettings,
    ReadResourceSettings,
    ResponseCachingMiddleware,
)
from key_value.aio.stores.memory import MemoryStore

from katana_mcp import __version__
from katana_mcp._fastmcp_patches import apply_fastmcp_patches as _apply_patches
from katana_mcp.logging import get_logger, setup_logging
from katana_mcp.services import Services
from katana_public_api_client import KatanaClient

# Apply FastMCP patches for Pydantic 2.12+ compatibility BEFORE registering tools
_apply_patches()

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[Services]:
    """Manage server lifespan and KatanaClient lifecycle.

    This context manager:
    1. Loads environment variables from .env file
    2. Validates required configuration (KATANA_API_KEY)
    3. Initializes KatanaClient with error handling
    4. Provides client to tools via ServerContext
    5. Ensures proper cleanup on shutdown

    Args:
        server: FastMCP server instance

    Yields:
        Services: Context object containing initialized KatanaClient

    Raises:
        ValueError: If KATANA_API_KEY environment variable is not set
        Exception: If KatanaClient initialization fails
    """
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    api_key = os.getenv("KATANA_API_KEY")
    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

    # Validate required configuration
    if not api_key:
        logger.error(
            "authentication_failed",
            reason="KATANA_API_KEY environment variable is required",
            message="Please set it in your .env file or environment.",
        )
        raise ValueError(
            "KATANA_API_KEY environment variable is required for authentication"
        )

    logger.info("server_initializing", version=__version__, base_url=base_url)

    try:
        # Initialize KatanaClient with automatic resilience features
        async with KatanaClient(
            api_key=api_key,
            base_url=base_url,
            timeout=30.0,
            max_retries=5,
            max_pages=100,
        ) as client:
            logger.info(
                "client_initialized",
                timeout=30.0,
                max_retries=5,
                max_pages=100,
            )

            # Initialize persistent catalog cache
            from katana_mcp.cache import CatalogCache

            cache = CatalogCache()
            await cache.open()
            logger.info("cache_initialized", db_path=str(cache.db_path))

            try:
                # Create context with client and cache for tools to access
                context = Services(client=client, cache=cache)  # type: ignore[arg-type]

                # Yield context to server - tools can access via lifespan dependency
                logger.info("server_ready", version=__version__)
                yield context
            finally:
                await cache.close()
                logger.info("cache_closed")

    except ValueError as e:
        # Authentication or configuration errors
        logger.error("initialization_failed", error_type="ValueError", error=str(e))
        raise
    except Exception as e:
        # Unexpected errors during initialization
        # Note: exc_info intentionally omitted to avoid leaking file paths and
        # module internals in production logs. The exception is re-raised for
        # the caller to handle debugging.
        logger.error(
            "initialization_failed",
            error_type=type(e).__name__,
            error=str(e),
        )
        raise
    finally:
        logger.info("server_shutting_down")


# Initialize FastMCP server with lifespan management
mcp = FastMCP(
    name="katana-erp",
    version=__version__,
    lifespan=lifespan,
    instructions="""\
Katana MCP Server — Manufacturing ERP tools for inventory, orders, and production.

## Domain Model

- **Items** are things with SKUs: products (sellable finished goods), materials
  (raw materials/components for manufacturing), and services.
- Each item has one or more **variants** identified by variant_id. Variants carry
  pricing, barcodes, supplier codes, and configuration attributes.
- **Orders** reference items by variant_id (not SKU). Always use search_items or
  get_variant_details to look up variant IDs before creating orders.
- **Locations** are warehouses/facilities. Orders and inventory are location-scoped.
- **Suppliers** provide materials via purchase orders.

## Tool Selection Guide

**Finding items:**
  search_items → get_variant_details → check_inventory

**Creating items:**
  create_product (finished goods) | create_material (raw materials) | create_item (services)

**Purchasing:**
  create_purchase_order → verify_order_document → receive_purchase_order

**Sales:**
  create_sales_order → fulfill_order (order_type="sales")

**Manufacturing:**
  create_manufacturing_order → fulfill_order (order_type="manufacturing")

**Inventory monitoring:**
  list_low_stock_items → check_inventory

## Safety Pattern

All create/modify/delete operations use a two-step confirm pattern:
1. Call with confirm=false — returns a preview (no changes made)
2. Call with confirm=true — executes the operation (prompts for user confirmation)

## Resources

Browse current state without making changes:
- katana://inventory/items — full catalog with item types
- katana://inventory/stock-movements — recent transfers and adjustments
- katana://sales-orders — open sales orders
- katana://purchase-orders — open purchase orders
- katana://manufacturing-orders — active production orders
- katana://help — detailed workflow guides and tool reference
""",
)

# Add response caching middleware with TTLs for read-only tools
_READ_ONLY_TOOLS = [
    "search_items",
    "get_item",
    "get_variant_details",
    "check_inventory",
    "list_low_stock_items",
    "verify_order_document",
]

mcp.add_middleware(
    ResponseCachingMiddleware(
        cache_storage=MemoryStore(),
        call_tool_settings=CallToolSettings(
            ttl=30,
            included_tools=_READ_ONLY_TOOLS,
        ),
        read_resource_settings=ReadResourceSettings(ttl=60),
    )
)
logger.info(
    "middleware_added",
    middleware="ResponseCachingMiddleware",
    storage="MemoryStore",
    cached_tools=_READ_ONLY_TOOLS,
    tool_ttl=30,
    resource_ttl=60,
)

# Register all tools, resources, and prompts with the mcp instance
# This must come after mcp initialization
from katana_mcp.prompts import register_all_prompts  # noqa: E402
from katana_mcp.resources import register_all_resources  # noqa: E402
from katana_mcp.tools import register_all_tools  # noqa: E402

register_all_tools(mcp)
register_all_resources(mcp)
register_all_prompts(mcp)


def main(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8765) -> None:
    """Main entry point for the Katana MCP Server.

    This function is called when running the server via:
    - uvx katana-mcp-server
    - python -m katana_mcp
    - katana-mcp-server (console script)

    Args:
        transport: Transport protocol ("stdio", "sse", or "http"). Default: "stdio"
        host: Host to bind to for HTTP/SSE transports. Default: "127.0.0.1"
        port: Port to bind to for HTTP/SSE transports. Default: 8765
    """
    logger.info(
        "server_starting",
        version=__version__,
        transport=transport,
        host=host,
        port=port,
    )
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
