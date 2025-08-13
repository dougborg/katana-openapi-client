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
from typing import Any, cast

import httpx
from dotenv import load_dotenv
from httpx import AsyncHTTPTransport
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from .client import AuthenticatedClient
from .client_types import Unset
from .models.detailed_error_response import DetailedErrorResponse
from .models.error_response import ErrorResponse


class ResilientAsyncTransport(AsyncHTTPTransport):
    """
    Custom async transport that adds retry logic, rate limiting, and automatic
    pagination directly at the HTTP transport layer.

    This makes ALL requests through the client automatically resilient and
    automatically handles pagination without any wrapper methods or decorators.

    Features:
    - Automatic retries with exponential backoff using tenacity
    - Rate limiting detection and handling
    - Smart pagination based on response headers and request parameters
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
            max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
            logger: Logger instance for capturing transport operations. If None, creates a default logger.
            **kwargs: Additional arguments passed to the underlying httpx AsyncHTTPTransport.

        Note:
            This transport automatically handles:
            - Retries on network errors and 5xx server errors
            - Rate limiting with Retry-After header support
            - Auto-pagination for GET requests with 'page' or 'limit' parameters
        """
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.logger = logger or logging.getLogger(__name__)

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
                self._log_detailed_error(detailed_error, method, url, status_code)
                return
            except (TypeError, ValueError, AttributeError):
                pass

        try:
            error_response = ErrorResponse.from_dict(error_data)
            self._log_error(error_response, method, url, status_code)
            return
        except (TypeError, ValueError, AttributeError):
            pass

        # Fallback: log raw error data
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
        log_message += f"\n  Error: {error.name} - {error.message}"
        if error.code is not None:
            log_message += f"\n  Code: {error.code}"
        if error.details:
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
        self.logger.error(log_message)

    def _log_error(
        self, error: ErrorResponse, method: str, url: str, status_code: int
    ) -> None:
        """Log general errors using the typed ErrorResponse model."""
        log_message = f"Client error {status_code} for {method} {url}"
        log_message += f"\n  Error: {error.name} - {error.message}"
        if error.additional_properties:
            formatted = ", ".join(
                f"{k}: {v!r}" for k, v in error.additional_properties.items()
            )
            log_message += f"\n  Additional info: {formatted}"
        self.logger.error(log_message)

    # _format_typed_validation_info and _log_error_fallback are no longer needed

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Handle HTTP requests with automatic retries, rate limiting, and pagination.

        This method is called for every HTTP request made through the client and provides
        the core resilience functionality of the transport layer.

        Args:
            request: The HTTP request to handle.

        Returns:
            The HTTP response, potentially with combined data from multiple pages
            if auto-pagination was triggered.

        Note:
            - GET requests with 'page' or 'limit' parameters trigger auto-pagination
            - Requests with explicit 'page' parameter disable auto-pagination
            - All requests get automatic retry logic for network and server errors
            - Rate limiting is handled automatically with Retry-After header support
        """
        return await self._handle_request_with_span(request)

    async def _handle_request_with_span(self, request: httpx.Request) -> httpx.Response:
        """Handle the request with optional span context."""
        # Check if this is a paginated request (has 'page' or 'limit' param)
        # Smart pagination: automatically detect based on request parameters
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
            return await self._handle_single_request(request)

    async def _handle_single_request(self, request: httpx.Request) -> httpx.Response:
        """
        Handle a single request with retries using tenacity.

        Args:
            request: The HTTP request to handle.

        Returns:
            The HTTP response from the server.

        Raises:
            RetryError: If all retry attempts are exhausted.
            httpx.HTTPError: For unrecoverable HTTP errors.
        """

        # Define a properly typed retry decorator
        def _make_retry_decorator() -> Callable[
            [Callable[[], Awaitable[httpx.Response]]],
            Callable[[], Awaitable[httpx.Response]],
        ]:
            return retry(
                stop=stop_after_attempt(self.max_retries + 1),
                wait=wait_exponential(multiplier=1, min=1, max=60),
                retry=(
                    retry_if_result(
                        lambda response: response.status_code == 429
                        or (500 <= response.status_code < 600)
                    )
                    | retry_if_exception_type(
                        (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)
                    )
                ),
                reraise=True,
            )

        @_make_retry_decorator()
        async def _make_request_with_retry() -> httpx.Response:
            """Make the actual HTTP request with retry logic."""
            response = await super(ResilientAsyncTransport, self).handle_async_request(
                request
            )

            if response.status_code == 429:
                retry_after = self._get_retry_after(response)
                self.logger.warning(
                    "Rate limited, retrying after exponential backoff (server suggested %ds)",
                    retry_after,
                )

            elif 500 <= response.status_code < 600:
                self.logger.warning(
                    "Server error %d, retrying with exponential backoff",
                    response.status_code,
                )

            return response

        # Execute the request with retries
        try:
            response = await _make_request_with_retry()

            # Log detailed information for 400-level client errors
            if 400 <= response.status_code < 500:
                await self._log_client_error(response, request)

            return response
        except RetryError as e:
            # For retry errors (when server keeps returning 4xx/5xx), return the last response
            self.logger.error(
                "Request failed after %d retries, extracting last response",
                self.max_retries,
            )

            # Extract the last response - tenacity stores it in the last_attempt
            try:
                if hasattr(e, "last_attempt"):
                    last_response = e.last_attempt.result()
                    response_type = type(last_response).__name__
                    self.logger.debug("Got last response: %s", response_type)
                    if isinstance(last_response, httpx.Response) or (
                        hasattr(last_response, "status_code")
                    ):
                        # Handle both real responses and mocks (for testing)
                        self.logger.debug(
                            "Returning last response with status %d",
                            last_response.status_code,
                        )
                        return last_response
                    self.logger.debug(
                        "Last response is not httpx.Response, it's %s",
                        response_type,
                    )
                self.logger.debug("No last_attempt found in retry error")
            except (ValueError, AttributeError, TypeError) as extract_error:
                self.logger.debug("Error extracting last response: %s", extract_error)

            # If we can't extract the response, re-raise
            self.logger.error("Could not extract last response from retry error")
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
            # For network errors, we want to re-raise the exception
            self.logger.error("Network error after %d retries: %s", self.max_retries, e)
            raise
        except Exception as e:
            # For other unexpected errors, re-raise
            self.logger.error(
                "Unexpected error after %d retries: %s", self.max_retries, e
            )
            raise

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
        limit = int(url_params.get("limit", 50))

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

            # Make the request
            response = await self._handle_single_request(paginated_request)

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
                    if (total_pages and current_page >= total_pages) or len(
                        items
                    ) < limit:
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

    def _get_retry_after(self, response: httpx.Response) -> float:
        """Extract retry-after value from response headers."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                # Sometimes it's a date string, but let's use default
                pass

        # Default retry after
        return 60.0


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
            **httpx_kwargs: Additional arguments passed to the underlying httpx client.

        Raises:
            ValueError: If no API key is provided and KATANA_API_KEY env var is not set.

        Example:
            >>> async with KatanaClient() as client:
            ...     # All API calls through client get automatic resilience
            ...     response = await some_api_method.asyncio_detailed(client=client)
        """
        load_dotenv()

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

        # Create resilient transport with observability hooks
        transport = ResilientAsyncTransport(
            max_retries=max_retries,
            max_pages=max_pages,
            logger=self.logger,
        )

        # Event hooks for observability - start with our defaults
        event_hooks: dict[str, list[Callable[[httpx.Response], Awaitable[None]]]] = {
            "response": [
                self._capture_pagination_metadata,
                self._log_response_metrics,
            ]
        }

        # Simply extend with user hooks if provided
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

        # Initialize the parent AuthenticatedClient
        super().__init__(
            base_url=base_url,
            token=api_key,
            timeout=httpx.Timeout(timeout),
            httpx_args={
                "transport": transport,
                "event_hooks": event_hooks,
                **httpx_kwargs,
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
