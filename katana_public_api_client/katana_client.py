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
from typing import TYPE_CHECKING, Any, cast

import httpx
from dotenv import load_dotenv
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    from httpx import AsyncHTTPTransport
else:
    AsyncHTTPTransport = httpx.AsyncHTTPTransport

from .generated.client import AuthenticatedClient

# OpenTracing imports - conditional to avoid hard dependency
try:
    import opentracing
    from opentracing import Tracer
    from opentracing.ext import tags

    OPENTRACING_AVAILABLE = True
except ImportError:
    opentracing = None  # type: ignore[assignment]
    Tracer = None  # type: ignore[assignment,misc]
    tags = None  # type: ignore[assignment]
    OPENTRACING_AVAILABLE = False


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
    - Optional OpenTracing support for distributed tracing
    """

    def __init__(
        self,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: logging.Logger | None = None,
        tracer: "Tracer | None" = None,
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
        self.tracer = tracer

        # Warn if OpenTracing is requested but not available
        if tracer is not None and not OPENTRACING_AVAILABLE:
            self.logger.warning(
                "OpenTracing tracer provided but opentracing library is not installed. "
                "Install with: pip install 'katana-openapi-client[tracing]'"
            )

    async def _log_client_error(
        self, response: httpx.Response, request: httpx.Request
    ) -> None:
        """
        Log detailed information for 400-level client errors.

        Provides enhanced logging for validation errors (422) and other client errors,
        extracting and formatting error details from the response body.

        Args:
            response: The HTTP response with a 400-level status code
            request: The original HTTP request that triggered the error
        """
        try:
            # Get basic request information
            method = request.method
            url = str(request.url)
            status_code = response.status_code

            # Try to parse the JSON error response
            try:
                error_data = response.json()
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If JSON parsing fails, log the raw response
                self.logger.error(
                    f"Client error {status_code} for {method} {url} - "
                    f"Response: {response.text[:500]}..."
                )
                return

            # Format the error message based on the error structure
            if status_code == 422 and isinstance(error_data, dict):
                # Enhanced logging for 422 validation errors
                self._log_validation_error(error_data, method, url, status_code)
            else:
                # General 400-level error logging
                self._log_general_client_error(error_data, method, url, status_code)

        except Exception as e:
            # Fallback logging if error parsing fails
            self.logger.error(
                f"Client error {response.status_code} for {request.method} {request.url} - "
                f"Failed to parse error details: {e}"
            )

    def _log_validation_error(
        self, error_data: dict[str, Any], method: str, url: str, status_code: int
    ) -> None:
        """Log detailed validation error information for 422 responses."""
        error_name = error_data.get("name", "UnprocessableEntityError")
        error_message = error_data.get("message", "Validation failed")
        error_code = error_data.get("code", "")
        details = error_data.get("details", [])

        # Start with the main error message
        log_message = f"Validation error {status_code} for {method} {url}"
        log_message += f"\n  Error: {error_name} - {error_message}"

        if error_code:
            log_message += f"\n  Code: {error_code}"

        # Add detailed validation errors
        if details and isinstance(details, list):
            log_message += f"\n  Validation details ({len(details)} errors):"
            for i, detail in enumerate(details, 1):
                # Type check each detail item
                if isinstance(detail, dict):
                    # Cast to dict[str, Any] for proper type inference
                    detail_dict = cast(dict[str, Any], detail)
                    path = detail_dict.get("path", "unknown")
                    code = detail_dict.get("code", "unknown")
                    message = detail_dict.get("message", "")
                    info = detail_dict.get("info", {})

                    log_message += f"\n    {i}. Path: {path}"
                    log_message += f"\n       Code: {code}"
                    if message:
                        log_message += f"\n       Message: {message}"
                    if info and isinstance(info, dict):
                        log_message += self._format_validation_info(info)
                else:
                    # Handle non-dict details gracefully
                    log_message += f"\n    {i}. {detail}"

        self.logger.error(log_message)

    def _format_validation_info(self, info: dict[str, Any]) -> str:
        """Format validation error info dictionary into a readable string."""
        if not info:
            return ""

        formatted_parts = []

        # Handle common validation info fields with nice formatting
        if "provided_value" in info:
            provided = info["provided_value"]
            if provided is None:
                formatted_parts.append("provided: null")
            elif isinstance(provided, str):
                formatted_parts.append(f"provided: '{provided}'")
            else:
                formatted_parts.append(f"provided: {provided}")

        if "allowed_values" in info:
            allowed = info["allowed_values"]
            if isinstance(allowed, list):
                if len(allowed) <= 5:
                    # Show all values if 5 or fewer
                    values_str = ", ".join(
                        f"'{v}'" if isinstance(v, str) else str(v) for v in allowed
                    )
                    formatted_parts.append(f"allowed: [{values_str}]")
                else:
                    # Show first few and count for long lists
                    first_few = allowed[:3]
                    values_str = ", ".join(
                        f"'{v}'" if isinstance(v, str) else str(v) for v in first_few
                    )
                    formatted_parts.append(
                        f"allowed: [{values_str}... ({len(allowed)} total)]"
                    )
            else:
                formatted_parts.append(f"allowed: {allowed}")

        if "expected_type" in info:
            formatted_parts.append(f"expected type: {info['expected_type']}")

        if "min_value" in info:
            formatted_parts.append(f"min: {info['min_value']}")

        if "max_value" in info:
            formatted_parts.append(f"max: {info['max_value']}")

        if "min_length" in info:
            formatted_parts.append(f"min length: {info['min_length']}")

        if "max_length" in info:
            formatted_parts.append(f"max length: {info['max_length']}")

        if "pattern" in info:
            formatted_parts.append(f"pattern: {info['pattern']}")

        # Handle any other fields that weren't specifically formatted
        handled_keys = {
            "provided_value",
            "allowed_values",
            "expected_type",
            "min_value",
            "max_value",
            "min_length",
            "max_length",
            "pattern",
        }
        other_fields = {k: v for k, v in info.items() if k not in handled_keys}

        if other_fields:
            for key, value in other_fields.items():
                if isinstance(value, str):
                    formatted_parts.append(f"{key}: '{value}'")
                else:
                    formatted_parts.append(f"{key}: {value}")

        if formatted_parts:
            return f"\n       Details: {', '.join(formatted_parts)}"
        else:
            return ""

    def _log_general_client_error(
        self, error_data: dict[str, Any], method: str, url: str, status_code: int
    ) -> None:
        """Log general client error information for non-422 4xx responses."""
        if isinstance(error_data, dict):
            error_name = error_data.get("name", f"ClientError{status_code}")
            error_message = error_data.get("message", "Client error occurred")
            error_code = error_data.get("code", "")

            log_message = f"Client error {status_code} for {method} {url}"
            log_message += f"\n  Error: {error_name} - {error_message}"

            if error_code:
                log_message += f"\n  Code: {error_code}"

            # Log any additional fields that might be present
            additional_fields = {
                k: v
                for k, v in error_data.items()
                if k not in {"statusCode", "name", "message", "code"}
            }
            if additional_fields:
                formatted_additional = []
                for key, value in additional_fields.items():
                    if isinstance(value, str):
                        formatted_additional.append(f"{key}: '{value}'")
                    elif isinstance(value, dict) and value:
                        # Format nested dicts more nicely
                        nested_items = []
                        for nested_key, nested_value in value.items():
                            if isinstance(nested_value, str):
                                nested_items.append(f"{nested_key}: '{nested_value}'")
                            else:
                                nested_items.append(f"{nested_key}: {nested_value}")
                        formatted_additional.append(
                            f"{key}: {{{', '.join(nested_items)}}}"
                        )
                    else:
                        formatted_additional.append(f"{key}: {value}")
                log_message += f"\n  Additional info: {', '.join(formatted_additional)}"

            self.logger.error(log_message)
        else:
            # If error_data is not a dict, log it as-is
            self.logger.error(
                f"Client error {status_code} for {method} {url} - "
                f"Response: {error_data}"
            )

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
        # Create OpenTracing span if tracer is configured
        if self.tracer is not None and OPENTRACING_AVAILABLE:
            with self.tracer.start_span(
                operation_name=f"katana_client.{request.method}",
                tags={
                    tags.COMPONENT: "katana-openapi-client",
                    tags.HTTP_METHOD: request.method,
                    tags.HTTP_URL: str(request.url),
                    tags.SPAN_KIND: tags.SPAN_KIND_RPC_CLIENT,
                },
            ) as span:
                try:
                    response = await self._handle_request_with_span(request, span)
                    # Tag successful responses
                    span.set_tag(tags.HTTP_STATUS_CODE, response.status_code)
                    if response.status_code >= 400:
                        span.set_tag(tags.ERROR, True)
                    return response
                except Exception as e:
                    # Tag errors
                    span.set_tag(tags.ERROR, True)
                    span.log_kv({"error": str(e)})
                    raise
        else:
            # No tracing, use original logic
            return await self._handle_request_with_span(request, None)

    async def _handle_request_with_span(
        self, request: httpx.Request, span: Any = None
    ) -> httpx.Response:
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
            if span is not None:
                span.set_tag("katana.pagination.enabled", True)
            return await self._handle_paginated_request(request, span)
        else:
            return await self._handle_single_request(request, span)

    async def _handle_single_request(
        self, request: httpx.Request, span: Any = None
    ) -> httpx.Response:
        """
        Handle a single request with retries using tenacity.

        Args:
            request: The HTTP request to handle.
            span: Optional OpenTracing span for distributed tracing.

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
                    f"Rate limited, retrying after exponential backoff (server suggested {retry_after}s)"
                )
                if span is not None:
                    span.log_kv({"event": "rate_limited", "retry_after": retry_after})

            elif 500 <= response.status_code < 600:
                self.logger.warning(
                    f"Server error {response.status_code}, retrying with exponential backoff"
                )
                if span is not None:
                    span.log_kv(
                        {"event": "server_error", "status_code": response.status_code}
                    )

            return response

        # Execute the request with retries
        try:
            response = await _make_request_with_retry()
            if span is not None:
                span.set_tag("katana.retry.success", True)

            # Log detailed information for 400-level client errors
            if 400 <= response.status_code < 500:
                await self._log_client_error(response, request)

            return response
        except RetryError as e:
            # For retry errors (when server keeps returning 4xx/5xx), return the last response
            if span is not None:
                span.set_tag("katana.retry.exhausted", True)
            self.logger.error(
                f"Request failed after {self.max_retries} retries, extracting last response"
            )

            # Extract the last response - tenacity stores it in the last_attempt
            try:
                if hasattr(e, "last_attempt") and e.last_attempt is not None:
                    last_response = e.last_attempt.result()
                    self.logger.debug(f"Got last response: {type(last_response)}")
                    if isinstance(last_response, httpx.Response) or (
                        hasattr(last_response, "status_code")
                    ):
                        # Handle both real responses and mocks (for testing)
                        self.logger.debug(
                            f"Returning last response with status {last_response.status_code}"
                        )
                        return last_response
                    else:
                        self.logger.debug(
                            f"Last response is not httpx.Response, it's {type(last_response)}"
                        )
                else:
                    self.logger.debug("No last_attempt found in retry error")
            except Exception as extract_error:
                self.logger.debug(f"Error extracting last response: {extract_error}")

            # If we can't extract the response, re-raise
            self.logger.error("Could not extract last response from retry error")
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError) as e:
            # For network errors, we want to re-raise the exception
            self.logger.error(f"Network error after {self.max_retries} retries: {e}")
            raise
        except Exception as e:
            # For other unexpected errors, re-raise
            self.logger.error(f"Unexpected error after {self.max_retries} retries: {e}")
            raise

    async def _handle_paginated_request(
        self, request: httpx.Request, span: Any = None
    ) -> httpx.Response:
        """
        Handle paginated requests by automatically collecting all pages.

        This method detects paginated responses and automatically collects all available
        pages up to the configured maximum. It preserves the original request structure
        while combining data from multiple pages.

        Args:
            request: The HTTP request to handle (must be a GET request with pagination parameters).
            span: Optional OpenTracing span for distributed tracing.

        Returns:
            A combined HTTP response containing data from all collected pages with
            pagination metadata in the response body.

        Note:
            - Only GET requests with 'limit' parameter trigger auto-pagination
            - Requests with explicit 'page' parameter are treated as single-page requests
            - The response contains an 'auto_paginated' flag in the pagination metadata
            - Data from all pages is combined into a single 'data' array
        """
        all_data = []
        current_page = 1
        total_pages = None

        # Parse initial parameters
        url_params = dict(request.url.params)
        limit = int(url_params.get("limit", 50))

        self.logger.info(f"Auto-paginating request: {request.url}")

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
            response = await self._handle_single_request(paginated_request, span)

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
                        f"Collected page {current_page}/{total_pages or '?'}, "
                        f"items: {len(items)}, total so far: {len(all_data)}"
                    )
                else:
                    # No pagination info found, treat as single page
                    all_data = data.get("data", data if isinstance(data, list) else [])
                    break

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning(f"Failed to parse paginated response: {e}")
                return response

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
            f"Auto-pagination complete: collected {len(all_data)} items from {page_num} pages"
        )

        # Add pagination tracing info
        if span is not None:
            span.set_tag("katana.pagination.pages_collected", page_num)
            span.set_tag("katana.pagination.total_items", len(all_data))
            if total_pages:
                span.set_tag("katana.pagination.total_pages", total_pages)

        return combined_response

    def _extract_pagination_info(
        self, response: httpx.Response, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract pagination information from response headers or body."""
        pagination_info = {}

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
        if isinstance(data, dict):
            if "pagination" in data:
                pagination_info.update(data["pagination"])
            elif "meta" in data and "pagination" in data["meta"]:
                pagination_info.update(data["meta"]["pagination"])

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
    - Optional OpenTracing support for distributed tracing
    - Minimal configuration - just works out of the box

    Usage:
        # Auto-pagination happens automatically - just call the API
        async with KatanaClient() as client:
            from katana_public_api_client.generated.api.product import get_all_products

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

        # With OpenTracing support
        import opentracing
        tracer = opentracing.tracer  # or configure your tracer
        async with KatanaClient(tracer=tracer) as client:
            # All requests will be automatically traced
            response = await get_all_products.asyncio_detailed(
                client=client,
                limit=50
            )
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: logging.Logger | None = None,
        tracer: "Tracer | None" = None,
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
            tracer: Optional OpenTracing tracer for distributed tracing support.
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
            tracer=tracer,
        )

        # Event hooks for observability
        event_hooks = {
            "response": [
                self._capture_pagination_metadata,
                self._log_response_metrics,
            ]
        }

        # Merge with any user-provided event hooks
        user_hooks = httpx_kwargs.pop("event_hooks", {})
        for event, hooks in user_hooks.items():
            if event in event_hooks:
                if isinstance(hooks, list):
                    event_hooks[event].extend(hooks)
                else:
                    event_hooks[event].append(hooks)
            else:
                event_hooks[event] = hooks if isinstance(hooks, list) else [hooks]

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


# Demo function to show usage
async def demo_katana_client():
    """Demonstrate the simplified KatanaClient usage."""

    async with KatanaClient() as client:
        from katana_public_api_client.generated.api.product import get_all_products

        print("=== KatanaClient Demo ===")
        print(
            "All API calls automatically have auto-pagination - no manual setup needed!"
        )
        print()

        # Direct API usage with automatic pagination
        print("1. Direct API call with automatic pagination:")
        response = await get_all_products.asyncio_detailed(
            client=client,
            limit=50,  # Will automatically paginate if needed
        )
        print(f"   Response status: {response.status_code}")
        if (
            hasattr(response, "parsed")
            and response.parsed
            and hasattr(response.parsed, "data")
        ):
            data = response.parsed.data
            if isinstance(data, list):
                print(f"   Total items collected: {len(data)}")
        print()

        # Single page only
        print("2. Single page only (disable auto-pagination):")
        response = await get_all_products.asyncio_detailed(
            client=client,
            page=1,
            limit=25,  # page=X disables auto-pagination
        )
        print(f"   Response status: {response.status_code}")
        if (
            hasattr(response, "parsed")
            and response.parsed
            and hasattr(response.parsed, "data")
        ):
            data = response.parsed.data
            if isinstance(data, list):
                print(f"   Single page items: {len(data)}")
        print()

        # Limited pagination
        print("3. Limited auto-pagination:")
        limited_client = KatanaClient(max_pages=2)  # Limit to 2 pages max
        async with limited_client as api_client:
            response = await get_all_products.asyncio_detailed(
                client=api_client, limit=25
            )
            print(f"   Response status: {response.status_code}")
            if (
                hasattr(response, "parsed")
                and response.parsed
                and hasattr(response.parsed, "data")
            ):
                data = response.parsed.data
                if isinstance(data, list):
                    print(f"   Total items collected (max 2 pages): {len(data)}")
        print()

        print(
            "✨ That's it! No helpers, no manual pagination, just direct API calls with automatic resilience."
        )


if __name__ == "__main__":
    import asyncio
    import logging

    # Set up logging to see the transport in action
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(demo_katana_client())
