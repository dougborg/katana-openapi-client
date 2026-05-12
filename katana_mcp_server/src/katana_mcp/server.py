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

import asyncio
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from fastmcp.server.auth import AuthProvider  # pragma: no cover

    from katana_mcp.typed_cache import TypedCacheEngine  # pragma: no cover

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
from katana_mcp.middleware import JsonStringCoercionMiddleware
from katana_mcp.services import Services
from katana_public_api_client import KatanaClient

# Apply FastMCP patches for Pydantic 2.12+ compatibility BEFORE registering tools
_apply_patches()

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


async def _warm_caches_in_background(
    client: KatanaClient,
    typed_cache: "TypedCacheEngine",
) -> None:
    """Kick off ``ensure_<entity>_synced`` for every cache-backed entity.

    Runs concurrently with the server accepting MCP requests so the gap
    between Claude/MCP startup and the first user-facing tool call gets
    used to warm the typed cache. Tool calls that arrive mid-warmup
    serialize on each entity's ``cache.lock_for(...)`` — they wait the
    same amount of time they would have waited without warmup, with the
    warmup's incremental progress available on later calls (closes #500's
    cold-cache window, the remaining mitigation for #463 after #592 and
    #591).

    Per-entity failures are swallowed and logged so a transient error on
    one entity never blocks the others from warming and never crashes
    the server. ``manufacturing_order_recipe_row`` is pulled implicitly
    via ``MANUFACTURING_ORDER_SPEC.related_specs`` when MOs are warmed,
    so it's intentionally absent from this list.
    """
    from katana_mcp.typed_cache import (
        ensure_additional_costs_synced,
        ensure_customers_synced,
        ensure_factory_synced,
        ensure_locations_synced,
        ensure_manufacturing_orders_synced,
        ensure_materials_synced,
        ensure_operators_synced,
        ensure_products_synced,
        ensure_purchase_orders_synced,
        ensure_sales_orders_synced,
        ensure_services_synced,
        ensure_stock_adjustments_synced,
        ensure_stock_transfers_synced,
        ensure_suppliers_synced,
        ensure_tax_rates_synced,
        ensure_variants_synced,
    )

    helpers = (
        ensure_sales_orders_synced,
        ensure_purchase_orders_synced,
        ensure_manufacturing_orders_synced,
        ensure_stock_adjustments_synced,
        ensure_stock_transfers_synced,
        ensure_customers_synced,
        ensure_suppliers_synced,
        ensure_locations_synced,
        ensure_tax_rates_synced,
        ensure_operators_synced,
        ensure_additional_costs_synced,
        ensure_variants_synced,
        ensure_products_synced,
        ensure_materials_synced,
        ensure_services_synced,
        ensure_factory_synced,
    )

    started = time.monotonic()
    # ``return_exceptions=True`` keeps the gather alive when any one
    # helper raises, so a transient API hiccup on one entity doesn't
    # block the others from warming. ``CancelledError`` propagates
    # through ``gather`` regardless of this flag, which is what we want
    # on shutdown.
    results = await asyncio.gather(
        *(fn(client, typed_cache) for fn in helpers),
        return_exceptions=True,
    )
    elapsed_s = round(time.monotonic() - started, 1)
    failures = [
        (fn.__name__, type(r).__name__, str(r))
        for fn, r in zip(helpers, results, strict=True)
        if isinstance(r, BaseException)
    ]
    if failures:
        logger.warning(
            "cache_warmup_partial",
            elapsed_s=elapsed_s,
            success_count=len(helpers) - len(failures),
            failure_count=len(failures),
            failures=failures,
        )
    else:
        logger.info(
            "cache_warmup_complete",
            elapsed_s=elapsed_s,
            entity_count=len(helpers),
        )


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

            # Initialize the SQLModel-backed typed cache (#342 + #472) —
            # one store covering both transactional and catalog tiers.
            # The legacy ``CatalogCache`` was retired in #472 Phase D.
            from katana_mcp.typed_cache import TypedCacheEngine

            typed_cache = TypedCacheEngine()
            await typed_cache.open()
            logger.info("typed_cache_initialized", db_path=str(typed_cache.db_path))

            # Fire-and-forget background warm-up so the gap between
            # MCP startup and the first user-facing tool call gets used
            # to populate the typed cache. Default ON; set
            # ``MCP_DISABLE_CACHE_WARMUP=1`` to skip (test runs do this
            # via the autouse fixture in ``conftest.py``).
            warmup_task: asyncio.Task[None] | None = None
            if os.getenv("MCP_DISABLE_CACHE_WARMUP") != "1":
                warmup_task = asyncio.create_task(
                    _warm_caches_in_background(cast(KatanaClient, client), typed_cache),
                    name="katana_cache_warmup",
                )
                logger.info("cache_warmup_started")

            try:
                # The generated ``AuthenticatedClient.__aenter__`` is
                # annotated to return its own class, dropping the
                # ``KatanaClient`` subclass we constructed.
                context = Services(
                    client=cast(KatanaClient, client),
                    typed_cache=typed_cache,
                )
                logger.info("server_ready", version=__version__)
                yield context
            finally:
                # Always await the warmup task on shutdown, regardless of
                # done-state, so any exception it raised is consumed
                # rather than emitted as an asyncio "Task exception was
                # never retrieved" warning. If still running, cancel
                # first so the await returns promptly. Awaiting before
                # ``typed_cache.close()`` also prevents the warmup from
                # writing against a closed engine.
                if warmup_task is not None:
                    if not warmup_task.done():
                        warmup_task.cancel()
                    try:
                        await warmup_task
                    except asyncio.CancelledError:
                        logger.info("cache_warmup_cancelled")
                    except Exception as exc:
                        # ``_warm_caches_in_background`` already swallows
                        # per-helper errors via ``return_exceptions=True``,
                        # so reaching this branch means something
                        # unexpected raised at the task scope (import
                        # error, logging failure, programmer bug).
                        logger.warning(
                            "cache_warmup_task_raised",
                            error_type=type(exc).__name__,
                            error=str(exc),
                        )
                await typed_cache.close()
                logger.info("typed_cache_closed")

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


def _build_auth() -> "AuthProvider | None":
    """Build auth provider from environment configuration.

    Supports two modes, selected by environment variables:
    - MCP_AUTH_TOKEN: Simple bearer token auth (dev/personal use)
    - MCP_GITHUB_CLIENT_ID + MCP_GITHUB_CLIENT_SECRET + MCP_BASE_URL: GitHub OAuth

    Returns None when no auth env vars are set (unauthenticated).
    """
    github_id = os.getenv("MCP_GITHUB_CLIENT_ID")
    github_secret = os.getenv("MCP_GITHUB_CLIENT_SECRET")
    base_url = os.getenv("MCP_BASE_URL")

    github_vars = {
        "MCP_GITHUB_CLIENT_ID": github_id,
        "MCP_GITHUB_CLIENT_SECRET": github_secret,
        "MCP_BASE_URL": base_url,
    }
    if github_id and github_secret and base_url:
        from fastmcp.server.auth.providers.github import GitHubProvider

        return GitHubProvider(
            client_id=github_id,
            client_secret=github_secret,
            base_url=base_url,
        )
    if any(github_vars.values()):
        missing = [k for k, v in github_vars.items() if not v]
        logger.warning(
            "incomplete_github_oauth_config",
            missing=missing,
            msg="Set all three vars for GitHub OAuth, or remove them for bearer token",
        )

    token = os.getenv("MCP_AUTH_TOKEN")
    if token:
        from fastmcp.server.auth import StaticTokenVerifier

        return StaticTokenVerifier(
            tokens={token: {"client_id": "katana-mcp", "scopes": ["all"]}},
        )

    return None


_auth = _build_auth()

# Initialize FastMCP server with lifespan management
mcp = FastMCP(
    name="katana-erp",
    version=__version__,
    lifespan=lifespan,
    auth=_auth,
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

All create/modify/delete operations use a two-step preview/apply pattern:
1. Call with preview=true (default) — returns a preview (no changes made)
2. Call with preview=false — executes the operation

Destructive tools advertise this via the standard MCP ``destructiveHint``
tool annotation, which the host uses to confirm with the user before
invocation. The server itself does not gate further.

## Resource URLs

Tool responses include a `katana_url` field where applicable — prefer it
over composing URLs yourself. Patterns (base: factory.katanamrp.com,
overridable via `KATANA_WEB_BASE_URL`):

  /salesorder/{id}              — sales orders
  /manufacturingorder/{id}      — manufacturing orders
  /purchaseorder/{id}           — purchase orders
  /product/{id}                 — products (variants link to the parent)
  /material/{id}                — materials (variants link to the parent)
  /contacts/customers/{id}      — customers
  /stocktransfer/{id}           — stock transfers
  /stockadjustment/{id}         — stock adjustments

Top-level pages: /inventory, /sales, /purchases, /manufacturingorders.

## Resources

Browse cached catalog:
- katana://inventory/items — full catalog (products, materials, services)
- katana://help — detailed workflow guides and tool reference

For reference data (suppliers, locations, tax rates, operators, additional
costs), use the parameterized search tools: `list_suppliers(query=...)`,
`list_locations(query=...)`, `list_tax_rates(query=...)`,
`list_operators(query=...)`, `list_additional_costs(query=...)`. They
support fuzzy name search and bounded output. Use `get_supplier(supplier_id)`
for full-detail supplier records.

For transactional data (orders, stock movements), use the corresponding tools.
""",
)

# Pre-decode JSON-stringified tool args before pydantic validation. Some
# harnesses (and some smaller LLMs) JSON-stringify nested args before
# sending tools/call; FastMCP's strict pydantic validation rejects them.
# This middleware is schema-aware and only decodes strings on fields whose
# schema declares array/object types and never accepts string. Registered
# before ResponseCachingMiddleware so cache keys reflect normalized args.
mcp.add_middleware(JsonStringCoercionMiddleware())
logger.info("middleware_added", middleware="JsonStringCoercionMiddleware")

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


def main(
    transport: Literal["stdio", "http", "sse", "streamable-http"] = "stdio",
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
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
    if _auth is not None:
        provider = type(_auth).__name__
        logger.info("auth_configured", provider=provider)
    elif transport != "stdio":
        logger.warning(
            "no_auth_configured",
            transport=transport,
            msg="MCP endpoint is unauthenticated — set MCP_AUTH_TOKEN or "
            "MCP_GITHUB_CLIENT_ID + MCP_GITHUB_CLIENT_SECRET",
        )
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=transport, host=host, port=port)


if __name__ == "__main__":
    main()
