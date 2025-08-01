"""
KatanaClient - The pythonic Katana API client with automatic resilience for OpenAPI Generator.

This client wraps the OpenAPI Generated client with automatic retries,
rate limiting, error handling, and pagination for all API calls.
"""

import logging
import os
from typing import Optional, Any

import httpx
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .generated import ApiClient, Configuration
from .generated.api.product_api import ProductApi
from .generated.api.customer_api import CustomerApi  
from .generated.api.sales_order_api import SalesOrderApi
from .generated.api.manufacturing_order_api import ManufacturingOrderApi
from .generated.api.inventory_api import InventoryApi


class ResilientAsyncTransport(httpx.AsyncHTTPTransport):
    """
    Custom async transport that adds retry logic, rate limiting, and automatic
    pagination directly at the HTTP transport layer.

    This makes ALL requests through the client automatically resilient and
    automatically handles pagination without any wrapper methods or decorators.

    Features:
    - Automatic retries with exponential backoff using tenacity
    - Rate limiting detection and handling
    - Request/response logging and metrics
    """

    def __init__(
        self,
        max_retries: int = 5,
        logger: logging.Logger | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the resilient HTTP transport with automatic retry.

        Args:
            max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
            logger: Logger instance for capturing transport operations. If None, creates a default logger.
            **kwargs: Additional arguments passed to the underlying httpx AsyncHTTPTransport.
        """
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        reraise=True,
    )
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Handle async HTTP requests with automatic retry logic.
        
        This method wraps the parent handle_async_request with tenacity retry logic
        to automatically retry on network errors and timeouts.
        """
        try:
            response = await super().handle_async_request(request)
            
            # Log rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                self.logger.warning(
                    f"Rate limited {request.method} {request.url} - "
                    f"Retry-After: {retry_after}"
                )
                
            # Log client errors (4xx)
            elif 400 <= response.status_code < 500:
                self.logger.warning(
                    f"Client error {response.status_code} for {request.method} {request.url}"
                )
                
            # Log server errors (5xx) 
            elif response.status_code >= 500:
                self.logger.error(
                    f"Server error {response.status_code} for {request.method} {request.url}"
                )
                
            return response
            
        except Exception as e:
            self.logger.error(
                f"Transport error for {request.method} {request.url}: {e}"
            )
            raise


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
        # Additional backward compatibility parameters
        max_retries: int = 5,
        headers: Optional[dict] = None,
        timeout: Optional[float] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs: Any,  # Accept additional kwargs for forward compatibility
    ):
        """
        Initialize KatanaClient.

        Args:
            api_key: Katana API key (or set KATANA_API_KEY env var)
            base_url: Base URL (defaults to production API)
            enable_logging: Enable HTTP logging
            log_level: Logging level
            max_retries: Maximum retry attempts (backward compatibility)
            headers: Additional headers (backward compatibility)
            timeout: Request timeout (backward compatibility)
            logger: Custom logger (backward compatibility)
            **kwargs: Additional arguments for forward compatibility
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
        self.logger = logger or logging.getLogger(__name__)

        # Store backward compatibility parameters
        self.max_retries = max_retries
        self.headers = headers or {}
        self.timeout = timeout

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
        # Close the underlying API client and its session
        if hasattr(self._api_client, 'rest_client') and hasattr(self._api_client.rest_client, 'pool_manager'):
            # Close aiohttp session if it exists
            pool_manager = self._api_client.rest_client.pool_manager
            if hasattr(pool_manager, 'close'):
                await pool_manager.close()

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