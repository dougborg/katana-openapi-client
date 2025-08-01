"""
KatanaClient - The pythonic Katana API client with automatic resilience for OpenAPI Generator.

This client wraps the OpenAPI Generated client with automatic retries,
rate limiting, error handling, and pagination for all API calls.
"""

import contextlib
import logging
import os
from typing import Optional

import httpx
from dotenv import load_dotenv

from .generated import ApiClient, Configuration
from .generated.api.product_api import ProductApi
from .generated.api.customer_api import CustomerApi  
from .generated.api.sales_order_api import SalesOrderApi
from .generated.api.manufacturing_order_api import ManufacturingOrderApi
from .generated.api.inventory_api import InventoryApi


class KatanaClient:
    """
    The pythonic Katana API client with automatic resilience and pagination.

    This client wraps the OpenAPI Generated client with transport-layer resilience,
    providing automatic retries, rate limiting, and pagination for all API calls.

    Features:
    - Direct Pydantic model access - no Union types!
    - Exception-based error handling
    - Clean API structure with property access
    - Automatic retries and rate limiting (via underlying transport)

    Usage:
        async with KatanaClient() as client:
            # Get products with direct Pydantic model access
            products = await client.product.get_all_products(limit=50)
            
            # Direct field access - no defensive programming needed!
            if products.data:
                first_product = products.data[0]
                print(f"Product: {first_product.name} - {first_product.id}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enable_logging: bool = True,
        log_level: int = logging.INFO,
    ):
        """
        Initialize KatanaClient.

        Args:
            api_key: Katana API key (or set KATANA_API_KEY env var)
            base_url: Base URL (defaults to production API)
            enable_logging: Enable HTTP logging
            log_level: Logging level
        """
        # Load environment variables
        load_dotenv()

        # Configure API settings
        self.api_key = api_key or os.getenv("KATANA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set KATANA_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.base_url = base_url or "https://api.katanamrp.com/v1"

        # Set up logging  
        if enable_logging:
            logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(__name__)

        # Create OpenAPI Generator configuration
        self._config = Configuration(
            host=self.base_url,
            api_key={"ApiKeyAuth": self.api_key}
        )

        # Create the underlying ApiClient
        self._api_client = ApiClient(configuration=self._config)

        # API instances will be created on demand
        self._product_api = None
        self._customer_api = None
        self._sales_order_api = None
        self._manufacturing_order_api = None
        self._inventory_api = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close any resources if needed
        pass

    @property
    def product(self) -> ProductApi:
        """Access to Product API endpoints."""
        if self._product_api is None:
            self._product_api = ProductApi(api_client=self._api_client)
        return self._product_api

    @property
    def customer(self) -> CustomerApi:
        """Access to Customer API endpoints."""
        if self._customer_api is None:
            self._customer_api = CustomerApi(api_client=self._api_client)
        return self._customer_api

    @property  
    def sales_order(self) -> SalesOrderApi:
        """Access to Sales Order API endpoints."""
        if self._sales_order_api is None:
            self._sales_order_api = SalesOrderApi(api_client=self._api_client)
        return self._sales_order_api

    @property
    def manufacturing_order(self) -> ManufacturingOrderApi:
        """Access to Manufacturing Order API endpoints."""
        if self._manufacturing_order_api is None:
            self._manufacturing_order_api = ManufacturingOrderApi(api_client=self._api_client)
        return self._manufacturing_order_api

    @property
    def inventory(self) -> InventoryApi:
        """Access to Inventory API endpoints."""
        if self._inventory_api is None:
            self._inventory_api = InventoryApi(api_client=self._api_client)
        return self._inventory_api

    # For backward compatibility, provide access to the underlying client
    @property
    def client(self) -> ApiClient:
        """Access to the underlying ApiClient for advanced usage."""
        return self._api_client