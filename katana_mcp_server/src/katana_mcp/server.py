"""Katana MCP Server - FastMCP server with environment-based authentication.

This module implements the core MCP server for Katana Manufacturing ERP,
providing tools, resources, and prompts for interacting with the Katana API.

Features:
- Environment-based authentication (KATANA_API_KEY)
- Automatic client initialization with error handling
- Lifespan management for KatanaClient context
- Production-ready with transport-layer resilience
- Structured logging with observability
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from katana_mcp import __version__
from katana_mcp.logging import get_logger, setup_logging
from katana_public_api_client import KatanaClient

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)


@dataclass
class ServerContext:
    """Context object that holds the KatanaClient instance for the server lifespan.

    This dataclass provides type-safe access to the KatanaClient throughout
    the server lifecycle, following the StockTrim architecture pattern.

    Attributes:
        client: Initialized KatanaClient instance for API operations
    """

    client: KatanaClient


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
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
        ServerContext: Context object containing initialized KatanaClient

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

            # Create context with client for tools to access
            context = ServerContext(client=client)  # type: ignore[arg-type]

            # Yield context to server - tools can access via lifespan dependency
            logger.info("server_ready", version=__version__)
            yield context

    except ValueError as e:
        # Authentication or configuration errors
        logger.error("initialization_failed", error_type="ValueError", error=str(e))
        raise
    except Exception as e:
        # Unexpected errors during initialization
        logger.error(
            "initialization_failed",
            error_type=type(e).__name__,
            error=str(e),
            exc_info=True,
        )
        raise
    finally:
        logger.info("server_shutting_down")


# Initialize FastMCP server with lifespan management
mcp = FastMCP(
    name="katana-erp",
    version=__version__,
    lifespan=lifespan,
    instructions="""
    Katana MCP Server provides tools for interacting with Katana Manufacturing ERP.

    Available capabilities:
    - Inventory management (check stock, search products, low stock alerts)
    - Sales order management (create, track, list orders)
    - Purchase order management (create, track, receive orders)
    - Manufacturing order management (create, track, list active orders)

    All tools require KATANA_API_KEY environment variable to be set.
    """,
)

# Register all tools, resources, and prompts with the mcp instance
# This must come after mcp initialization
from katana_mcp.resources import register_all_resources  # noqa: E402
from katana_mcp.tools import register_all_tools  # noqa: E402

register_all_tools(mcp)
register_all_resources(mcp)


def main(**kwargs: Any) -> None:
    """Main entry point for the Katana MCP Server.

    This function is called when running the server via:
    - uvx katana-mcp-server
    - python -m katana_mcp
    - katana-mcp-server (console script)

    Args:
        **kwargs: Additional arguments passed to mcp.run()
    """
    logger.info("server_starting", version=__version__)
    mcp.run(**kwargs)


if __name__ == "__main__":
    main()
