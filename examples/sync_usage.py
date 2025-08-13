#!/usr/bin/env python3
"""
Synchronous usage example for KatanaClient.

This example demonstrates the synchronous KatanaClient usage with automatic
pagination and resilience features, showcasing the generated OpenAPI models.

Run with:
    poetry run python examples/sync_usage.py

Make sure you have KATANA_API_KEY set in your environment or .env file.
"""

import logging

import httpx

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.client import AuthenticatedClient
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.errors import UnexpectedStatus
from katana_public_api_client.models.product_list_response import (
    ProductListResponse,
)

# Set up logging
logger = logging.getLogger(__name__)


def demo_auto_pagination(client: AuthenticatedClient) -> None:
    """Demonstrate auto-pagination with small page size (synchronous)."""
    logger.info("=== Auto-pagination example (limit=5 per page) ===")

    try:
        response = get_all_products.sync_detailed(
            client=client,
            limit=5,  # Small page size to demonstrate pagination
        )
        if response.status_code == 200:
            # Type-safe access to the generated model
            if isinstance(response.parsed, ProductListResponse):
                products_response = response.parsed
                if products_response.data:
                    logger.info(
                        "Total items collected: %d", len(products_response.data)
                    )
                    # Demonstrate accessing individual product attributes
                    for i, product in enumerate(
                        products_response.data[:3]
                    ):  # Show first 3
                        logger.info(
                            "Product %d: %s (ID: %s)", i + 1, product.name, product.id
                        )
                        if product.uom:
                            logger.info("  - Unit of Measure: %s", product.uom)
                        if product.is_sellable is not UNSET:
                            logger.info("  - Sellable: %s", product.is_sellable)
                        if product.category_name:
                            logger.info("  - Category: %s", product.category_name)
                else:
                    logger.info("No products found")
            else:
                logger.warning("Unexpected response format")
        else:
            logger.error("HTTP error: %d", response.status_code)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.error("Network/HTTP error (expected in tests): %s", e)
    except UnexpectedStatus as e:
        logger.error("Unexpected API response status: %s", e)
    except (KeyError, AttributeError, ValueError) as e:
        logger.error("Data parsing error: %s", e)


def demo_single_page(client: AuthenticatedClient) -> None:
    """Demonstrate single page request without pagination (synchronous)."""
    logger.info("=== Single page example (no pagination) ===")

    try:
        response = get_all_products.sync_detailed(client=client, limit=10, page=1)
        if response.status_code == 200:
            if isinstance(response.parsed, ProductListResponse):
                products_response = response.parsed
                if products_response.data:
                    logger.info("Single page items: %d", len(products_response.data))
                    # Show how to work with typed product data
                    sellable_count = sum(
                        1 for p in products_response.data if p.is_sellable is True
                    )
                    producible_count = sum(
                        1 for p in products_response.data if p.is_producible is True
                    )
                    logger.info("Sellable products: %d", sellable_count)
                    logger.info("Producible products: %d", producible_count)
                else:
                    logger.info("No products found")
            else:
                logger.warning("Unexpected response format")
        else:
            logger.error("HTTP error: %d", response.status_code)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.error("Network/HTTP error (expected in tests): %s", e)
    except UnexpectedStatus as e:
        logger.error("Unexpected API response status: %s", e)
    except (KeyError, AttributeError, ValueError) as e:
        logger.error("Data parsing error: %s", e)


def demo_filtered_query(client: AuthenticatedClient) -> None:
    """Demonstrate filtered query with product attributes (synchronous)."""
    logger.info("=== Filtered query example (sellable products only) ===")

    try:
        response = get_all_products.sync_detailed(
            client=client, is_sellable=True, limit=10
        )
        if response.status_code == 200:
            if isinstance(response.parsed, ProductListResponse):
                products_response = response.parsed
                if products_response.data:
                    logger.info(
                        "Sellable products found: %d", len(products_response.data)
                    )
                    # Demonstrate working with product variants and suppliers
                    for product in products_response.data[:2]:  # Show first 2
                        logger.info("- %s", product.name)
                        if product.variants:
                            logger.info("  Has %d variants", len(product.variants))
                        if product.supplier and hasattr(product.supplier, "name"):
                            logger.info("  Supplier: %s", product.supplier.name)
                        if product.created_at:
                            logger.info(
                                "  Created: %s", product.created_at.strftime("%Y-%m-%d")
                            )
                else:
                    logger.info("No sellable products found")
            else:
                logger.warning("Unexpected response format")
        else:
            logger.error("HTTP error: %d", response.status_code)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.error("Network/HTTP error (expected in tests): %s", e)
    except UnexpectedStatus as e:
        logger.error("Unexpected API response status: %s", e)
    except (KeyError, AttributeError, ValueError) as e:
        logger.error("Data parsing error: %s", e)


def demo_simple_sync_call(client: AuthenticatedClient) -> None:
    """Demonstrate the simplest synchronous call using sync() method."""
    logger.info("=== Simple sync call example ===")

    try:
        # Using the simple sync() method that returns the parsed response directly
        products_response = get_all_products.sync(client=client, limit=5)
        if products_response and isinstance(products_response, ProductListResponse):
            if products_response.data:
                logger.info("Simple sync call - items: %d", len(products_response.data))
                for product in products_response.data[:2]:  # Show first 2
                    logger.info(
                        "- %s (sellable: %s)", product.name, product.is_sellable
                    )
            else:
                logger.info("No products found")
        else:
            logger.info("No response received or unexpected response type")
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.error("Network/HTTP error (expected in tests): %s", e)
    except UnexpectedStatus as e:
        logger.error("Unexpected API response status: %s", e)
    except (KeyError, AttributeError, ValueError) as e:
        logger.error("Data parsing error: %s", e)


def demo_katana_client_sync():
    """Demonstrate the synchronous KatanaClient usage with generated models."""

    logger.info("=== KatanaClient Synchronous Demo ===")
    logger.info(
        "All API calls automatically have auto-pagination - no manual setup needed!"
    )

    with KatanaClient() as client:
        # Run each demo scenario
        demo_auto_pagination(client)
        demo_single_page(client)
        demo_filtered_query(client)
        demo_simple_sync_call(client)

        logger.info("=== Demo Complete ===")
        logger.info("Key benefits demonstrated:")
        logger.info("- Automatic retry logic for network failures")
        logger.info("- Auto-pagination (transport layer handles it transparently)")
        logger.info("- Type-safe access to structured product data")
        logger.info("- Rich product model with attributes, variants, and relationships")
        logger.info("- Synchronous execution - no async/await needed")


if __name__ == "__main__":
    # Set up logging to see the transport in action
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    demo_katana_client_sync()
