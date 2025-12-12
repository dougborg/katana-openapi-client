"""Test utilities for integration test data isolation and cleanup.

This module provides utilities to ensure integration tests:
1. Create data with a recognizable namespace prefix
2. Track all created resources for cleanup
3. Clean up all test data after tests complete (even on failure)

NAMESPACE STRATEGY:
All test-created data uses the prefix "MCPTEST-" followed by a session ID.
This allows:
- Easy identification of test data in the Katana UI
- Bulk cleanup of orphaned test data
- Isolation between concurrent test runs

Example test data names:
- SKU: "MCPTEST-abc123-WIDGET-001"
- Order number: "MCPTEST-abc123-PO-001"
- Product name: "MCPTEST-abc123 Test Product"
"""

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.manufacturing_order import delete_manufacturing_order
from katana_public_api_client.api.material import delete_material
from katana_public_api_client.api.product import delete_product
from katana_public_api_client.api.purchase_order import delete_purchase_order
from katana_public_api_client.api.sales_order import delete_sales_order
from katana_public_api_client.api.services import delete_service
from katana_public_api_client.utils import unwrap_data

logger = logging.getLogger(__name__)

# Namespace prefix for all test-created data
TEST_NAMESPACE_PREFIX = "MCPTEST"


class ResourceType(Enum):
    """Types of Katana resources that can be created by tests."""

    PRODUCT = "product"
    MATERIAL = "material"
    SERVICE = "service"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    MANUFACTURING_ORDER = "manufacturing_order"


@dataclass
class TrackedResource:
    """A resource created during testing that needs cleanup."""

    resource_type: ResourceType
    resource_id: int
    identifier: str  # SKU, order number, etc. for logging


@dataclass
class TrackedTestSession:
    """Tracks resources created during a test session for cleanup.

    Usage:
        async with tracked_session(client) as session:
            # Create resources - they're automatically tracked
            sku = session.namespaced_sku("WIDGET-001")
            product_id = await create_product(sku=sku, ...)
            session.track(ResourceType.PRODUCT, product_id, sku)

            # Resources are cleaned up when context exits
    """

    client: "KatanaClient"
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    resources: list[TrackedResource] = field(default_factory=list)
    cleanup_errors: list[str] = field(default_factory=list)

    @property
    def namespace(self) -> str:
        """Get the full namespace prefix for this session."""
        return f"{TEST_NAMESPACE_PREFIX}-{self.session_id}"

    def namespaced_sku(self, base_sku: str) -> str:
        """Generate a namespaced SKU for test data.

        Args:
            base_sku: The base SKU (e.g., "WIDGET-001")

        Returns:
            Namespaced SKU (e.g., "MCPTEST-abc123-WIDGET-001")
        """
        return f"{self.namespace}-{base_sku}"

    def namespaced_order_number(self, base_number: str) -> str:
        """Generate a namespaced order number for test data.

        Args:
            base_number: The base order number (e.g., "PO-001")

        Returns:
            Namespaced order number (e.g., "MCPTEST-abc123-PO-001")
        """
        return f"{self.namespace}-{base_number}"

    def namespaced_name(self, base_name: str) -> str:
        """Generate a namespaced name for test data.

        Args:
            base_name: The base name (e.g., "Test Product")

        Returns:
            Namespaced name (e.g., "MCPTEST-abc123 Test Product")
        """
        return f"{self.namespace} {base_name}"

    def track(
        self, resource_type: ResourceType, resource_id: int, identifier: str
    ) -> None:
        """Track a resource for cleanup.

        Args:
            resource_type: Type of resource (product, order, etc.)
            resource_id: The Katana API ID of the resource
            identifier: Human-readable identifier (SKU, order number) for logging
        """
        self.resources.append(
            TrackedResource(
                resource_type=resource_type,
                resource_id=resource_id,
                identifier=identifier,
            )
        )
        logger.debug(
            "Tracked resource for cleanup: %s %s (ID: %d)",
            resource_type.value,
            identifier,
            resource_id,
        )

    async def cleanup(self) -> None:
        """Clean up all tracked resources.

        Resources are cleaned up in reverse order (LIFO) to handle dependencies.
        For example, orders referencing products are deleted before the products.

        Errors during cleanup are logged but don't raise exceptions to ensure
        all resources are attempted for cleanup.
        """
        if not self.resources:
            logger.debug("No resources to clean up")
            return

        logger.info(
            "Cleaning up %d test resources for session %s",
            len(self.resources),
            self.session_id,
        )

        # Clean up in reverse order (LIFO) to handle dependencies
        for resource in reversed(self.resources):
            try:
                await self._delete_resource(resource)
                logger.debug(
                    "Cleaned up %s %s (ID: %d)",
                    resource.resource_type.value,
                    resource.identifier,
                    resource.resource_id,
                )
            except Exception as e:
                error_msg = (
                    f"Failed to clean up {resource.resource_type.value} "
                    f"{resource.identifier} (ID: {resource.resource_id}): {e}"
                )
                logger.warning(error_msg)
                self.cleanup_errors.append(error_msg)

        if self.cleanup_errors:
            logger.warning(
                "Cleanup completed with %d errors. Manual cleanup may be needed "
                "for resources with namespace prefix: %s",
                len(self.cleanup_errors),
                self.namespace,
            )

    async def _delete_resource(self, resource: TrackedResource) -> None:
        """Delete a single resource from Katana."""
        delete_funcs = {
            ResourceType.PRODUCT: delete_product.asyncio_detailed,
            ResourceType.MATERIAL: delete_material.asyncio_detailed,
            ResourceType.SERVICE: delete_service.asyncio_detailed,
            ResourceType.PURCHASE_ORDER: delete_purchase_order.asyncio_detailed,
            ResourceType.SALES_ORDER: delete_sales_order.asyncio_detailed,
            ResourceType.MANUFACTURING_ORDER: delete_manufacturing_order.asyncio_detailed,
        }

        delete_func = delete_funcs.get(resource.resource_type)
        if delete_func is None:
            logger.warning(
                "No delete function for resource type: %s", resource.resource_type
            )
            return

        response = await delete_func(client=self.client, id=resource.resource_id)

        # 200, 204, and 404 are all acceptable (resource deleted or already gone)
        if response.status_code not in (200, 204, 404):
            raise RuntimeError(
                f"Delete returned unexpected status {response.status_code}"
            )


@asynccontextmanager
async def tracked_session(
    client: KatanaClient,
) -> AsyncGenerator[TrackedTestSession, None]:
    """Context manager for test sessions with automatic cleanup.

    Usage:
        async with tracked_session(client) as session:
            sku = session.namespaced_sku("WIDGET-001")
            product_id = await create_test_product(client, sku)
            session.track(ResourceType.PRODUCT, product_id, sku)

            # Test your code here...

        # Resources are automatically cleaned up when exiting

    Args:
        client: KatanaClient instance for API calls

    Yields:
        TrackedTestSession: Session object for tracking resources
    """
    session = TrackedTestSession(client=client)
    logger.info("Starting test session: %s", session.session_id)

    try:
        yield session
    finally:
        await session.cleanup()
        logger.info("Completed test session: %s", session.session_id)


def is_test_data(identifier: str) -> bool:
    """Check if an identifier belongs to test data.

    Args:
        identifier: SKU, order number, or name to check

    Returns:
        True if the identifier starts with the test namespace prefix
    """
    return identifier.startswith(TEST_NAMESPACE_PREFIX)


async def cleanup_orphaned_test_data(client: KatanaClient) -> dict[str, int]:
    """Clean up any orphaned test data from previous test runs.

    This function searches for and deletes any resources with the test
    namespace prefix. Use this to clean up after failed test runs that
    didn't complete cleanup.

    Args:
        client: KatanaClient instance for API calls

    Returns:
        Dict mapping resource type to count of deleted resources

    Warning:
        This will delete ALL data matching the test namespace prefix.
        Only use in test environments, never in production.
    """
    # Import here to avoid circular imports
    from katana_public_api_client.api.manufacturing_order import (
        get_all_manufacturing_orders,
    )
    from katana_public_api_client.api.material import get_all_materials
    from katana_public_api_client.api.product import get_all_products
    from katana_public_api_client.api.purchase_order import get_all_purchase_orders
    from katana_public_api_client.api.sales_order import get_all_sales_orders

    deleted_counts: dict[str, int] = {}

    # Define search and delete operations for each resource type
    cleanup_configs = [
        (
            "products",
            get_all_products.asyncio_detailed,
            delete_product.asyncio_detailed,
            lambda r: r.name if hasattr(r, "name") else None,
        ),
        (
            "materials",
            get_all_materials.asyncio_detailed,
            delete_material.asyncio_detailed,
            lambda r: r.name if hasattr(r, "name") else None,
        ),
        (
            "purchase_orders",
            get_all_purchase_orders.asyncio_detailed,
            delete_purchase_order.asyncio_detailed,
            lambda r: r.order_no if hasattr(r, "order_no") else None,
        ),
        (
            "sales_orders",
            get_all_sales_orders.asyncio_detailed,
            delete_sales_order.asyncio_detailed,
            lambda r: r.order_no if hasattr(r, "order_no") else None,
        ),
        (
            "manufacturing_orders",
            get_all_manufacturing_orders.asyncio_detailed,
            delete_manufacturing_order.asyncio_detailed,
            lambda r: r.additional_info if hasattr(r, "additional_info") else None,
        ),
    ]

    for resource_name, list_func, delete_func, get_identifier in cleanup_configs:
        try:
            response = await list_func(client=client)
            # Use unwrap_data helper to safely extract data list
            items = unwrap_data(response, raise_on_error=False, default=[])
            deleted = 0

            for item in items:
                identifier = get_identifier(item)
                if identifier and is_test_data(identifier):
                    try:
                        await delete_func(client=client, id=item.id)
                        deleted += 1
                        logger.debug(
                            "Deleted orphaned %s: %s", resource_name, identifier
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to delete orphaned %s %s: %s",
                            resource_name,
                            identifier,
                            e,
                        )

            if deleted > 0:
                deleted_counts[resource_name] = deleted
                logger.info("Cleaned up %d orphaned %s", deleted, resource_name)

        except Exception as e:
            logger.warning(
                "Error scanning %s for orphaned test data: %s", resource_name, e
            )

    return deleted_counts
