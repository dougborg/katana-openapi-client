"""
KatanaClient - The pythonic Katana API client with automatic resilience for OpenAPI Generator.

This client wraps the OpenAPI Generated client with automatic retries,
rate limiting, error handling, and pagination for all API calls.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from .generated.api.customer_api import CustomerApi
from .generated.api.inventory_api import InventoryApi
from .generated.api.manufacturing_order_api import ManufacturingOrderApi
from .generated.api.product_api import ProductApi
from .generated.api.sales_order_api import SalesOrderApi
from .generated.api_client import ApiClient
from .generated.configuration import Configuration


class ResilientAsyncTransport(httpx.AsyncHTTPTransport):
    """
    Custom async transport that adds retry logic, rate limiting, and automatic
    pagination directly at the HTTP transport layer.

    This makes ALL requests through the client automatically resilient and
    automatically handles pagination without any wrapper methods or decorators.

    Features:
    - Automatic retries with exponential backoff using tenacity
    - Rate limiting detection and handling
    - Auto-pagination for GET requests with limit/page parameters
    - Request/response logging and metrics
    """

    def __init__(
        self,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: logging.Logger | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the resilient HTTP transport with automatic retry and pagination.

        Args:
            max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
            max_pages: Maximum number of pages to auto-paginate. Defaults to 100.
            logger: Logger instance for capturing transport operations. If None, creates a default logger.
            **kwargs: Additional arguments passed to the underlying httpx AsyncHTTPTransport.
        """
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.logger = logger or logging.getLogger(__name__)

    def _should_retry(self, response: httpx.Response) -> bool:
        """Check if a response should be retried."""
        return response.status_code in [429, 500, 502, 503, 504]

    def _log_client_error(
        self, response: httpx.Response, request: httpx.Request
    ) -> None:
        """Log client error responses with detailed information."""
        try:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("message", "Unknown error")

            if response.status_code == 422:
                self.logger.warning(
                    f"Validation error {response.status_code} for {request.method} {request.url}: {error_msg}"
                )
            else:
                self.logger.warning(
                    f"Client error {response.status_code} for {request.method} {request.url}: {error_msg}"
                )
        except Exception:
            # Fallback if JSON parsing fails
            self.logger.warning(
                f"Client error {response.status_code} for {request.method} {request.url}"
            )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=(
            retry_if_exception_type((httpx.TransportError, httpx.TimeoutException))
            | retry_if_result(
                lambda r: hasattr(r, "status_code")
                and r.status_code in [429, 500, 502, 503, 504]
            )
        ),
        reraise=True,
    )
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Handle async HTTP requests with automatic retry logic and auto-pagination.

        This method wraps the parent handle_async_request with tenacity retry logic
        and implements auto-pagination for GET requests.
        """
        try:
            # Handle auto-pagination for GET requests with pagination parameters
            if (
                request.method == "GET"
                and request.url.params
                and any(param in str(request.url.params) for param in ["limit", "page"])
            ):
                return await self._handle_paginated_request(request)

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
                self._log_client_error(response, request)

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

    async def _handle_paginated_request(self, request: httpx.Request) -> httpx.Response:
        """Handle paginated requests by combining multiple pages into a single response."""
        parsed_url = urlparse(str(request.url))
        params = parse_qs(parsed_url.query) if parsed_url.query else {}

        # Extract pagination parameters
        limit = int(params.get("limit", [50])[0])
        current_page = int(params.get("page", [1])[0])

        all_data = []
        page = current_page
        total_pages_fetched = 0

        while total_pages_fetched < self.max_pages:
            # Create request for current page
            page_params = params.copy()
            page_params["page"] = [str(page)]
            page_params["limit"] = [str(limit)]

            query_string = urlencode(page_params, doseq=True)
            page_url = request.url.copy_with(params=query_string)
            page_request = request.copy_with(url=page_url)  # type: ignore[attr-defined]

            # Make the request for this page
            response = await super().handle_async_request(page_request)

            if response.status_code != 200:
                # If any page fails, return the failed response
                return response

            try:
                page_data = response.json()

                # Check if this is a list response with pagination
                if isinstance(page_data, dict) and "data" in page_data:
                    page_items = page_data.get("data", [])
                    all_data.extend(page_items)

                    # Check if we've reached the end
                    if len(page_items) < limit:
                        break
                else:
                    # Single page response, return as-is
                    return response

            except json.JSONDecodeError:
                # If we can't parse JSON, return the response as-is
                return response

            page += 1
            total_pages_fetched += 1

        # Create combined response
        if all_data:
            combined_data = {
                "data": all_data,
                "total": len(all_data),
                "page": current_page,
                "limit": limit,
                "auto_paginated": True,
                "pages_fetched": total_pages_fetched,
            }

            # Create a new response with combined data
            combined_content = json.dumps(combined_data).encode("utf-8")
            return httpx.Response(
                status_code=200,
                headers=response.headers,
                content=combined_content,
                request=request,
            )

        # If no data was collected, return the last response
        return response


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
        api_key: str | None = None,
        base_url: str | None = None,
        enable_logging: bool = True,
        log_level: int = logging.INFO,
        # Additional backward compatibility parameters
        max_retries: int = 5,
        max_pages: int = 100,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        logger: logging.Logger | None = None,
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
            max_pages: Maximum pages to auto-paginate (backward compatibility)
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
        self.max_pages = max_pages
        self.headers = headers or {}
        self.timeout = timeout
        self.token = self.api_key  # Backward compatibility alias

        # Create the resilient transport
        self._transport = ResilientAsyncTransport(
            max_retries=max_retries, max_pages=self.max_pages, logger=self.logger
        )

        # Store configuration for later initialization
        self._config = Configuration(
            host=self.base_url, api_key={"ApiKeyAuth": self.api_key}
        )

        # Delay API client creation until async context is entered
        self._api_client: ApiClient | None = None

        # API instances will be created on demand
        self._product_api = None
        self._customer_api = None
        self._sales_order_api = None
        self._manufacturing_order_api = None
        self._inventory_api = None

    async def _initialize_api_client(self):
        """Initialize the API client when async context is available."""
        if self._api_client is None:
            self._api_client = ApiClient(configuration=self._config)
            # Override the API client's REST client to use our resilient HTTP client
            if hasattr(self._api_client, "rest_client"):
                self._api_client.rest_client.pool_manager = self._http_client

    async def __aenter__(self):
        """Async context manager entry."""
        # Create HTTP client with resilient transport when entering async context
        self._http_client = httpx.AsyncClient(
            transport=self._transport,
            timeout=self.timeout or 30.0,
            headers=self.headers,
        )

        # Initialize the API client now that we have an event loop
        await self._initialize_api_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close the HTTP client and transport
        if hasattr(self, "_http_client"):
            await self._http_client.aclose()

        # Close the underlying API client if it has sessions
        if (
            self._api_client is not None
            and hasattr(self._api_client, "rest_client")
            and hasattr(self._api_client.rest_client, "pool_manager")
        ):
            pool_manager = self._api_client.rest_client.pool_manager
            if hasattr(pool_manager, "aclose"):
                await pool_manager.aclose()

    @property
    def product(self) -> ProductApi:
        """Access to Product API endpoints."""
        if self._product_api is None:
            if self._api_client is None:
                raise RuntimeError(
                    "KatanaClient must be used as an async context manager"
                )
            self._product_api = ProductApi(api_client=self._api_client)
        return self._product_api

    @property
    def customer(self) -> CustomerApi:
        """Access to Customer API endpoints."""
        if self._customer_api is None:
            if self._api_client is None:
                raise RuntimeError(
                    "KatanaClient must be used as an async context manager"
                )
            self._customer_api = CustomerApi(api_client=self._api_client)
        return self._customer_api

    @property
    def sales_order(self) -> SalesOrderApi:
        """Access to Sales Order API endpoints."""
        if self._sales_order_api is None:
            if self._api_client is None:
                raise RuntimeError(
                    "KatanaClient must be used as an async context manager"
                )
            self._sales_order_api = SalesOrderApi(api_client=self._api_client)
        return self._sales_order_api

    @property
    def manufacturing_order(self) -> ManufacturingOrderApi:
        """Access to Manufacturing Order API endpoints."""
        if self._manufacturing_order_api is None:
            if self._api_client is None:
                raise RuntimeError(
                    "KatanaClient must be used as an async context manager"
                )
            self._manufacturing_order_api = ManufacturingOrderApi(
                api_client=self._api_client
            )
        return self._manufacturing_order_api

    @property
    def inventory(self) -> InventoryApi:
        """Access to Inventory API endpoints."""
        if self._inventory_api is None:
            if self._api_client is None:
                raise RuntimeError(
                    "KatanaClient must be used as an async context manager"
                )
            self._inventory_api = InventoryApi(api_client=self._api_client)
        return self._inventory_api

    # For backward compatibility, provide access to the underlying client
    @property
    def client(self) -> ApiClient:
        """Access to the underlying ApiClient for advanced usage."""
        if self._api_client is None:
            raise RuntimeError("KatanaClient must be used as an async context manager")
        return self._api_client

    # Backward compatibility methods for tests
    def get_async_httpx_client(self) -> httpx.AsyncClient:
        """Get the underlying httpx.AsyncClient for backward compatibility."""
        if not hasattr(self, "_http_client") or self._http_client is None:
            raise RuntimeError("KatanaClient must be used as an async context manager")
        return self._http_client

    def with_headers(self, headers: dict[str, str]) -> KatanaClient:
        """Get a new client with additional headers (backward compatibility)."""
        new_headers = {**self.headers, **headers}
        return KatanaClient(
            api_key=self.api_key,
            base_url=self.base_url,
            headers=new_headers,
            timeout=self.timeout,
            max_retries=self.max_retries,
            max_pages=self.max_pages,
            logger=self.logger,
        )
