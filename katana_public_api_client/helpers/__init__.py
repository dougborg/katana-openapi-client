"""Domain classes for the Katana API client.

These domain classes provide ergonomic, domain-specific methods that reduce boilerplate
and serve as the foundation for MCP tools.

Example:
    >>> async with KatanaClient() as client:
    ...     # Product catalog operations
    ...     products = await client.products.list(is_sellable=True)
    ...     product = await client.products.get(123)
    ...     results = await client.products.search("widget")
    ...
    ...     # Inventory and stock operations
    ...     stock = await client.inventory.check_stock("WIDGET-001")
    ...     low_stock = await client.inventory.list_low_stock(threshold=10)
"""

from katana_public_api_client.helpers.base import Base
from katana_public_api_client.helpers.inventory import Inventory
from katana_public_api_client.helpers.materials import Materials
from katana_public_api_client.helpers.products import Products
from katana_public_api_client.helpers.services import Services
from katana_public_api_client.helpers.variants import Variants

__all__ = [
    "Base",
    "Inventory",
    "Materials",
    "Products",
    "Services",
    "Variants",
]
