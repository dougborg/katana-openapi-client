"""
KatanaClient - The pythonic Katana API client with automatic resilience.

This client uses httpx's native transport layer to provide automatic retries,
rate limiting, error handling, and pagination for all API calls without any
decorators or wrapper methods needed.
"""

import contextlib
import json
import logging
import os
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Any, cast

import httpx
from dotenv import load_dotenv
from httpx import AsyncHTTPTransport
from httpx_retries import Retry, RetryTransport

from .client import AuthenticatedClient
from .client_types import Unset
from .models.detailed_error_response import DetailedErrorResponse
from .models.error_response import ErrorResponse


class RateLimitAwareRetry(Retry):
    """
    Custom Retry class that allows non-idempotent methods (POST, PATCH) to be
    retried ONLY when receiving a 429 (Too Many Requests) status code.

    For all other retryable status codes (502, 503, 504), only idempotent methods
    (HEAD, GET, PUT, DELETE, OPTIONS, TRACE) will be retried.

    This ensures we don't accidentally retry non-idempotent operations after
    server errors, but we DO retry them when we're being rate-limited.
    """

    # Idempotent methods that are always safe to retry
    IDEMPOTENT_METHODS = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize and track the current request method."""
        super().__init__(*args, **kwargs)
        self._current_method: str | None = None

    def is_retryable_method(self, method: str) -> bool:
        """
        Allow all methods to pass through the initial check.

        Store the method for later use in is_retryable_status_code.
        """
        self._current_method = method.upper()
        # Accept all methods - we'll filter in is_retryable_status_code
        return self._current_method in self.allowed_methods

    def is_retryable_status_code(self, status_code: int) -> bool:
        """
        Check if a status code is retryable for the current method.

        For 429 (rate limiting), allow all methods.
        For other errors (502, 503, 504), only allow idempotent methods.
        """
        # First check if the status code is in the allowed list at all
        if status_code not in self.status_forcelist:
            return False

        # If we don't know the method, fall back to default behavior
        if self._current_method is None:
            return True

        # Rate limiting (429) - retry all methods
        if status_code == HTTPStatus.TOO_MANY_REQUESTS:
            return True

        # Other retryable errors - only retry idempotent methods
        return self._current_method in self.IDEMPOTENT_METHODS

    def increment(self) -> "RateLimitAwareRetry":
        """Return a new retry instance with the attempt count incremented."""
        # Call parent's increment which creates a new instance of our class
        new_retry = cast(RateLimitAwareRetry, super().increment())
        # Preserve the current method across retry attempts
        new_retry._current_method = self._current_method
        return new_retry


class ErrorLoggingTransport(AsyncHTTPTransport):
    """
    Transport layer that adds detailed error logging for 4xx client errors.

    This transport wraps another AsyncHTTPTransport and intercepts responses
    to log detailed error information using the generated error models.
    """

    def __init__(
        self,
        wrapped_transport: AsyncHTTPTransport | None = None,
        logger: logging.Logger | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the error logging transport.

        Args:
            wrapped_transport: The transport to wrap. If None, creates a new AsyncHTTPTransport.
            logger: Logger instance for capturing error details. If None, creates a default logger.
            **kwargs: Additional arguments passed to AsyncHTTPTransport if wrapped_transport is None.
        """
        super().__init__()
        if wrapped_transport is None:
            wrapped_transport = AsyncHTTPTransport(**kwargs)
        self._wrapped_transport = wrapped_transport
        self.logger = logger or logging.getLogger(__name__)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request and log detailed error information for 4xx responses."""
        response = await self._wrapped_transport.handle_async_request(request)

        # Log detailed information for 400-level client errors
        if 400 <= response.status_code < 500:
            await self._log_client_error(response, request)

        return response

    async def _log_client_error(
        self, response: httpx.Response, request: httpx.Request
    ) -> None:
        """
        Log detailed information for 400-level client errors using generated models.
        Assumes error responses are always typed (DetailedErrorResponse or ErrorResponse).
        """
        method = request.method
        url = str(request.url)
        status_code = response.status_code

        # Read response content if it's streaming
        if hasattr(response, "aread"):
            with contextlib.suppress(TypeError, AttributeError):
                await response.aread()

        try:
            error_data = response.json()
        except (json.JSONDecodeError, TypeError, ValueError):
            self.logger.error(
                f"Client error {status_code} for {method} {url} - "
                f"Response: {getattr(response, 'text', '')[:500]}..."
            )
            return

        # Prefer DetailedErrorResponse for 422, else ErrorResponse
        if status_code == 422:
            try:
                detailed_error = DetailedErrorResponse.from_dict(error_data)
                # Debug log the parsed error structure
                self.logger.debug(
                    f"Parsed DetailedErrorResponse - "
                    f"details type: {type(detailed_error.details)}, "
                    f"details value: {detailed_error.details}, "
                    f"is Unset: {isinstance(detailed_error.details, Unset)}, "
                    f"raw error_data: {error_data}"
                )
                self._log_detailed_error(detailed_error, method, url, status_code)
                return
            except (TypeError, ValueError, AttributeError) as e:
                self.logger.debug(
                    f"Failed to parse as DetailedErrorResponse: {type(e).__name__}: {e}"
                )

        try:
            error_response = ErrorResponse.from_dict(error_data)
            self._log_error(error_response, method, url, status_code)
            return
        except (TypeError, ValueError, AttributeError) as e:
            self.logger.debug(
                f"Failed to parse as ErrorResponse: {type(e).__name__}: {e}"
            )

        # Fallback: log raw error data if parsing failed
        self.logger.error(
            f"Client error {status_code} for {method} {url} - Raw error: {error_data}"
        )

    def _log_detailed_error(
        self, error: DetailedErrorResponse, method: str, url: str, status_code: int
    ) -> None:
        """Log detailed errors using the typed DetailedErrorResponse model."""

        # Use the log prefix expected by tests for 422 errors
        if status_code == 422:
            log_message = f"Validation error 422 for {method} {url}"
        else:
            log_message = f"Detailed error {status_code} for {method} {url}"

        # Check for Unset values before logging
        error_name = error.name if not isinstance(error.name, Unset) else None
        error_message = error.message if not isinstance(error.message, Unset) else None
        error_code = error.code if not isinstance(error.code, Unset) else None

        # If main fields are Unset, check additional_properties for nested error data
        if (
            error_name is None
            and error_message is None
            and hasattr(error, "additional_properties")
        ):
            nested = error.additional_properties
            if isinstance(nested, dict) and "error" in nested:
                nested_error = nested["error"]
                if isinstance(nested_error, dict):
                    error_name = nested_error.get("name", "(not provided)")
                    error_message = nested_error.get("message", "(not provided)")
                    if "statusCode" in nested_error and error_code is None:
                        error_code = nested_error.get("statusCode")

        # Use fallback if still not found
        if error_name is None:
            error_name = "(not provided)"
        if error_message is None:
            error_message = "(not provided)"

        log_message += f"\n  Error: {error_name} - {error_message}"

        if error_code is not None:
            log_message += f"\n  Code: {error_code}"

        # Log validation details if present
        if not isinstance(error.details, Unset) and error.details:
            log_message += f"\n  Validation details ({len(error.details)} errors):"
            for i, detail in enumerate(error.details, 1):
                log_message += f"\n    {i}. Path: {detail.path}"
                # Only log detail.code if not Unset
                if hasattr(detail, "code") and detail.code is not None:
                    log_message += f"\n       Code: {detail.code}"
                if getattr(detail, "message", None):
                    log_message += f"\n       Message: {detail.message}"
                if (
                    getattr(detail, "info", None)
                    and detail.info is not None
                    and not isinstance(detail.info, Unset)
                    and hasattr(detail.info, "additional_properties")
                ):
                    info = detail.info.additional_properties
                    if info:
                        formatted = ", ".join(f"{k}: {v!r}" for k, v in info.items())
                        log_message += f"\n       Details: {formatted}"

        # Also check additional_properties for nested error details
        # The API might return details in a nested structure
        if hasattr(error, "additional_properties") and error.additional_properties:
            nested_error = error.additional_properties.get("error")
            if isinstance(nested_error, dict):
                nested_details = nested_error.get("details")
                if nested_details and isinstance(nested_details, list):
                    log_message += (
                        f"\n  Nested validation details ({len(nested_details)} errors):"
                    )
                    for i, detail in enumerate(nested_details, 1):
                        if isinstance(detail, dict):
                            log_message += (
                                f"\n    {i}. Path: {detail.get('path', 'unknown')}"
                            )
                            if "code" in detail:
                                log_message += f"\n       Code: {detail['code']}"
                            if "message" in detail:
                                log_message += f"\n       Message: {detail['message']}"

        self.logger.error(log_message)

    def _log_error(
        self, error: ErrorResponse, method: str, url: str, status_code: int
    ) -> None:
        """Log general errors using the typed ErrorResponse model."""
        log_message = f"Client error {status_code} for {method} {url}"

        # Check for Unset values before logging
        error_name = error.name if not isinstance(error.name, Unset) else None
        error_message = error.message if not isinstance(error.message, Unset) else None

        # If main fields are Unset, check additional_properties for nested error data
        if (
            error_name is None
            and error_message is None
            and hasattr(error, "additional_properties")
        ):
            nested = error.additional_properties
            if isinstance(nested, dict) and "error" in nested:
                nested_error = nested["error"]
                if isinstance(nested_error, dict):
                    error_name = nested_error.get("name", "(not provided)")
                    error_message = nested_error.get("message", "(not provided)")

        # Use fallback values if still None
        if error_name is None:
            error_name = "(not provided)"
        if error_message is None:
            error_message = "(not provided)"

        log_message += f"\n  Error: {error_name} - {error_message}"

        if error.additional_properties:
            formatted = ", ".join(
                f"{k}: {v!r}" for k, v in error.additional_properties.items()
            )
            log_message += f"\n  Additional info: {formatted}"
        self.logger.error(log_message)


class PaginationTransport(AsyncHTTPTransport):
    """
    Transport layer that adds automatic pagination for GET requests.

    This transport wraps another transport and automatically collects all pages
    for requests that use 'page' or 'limit' parameters.
    """

    def __init__(
        self,
        wrapped_transport: AsyncHTTPTransport | None = None,
        max_pages: int = 100,
        logger: logging.Logger | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the pagination transport.

        Args:
            wrapped_transport: The transport to wrap. If None, creates a new AsyncHTTPTransport.
            max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
            logger: Logger instance for capturing pagination operations. If None, creates a default logger.
            **kwargs: Additional arguments passed to AsyncHTTPTransport if wrapped_transport is None.
        """
        # If no wrapped transport provided, create a base one
        if wrapped_transport is None:
            wrapped_transport = AsyncHTTPTransport(**kwargs)
            super().__init__()
        else:
            super().__init__()

        self._wrapped_transport = wrapped_transport
        self.max_pages = max_pages
        self.logger = logger or logging.getLogger(__name__)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request with automatic pagination for GET requests with page/limit params."""
        # Check if this is a paginated request
        should_paginate = (
            request.method == "GET"
            and hasattr(request, "url")
            and request.url
            and request.url.params
            and ("page" in request.url.params or "limit" in request.url.params)
        )

        if should_paginate:
            return await self._handle_paginated_request(request)
        else:
            # For non-paginated requests, just pass through to wrapped transport
            return await self._wrapped_transport.handle_async_request(request)

    async def _handle_paginated_request(self, request: httpx.Request) -> httpx.Response:
        """
        Handle paginated requests by automatically collecting all pages.

        This method detects paginated responses and automatically collects all available
        pages up to the configured maximum. It preserves the original request structure
        while combining data from multiple pages.

        Args:
            request: The HTTP request to handle (must be a GET request with pagination parameters).

        Returns:
            A combined HTTP response containing data from all collected pages with
            pagination metadata in the response body.

        Note:
            - Only GET requests with 'limit' parameter trigger auto-pagination
            - Requests with explicit 'page' parameter are treated as single-page requests
            - The response contains an 'auto_paginated' flag in the pagination metadata
            - Data from all pages is combined into a single 'data' array
        """
        all_data: list[Any] = []
        current_page = 1
        total_pages: int | None = None
        page_num = 1
        response: httpx.Response | None = None

        # Parse initial parameters
        url_params = dict(request.url.params)

        self.logger.info("Auto-paginating request: %s", request.url)

        for page_num in range(1, self.max_pages + 1):
            # Update the page parameter
            url_params["page"] = str(page_num)

            # Create a new request with updated parameters
            paginated_request = httpx.Request(
                method=request.method,
                url=request.url.copy_with(params=url_params),
                headers=request.headers,
                content=request.content,
                extensions=request.extensions,
            )

            # Make the request using the wrapped transport
            response = await self._wrapped_transport.handle_async_request(
                paginated_request
            )

            if response.status_code != 200:
                # If we get an error, return the original response
                return response

            # Parse the response
            try:
                # Read the response content if it's streaming
                if hasattr(response, "aread"):
                    with contextlib.suppress(TypeError, AttributeError):
                        # Skip aread if it's not async (e.g., in tests with mocks)
                        await response.aread()

                data = response.json()

                # Extract pagination info from headers or response body
                pagination_info = self._extract_pagination_info(response, data)

                if pagination_info:
                    current_page = pagination_info.get("page", page_num)
                    total_pages = pagination_info.get("total_pages")

                    # Extract the actual data items
                    items = data.get("data", data if isinstance(data, list) else [])
                    all_data.extend(items)

                    # Check if we're done
                    # Break if we've reached the last known page or got an empty page
                    if (total_pages and current_page >= total_pages) or len(items) == 0:
                        break

                    self.logger.debug(
                        "Collected page %s/%s, items: %d, total so far: %d",
                        current_page,
                        total_pages or "?",
                        len(items),
                        len(all_data),
                    )
                else:
                    # No pagination info found, treat as single page
                    all_data = data.get("data", data if isinstance(data, list) else [])
                    break

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning("Failed to parse paginated response: %s", e)
                return response

        # Ensure we have a response at this point
        if response is None:
            msg = "No response available after pagination"
            raise RuntimeError(msg)

        # Create a combined response
        combined_data: dict[str, Any] = {"data": all_data}

        # Add pagination metadata
        if total_pages:
            combined_data["pagination"] = {
                "total_pages": total_pages,
                "collected_pages": page_num,
                "total_items": len(all_data),
                "auto_paginated": True,
            }

        # Create a new response with the combined data
        # Remove content-encoding headers to avoid compression issues
        headers = dict(response.headers)
        headers.pop("content-encoding", None)
        headers.pop("content-length", None)  # Will be recalculated

        combined_response = httpx.Response(
            status_code=200,
            headers=headers,
            content=json.dumps(combined_data).encode(),
            request=request,
        )

        self.logger.info(
            "Auto-pagination complete: collected %d items from %d pages",
            len(all_data),
            page_num,
        )

        return combined_response

    def _extract_pagination_info(
        self, response: httpx.Response, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract pagination information from response headers or body."""
        pagination_info: dict[str, Any] = {}

        # Check for X-Pagination header (JSON format)
        if "X-Pagination" in response.headers:
            try:
                pagination_info = json.loads(response.headers["X-Pagination"])
                return pagination_info
            except (json.JSONDecodeError, KeyError):
                pass

        # Check for individual headers
        if "X-Total-Pages" in response.headers:
            pagination_info["total_pages"] = int(response.headers["X-Total-Pages"])
        if "X-Current-Page" in response.headers:
            pagination_info["page"] = int(response.headers["X-Current-Page"])

        # Check for pagination in response body
        if "pagination" in data:
            page_data = data["pagination"]
            if isinstance(page_data, dict):
                pagination_info.update(cast(dict[str, Any], page_data))
        elif (
            "meta" in data
            and isinstance(data["meta"], dict)
            and "pagination" in data["meta"]
        ):
            meta_pagination = cast(Any, data["meta"]["pagination"])
            if isinstance(meta_pagination, dict):
                pagination_info.update(cast(dict[str, Any], meta_pagination))

        return pagination_info if pagination_info else None


def ResilientAsyncTransport(
    max_retries: int = 5,
    max_pages: int = 100,
    logger: logging.Logger | None = None,
    **kwargs: Any,
) -> RetryTransport:
    """
    Factory function that creates a chained transport with error logging,
    pagination, and retry capabilities.

    This function chains multiple transport layers:
    1. AsyncHTTPTransport (base HTTP transport)
    2. ErrorLoggingTransport (logs detailed 4xx errors)
    3. PaginationTransport (auto-collects paginated responses)
    4. RetryTransport (handles retries with Retry-After header support)

    Args:
        max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
        max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
        logger: Logger instance for capturing operations. If None, creates a default logger.
        **kwargs: Additional arguments passed to the base AsyncHTTPTransport.
            Common parameters include:
            - http2 (bool): Enable HTTP/2 support
            - limits (httpx.Limits): Connection pool limits
            - verify (bool | str | ssl.SSLContext): SSL certificate verification
            - cert (str | tuple): Client-side certificates
            - trust_env (bool): Trust environment variables for proxy configuration

    Returns:
        A RetryTransport instance wrapping all the layered transports.

    Note:
        When using a custom transport, parameters like http2, limits, and verify
        must be passed to this factory function (which passes them to the base
        AsyncHTTPTransport), not to the httpx.Client/AsyncClient constructor.

    Example:
        ```python
        transport = ResilientAsyncTransport(max_retries=3, max_pages=50)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get("https://api.example.com/items")
        ```
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Build the transport chain from inside out:
    # 1. Base AsyncHTTPTransport
    base_transport = AsyncHTTPTransport(**kwargs)

    # 2. Wrap with error logging
    error_logging_transport = ErrorLoggingTransport(
        wrapped_transport=base_transport,
        logger=logger,
    )

    # 3. Wrap with pagination
    pagination_transport = PaginationTransport(
        wrapped_transport=error_logging_transport,
        max_pages=max_pages,
        logger=logger,
    )

    # Finally wrap with retry logic (outermost layer)
    # Use RateLimitAwareRetry which:
    # - Retries ALL methods (including POST/PATCH) for 429 rate limiting
    # - Retries ONLY idempotent methods for server errors (502, 503, 504)
    retry = RateLimitAwareRetry(
        total=max_retries,
        backoff_factor=1.0,  # Exponential backoff: 1, 2, 4, 8, 16 seconds
        respect_retry_after_header=True,  # Honor server's Retry-After header
        status_forcelist=[
            429,
            502,
            503,
            504,
        ],  # Status codes that should trigger retries
        allowed_methods=[
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
            "PATCH",
        ],
    )
    retry_transport = RetryTransport(
        transport=pagination_transport,
        retry=retry,
    )

    return retry_transport


class KatanaClient(AuthenticatedClient):
    """
    The pythonic Katana API client with automatic resilience and pagination.

    This client inherits from AuthenticatedClient and can be passed directly to
    generated API methods without needing the .client property.

    Features:
    - Automatic retries on network errors and server errors (5xx)
    - Automatic rate limit handling with Retry-After header support
    - Smart auto-pagination that detects and handles paginated responses automatically
    - Rich logging and observability
    - Minimal configuration - just works out of the box

    Usage:
        # Auto-pagination happens automatically - just call the API
        async with KatanaClient() as client:
            from katana_public_api_client.api.product import get_all_products

            # This automatically collects all pages if pagination is detected
            response = await get_all_products.asyncio_detailed(
                client=client,  # Pass client directly - no .client needed!
                limit=50  # All pages collected automatically
            )

            # Get specific page only (add page=X to disable auto-pagination)
            response = await get_all_products.asyncio_detailed(
                client=client,
                page=1,      # Get specific page
                limit=100    # Set page size
            )

            # Control max pages globally
            client_limited = KatanaClient(max_pages=5)  # Limit to 5 pages max
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: logging.Logger | None = None,
        **httpx_kwargs: Any,
    ):
        """
        Initialize the Katana API client with automatic resilience features.

        Args:
            api_key: Katana API key. If None, will try to load from KATANA_API_KEY env var.
            base_url: Base URL for the Katana API. Defaults to https://api.katanamrp.com/v1
            timeout: Request timeout in seconds. Defaults to 30.0.
            max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
            max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
            logger: Logger instance for capturing client operations. If None, creates a default logger.
            **httpx_kwargs: Additional arguments passed to the base AsyncHTTPTransport.
                Common parameters include:
                - http2 (bool): Enable HTTP/2 support
                - limits (httpx.Limits): Connection pool limits
                - verify (bool | str | ssl.SSLContext): SSL certificate verification
                - cert (str | tuple): Client-side certificates
                - trust_env (bool): Trust environment variables for proxy configuration
                - event_hooks (dict): Custom event hooks (will be merged with built-in hooks)

        Raises:
            ValueError: If no API key is provided and KATANA_API_KEY env var is not set.

        Note:
            Transport-related parameters (http2, limits, verify, etc.) are correctly
            passed to the innermost AsyncHTTPTransport layer, ensuring they take effect
            even with the layered transport architecture.

        Example:
            >>> async with KatanaClient() as client:
            ...     # All API calls through client get automatic resilience
            ...     response = await some_api_method.asyncio_detailed(client=client)
        """
        load_dotenv()

        # Handle backwards compatibility: accept 'token' kwarg as alias for 'api_key'
        if "token" in httpx_kwargs:
            if api_key is not None:
                raise ValueError("Cannot specify both 'api_key' and 'token' parameters")
            api_key = httpx_kwargs.pop("token")

        # Setup credentials
        api_key = api_key or os.getenv("KATANA_API_KEY")
        base_url = (
            base_url or os.getenv("KATANA_BASE_URL") or "https://api.katanamrp.com/v1"
        )

        if not api_key:
            raise ValueError(
                "API key required (KATANA_API_KEY env var or api_key param)"
            )

        self.logger = logger or logging.getLogger(__name__)
        self.max_pages = max_pages

        # Extract client-level parameters that shouldn't go to the transport
        # Event hooks for observability - start with our defaults
        event_hooks: dict[str, list[Callable[[httpx.Response], Awaitable[None]]]] = {
            "response": [
                self._capture_pagination_metadata,
                self._log_response_metrics,
            ]
        }

        # Extract and merge user hooks
        user_hooks = httpx_kwargs.pop("event_hooks", {})
        for event, hooks in user_hooks.items():
            # Normalize to list and add to existing or create new event
            hook_list = cast(
                list[Callable[[httpx.Response], Awaitable[None]]],
                hooks if isinstance(hooks, list) else [hooks],
            )
            if event in event_hooks:
                event_hooks[event].extend(hook_list)
            else:
                event_hooks[event] = hook_list

        # Check if user wants to override the transport entirely
        custom_transport = httpx_kwargs.pop("transport", None) or httpx_kwargs.pop(
            "async_transport", None
        )

        if custom_transport:
            # User provided a custom transport, use it as-is
            transport = custom_transport
        else:
            # Separate transport-specific kwargs from client-specific kwargs
            # Client-specific params that should NOT go to the transport
            client_only_params = ["headers", "cookies", "params", "auth"]
            client_kwargs = {
                k: httpx_kwargs.pop(k)
                for k in list(httpx_kwargs.keys())
                if k in client_only_params
            }

            # Create resilient transport with remaining transport-specific httpx_kwargs
            # These will be passed to the base AsyncHTTPTransport (http2, limits, verify, etc.)
            transport = ResilientAsyncTransport(
                max_retries=max_retries,
                max_pages=max_pages,
                logger=self.logger,
                **httpx_kwargs,  # Pass through http2, limits, verify, cert, trust_env, etc.
            )

            # Put client-specific params back into httpx_kwargs for the parent class
            httpx_kwargs.update(client_kwargs)

        # Initialize the parent AuthenticatedClient
        super().__init__(
            base_url=base_url,
            token=api_key,
            timeout=httpx.Timeout(timeout),
            httpx_args={
                "transport": transport,
                "event_hooks": event_hooks,
                **httpx_kwargs,  # Include any remaining client-level kwargs
            },
        )

    # Remove the client property since we inherit from AuthenticatedClient
    # Users can now pass the KatanaClient instance directly to API methods

    # Event hooks for observability
    async def _capture_pagination_metadata(self, response: httpx.Response) -> None:
        """Capture and store pagination metadata from response headers."""
        if response.status_code == 200:
            x_pagination = response.headers.get("X-Pagination")
            if x_pagination:
                try:
                    pagination_info = json.loads(x_pagination)
                    self.logger.debug(f"Pagination metadata: {pagination_info}")
                    # Store pagination info for easy access
                    setattr(response, "pagination_info", pagination_info)  # noqa: B010
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid X-Pagination header: {x_pagination}")

    async def _log_response_metrics(self, response: httpx.Response) -> None:
        """Log response metrics for observability."""
        # Extract timing info if available (after response is read)
        try:
            if hasattr(response, "elapsed"):
                duration = response.elapsed.total_seconds()
            else:
                duration = 0.0
        except RuntimeError:
            # elapsed not available yet
            duration = 0.0

        self.logger.debug(
            f"Response: {response.status_code} {response.request.method} "
            f"{response.request.url!s} ({duration:.2f}s)"
        )
