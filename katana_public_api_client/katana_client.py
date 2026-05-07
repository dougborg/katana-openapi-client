"""
KatanaClient - The pythonic Katana API client with automatic resilience.

This client uses httpx's native transport layer to provide automatic retries,
rate limiting, error handling, and pagination for all API calls without any
decorators or wrapper methods needed.
"""

import asyncio
import contextlib
import json
import logging
import netrc
import os
import time
from collections.abc import Awaitable, Callable
from http import HTTPStatus
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse

import httpx
from dotenv import load_dotenv
from httpx import AsyncBaseTransport, AsyncHTTPTransport
from httpx_retries import Retry, RetryTransport
from pyrate_limiter import Duration, Limiter, Rate

from ._logging import Logger
from .api_wrapper import ApiNamespace
from .client import AuthenticatedClient
from .client_types import Unset
from .helpers.materials import Materials
from .helpers.products import Products
from .helpers.services import Services
from .helpers.variants import Variants
from .models.additional_properties_validation_error import (
    AdditionalPropertiesValidationError,
)
from .models.const_validation_error import ConstValidationError
from .models.dependencies_validation_error import DependenciesValidationError
from .models.detailed_error_response import DetailedErrorResponse
from .models.enum_validation_error import EnumValidationError
from .models.error_response import ErrorResponse
from .models.exclusive_maximum_validation_error import (
    ExclusiveMaximumValidationError,
)
from .models.exclusive_minimum_validation_error import (
    ExclusiveMinimumValidationError,
)
from .models.format_validation_error import FormatValidationError
from .models.max_items_validation_error import MaxItemsValidationError
from .models.max_length_validation_error import MaxLengthValidationError
from .models.maximum_validation_error import MaximumValidationError
from .models.min_items_validation_error import MinItemsValidationError
from .models.min_length_validation_error import MinLengthValidationError
from .models.minimum_validation_error import MinimumValidationError
from .models.multiple_of_validation_error import MultipleOfValidationError
from .models.one_of_validation_error import OneOfValidationError
from .models.pattern_validation_error import PatternValidationError
from .models.required_validation_error import RequiredValidationError
from .models.type_validation_error import TypeValidationError
from .models.unique_items_validation_error import UniqueItemsValidationError

# Patterns used to identify sensitive query parameters and body fields in logs.
# Values matching these patterns are redacted to prevent information disclosure.
# See also: katana_mcp_server/src/katana_mcp/logging.py filter_sensitive_data()
# for the MCP equivalent.
_SENSITIVE_PARAMS: frozenset[str] = frozenset(
    {
        "api_key",
        "auth",
        "authorization",
        "credential",
        "email",
        "key",
        "password",
        "secret",
        "token",
    }
)

_REDACTED = "***"


def _is_sensitive(name: str) -> bool:
    """Check if a parameter/field name matches any sensitive pattern."""
    lower = name.lower()
    return any(pattern in lower for pattern in _SENSITIVE_PARAMS)


def _sanitize_url(url: str) -> str:
    """Redact sensitive query parameter values from a URL for safe logging."""
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        params = parse_qs(parsed.query, keep_blank_values=True)
        sanitized = {}
        for k, values in params.items():
            if _is_sensitive(k):
                sanitized[k] = [_REDACTED]
            else:
                sanitized[k] = values
        # Use urlencode with custom quote function that preserves * characters
        clean_query = urlencode(
            sanitized,
            doseq=True,
            quote_via=lambda s, safe="", encoding=None, errors=None: quote(
                s, safe=safe + "*", encoding=encoding, errors=errors
            ),
        )
        return urlunparse(parsed._replace(query=clean_query))
    except Exception:
        # If URL parsing fails, strip the query string entirely
        base, _, _ = url.partition("?")
        return f"{base}?{_REDACTED}"


def _sanitize_body(body: Any) -> Any:
    """Redact sensitive field values from nested dict/list bodies for safe logging."""

    def _sanitize_value(value: Any) -> Any:
        """Recursively sanitize nested structures."""
        if isinstance(value, dict):
            return {
                k: _REDACTED if _is_sensitive(k) else _sanitize_value(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [_sanitize_value(item) for item in value]
        return value

    if not isinstance(body, dict):
        return "[non-dict body]"
    return _sanitize_value(body)


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


def _extract_nested_error(
    additional_properties: dict[str, Any],
) -> tuple[str | None, str | None, int | None, list[dict[str, str]]]:
    """Extract typed error fields from an untyped additional_properties dict.

    The Katana API sometimes returns error details in a nested structure within
    additional_properties rather than in the typed model fields. This function
    safely extracts those fields with proper typing.

    Returns:
        Tuple of (name, message, status_code, detail_dicts) where detail_dicts
        is a list of dicts that always include a 'path' string key and may
        optionally include 'code' and 'message' string keys.
    """
    name: str | None = None
    message: str | None = None
    status_code: int | None = None
    details: list[dict[str, str]] = []

    nested_error = additional_properties.get("error")
    if not isinstance(nested_error, dict):
        return name, message, status_code, details

    raw_name = nested_error.get("name")
    if isinstance(raw_name, str):
        name = raw_name
    raw_message = nested_error.get("message")
    if isinstance(raw_message, str):
        message = raw_message
    raw_code = nested_error.get("statusCode")
    if isinstance(raw_code, int):
        status_code = raw_code

    raw_details = nested_error.get("details")
    if isinstance(raw_details, list):
        for item in raw_details:
            if isinstance(item, dict):
                detail: dict[str, str] = {
                    "path": str(item.get("path", "unknown")),
                }
                raw_code_val = item.get("code")
                if raw_code_val is not None:
                    detail["code"] = str(raw_code_val)
                raw_msg_val = item.get("message")
                if raw_msg_val is not None:
                    detail["message"] = str(raw_msg_val)
                details.append(detail)

    return name, message, status_code, details


class ErrorLoggingTransport(AsyncBaseTransport):
    """
    Transport layer that adds detailed error logging for 4xx client errors.

    This transport wraps another transport and intercepts responses to log
    detailed error information using the generated error models. Inherits
    from ``AsyncBaseTransport`` (not ``AsyncHTTPTransport``) so we don't
    spin up an unused connection pool inside this layer; all I/O goes
    through the wrapped transport.
    """

    def __init__(
        self,
        wrapped_transport: AsyncBaseTransport | None = None,
        logger: Logger | None = None,
        **kwargs: Any,
    ):
        """
        Initialize the error logging transport.

        Args:
            wrapped_transport: The transport to wrap. If None, creates a new AsyncHTTPTransport.
            logger: Logger instance for capturing error details. If None, creates a default logger.
            **kwargs: Additional arguments passed to AsyncHTTPTransport if wrapped_transport is None.
        """
        if wrapped_transport is None:
            wrapped_transport = AsyncHTTPTransport(**kwargs)
        self._wrapped_transport = wrapped_transport
        self.logger: Logger = logger or logging.getLogger(__name__)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request and log detailed error information for 4xx responses."""
        response = await self._wrapped_transport.handle_async_request(request)

        # Log detailed information for 400-level client errors
        if 400 <= response.status_code < 500:
            await self._log_client_error(response, request)

        return response

    async def aclose(self) -> None:
        """Propagate close down the wrapped chain so inner transports release resources."""
        await self._wrapped_transport.aclose()

    async def _log_client_error(
        self, response: httpx.Response, request: httpx.Request
    ) -> None:
        """
        Log detailed information for 400-level client errors using generated models.
        Assumes error responses are always typed (DetailedErrorResponse or ErrorResponse).
        """
        method = request.method
        url = _sanitize_url(str(request.url))
        status_code = response.status_code

        # Capture request body for validation error context
        request_body = None
        if request.content:
            with contextlib.suppress(
                json.JSONDecodeError, UnicodeDecodeError, AttributeError, TypeError
            ):
                request_body = json.loads(request.content.decode("utf-8"))

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
            # Try parsing directly, then try unwrapping nested 'error' key
            parse_attempts = [error_data]
            if isinstance(error_data, dict) and "error" in error_data:
                parse_attempts.append(error_data["error"])
            for attempt_data in parse_attempts:
                # Skip dicts that lack all error fields (e.g. wrapper like {"error": {...}})
                if isinstance(attempt_data, dict) and not any(
                    k in attempt_data for k in ("statusCode", "name", "message")
                ):
                    continue
                try:
                    detailed_error = DetailedErrorResponse.from_dict(attempt_data)
                    self.logger.debug(
                        f"Parsed DetailedErrorResponse - "
                        f"details type: {type(detailed_error.details)}, "
                        f"details value: {detailed_error.details}, "
                        f"is Unset: {isinstance(detailed_error.details, Unset)}, "
                        f"raw error_data: {_sanitize_body(error_data)}"
                    )
                    self._log_detailed_error(
                        detailed_error, method, url, status_code, request_body
                    )
                    return
                except (TypeError, ValueError, AttributeError, KeyError) as e:
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
            f"Client error {status_code} for {method} {url} - "
            f"Raw error: {_sanitize_body(error_data)}"
        )

    def _log_detailed_error(
        self,
        error: DetailedErrorResponse,
        method: str,
        url: str,
        status_code: int,
        request_body: dict[str, Any] | None = None,
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
            and error.additional_properties
        ):
            nested_name, nested_msg, nested_code, _ = _extract_nested_error(
                error.additional_properties
            )
            if nested_name is not None:
                error_name = nested_name
            if nested_msg is not None:
                error_message = nested_msg
            if nested_code is not None and error_code is None:
                error_code = nested_code

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
                log_message += f"\n       Code: {detail.code}"
                log_message += f"\n       Message: {detail.message}"

                # Type-safe extraction of sent value from request body. Ajv's
                # ``instancePath`` arrives in two flavors depending on Ajv
                # config: JSON Pointer (``/foo/bar``) or legacy ``dataPath``
                # (``.foo.bar``). Strip both so a top-level field like
                # ``.email`` resolves against ``request_body["email"]``.
                sent_value = None
                if request_body and detail.path:
                    field_path = detail.path.lstrip("/.")
                    if "/" not in field_path and "." not in field_path:
                        sent_value = request_body.get(field_path)
                    if sent_value is not None and _is_sensitive(field_path):
                        sent_value = _REDACTED

                # Ajv-keyword-specific augmentation. Each branch surfaces the
                # ``info.*`` payload alongside the value that was actually
                # sent (where helpful) so the log entry tells operators
                # exactly what to fix.
                if isinstance(detail, EnumValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += (
                        f"\n       Allowed values: {detail.info.allowed_values}"
                    )

                elif isinstance(detail, MinimumValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Minimum allowed: {detail.info.limit}"

                elif isinstance(detail, MaximumValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Maximum allowed: {detail.info.limit}"

                elif isinstance(detail, ExclusiveMinimumValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Must be > {detail.info.limit}"

                elif isinstance(detail, ExclusiveMaximumValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Must be < {detail.info.limit}"

                elif isinstance(detail, MultipleOfValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += (
                        f"\n       Must be a multiple of: {detail.info.multiple_of}"
                    )

                elif isinstance(detail, TypeValidationError):
                    if sent_value is not None:
                        sent_type = type(sent_value).__name__
                        log_message += (
                            f"\n       Sent value: {sent_value!r} (type: {sent_type})"
                        )
                    log_message += f"\n       Expected type: {detail.info.type_}"

                elif isinstance(detail, MinLengthValidationError):
                    if sent_value is not None and isinstance(sent_value, list | str):
                        log_message += f"\n       Sent value length: {len(sent_value)}"
                    log_message += f"\n       Minimum length: {detail.info.limit}"

                elif isinstance(detail, MaxLengthValidationError):
                    if sent_value is not None and isinstance(sent_value, list | str):
                        log_message += f"\n       Sent value length: {len(sent_value)}"
                    log_message += f"\n       Maximum length: {detail.info.limit}"

                elif isinstance(detail, MinItemsValidationError):
                    if sent_value is not None and isinstance(sent_value, list | str):
                        log_message += f"\n       Sent value length: {len(sent_value)}"
                    log_message += f"\n       Minimum items: {detail.info.limit}"

                elif isinstance(detail, MaxItemsValidationError):
                    if sent_value is not None and isinstance(sent_value, list | str):
                        log_message += f"\n       Sent value length: {len(sent_value)}"
                    log_message += f"\n       Maximum items: {detail.info.limit}"

                elif isinstance(detail, UniqueItemsValidationError):
                    log_message += (
                        f"\n       Duplicate at indices: {detail.info.i}, "
                        f"{detail.info.j}"
                    )

                elif isinstance(detail, RequiredValidationError):
                    log_message += (
                        f"\n       Missing required field: "
                        f"{detail.info.missing_property}"
                    )
                    if request_body:
                        provided_fields = list(request_body.keys())
                        log_message += f"\n       Provided fields: {provided_fields}"

                elif isinstance(detail, AdditionalPropertiesValidationError):
                    log_message += (
                        f"\n       Unexpected property: "
                        f"{detail.info.additional_property}"
                    )

                elif isinstance(detail, DependenciesValidationError):
                    log_message += (
                        f"\n       Property '{detail.info.property_}' requires "
                        f"'{detail.info.missing_property}'"
                    )

                elif isinstance(detail, PatternValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Required pattern: {detail.info.pattern}"

                elif isinstance(detail, FormatValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += f"\n       Required format: {detail.info.format_}"

                elif isinstance(detail, ConstValidationError):
                    if sent_value is not None:
                        log_message += f"\n       Sent value: {sent_value!r}"
                    log_message += (
                        f"\n       Required value: {detail.info.allowed_value!r}"
                    )

                elif isinstance(detail, OneOfValidationError):
                    passing = detail.info.passing_schemas
                    if passing is None:
                        log_message += (
                            "\n       Did not match any allowed schema branch"
                        )
                    else:
                        log_message += (
                            f"\n       Matched multiple branches "
                            f"(indices {passing}); must match exactly one"
                        )

        # Also check additional_properties for nested error details
        if hasattr(error, "additional_properties") and error.additional_properties:
            _, _, _, nested_details = _extract_nested_error(error.additional_properties)
            if nested_details:
                log_message += (
                    f"\n  Nested validation details ({len(nested_details)} errors):"
                )
                for i, d in enumerate(nested_details, 1):
                    log_message += f"\n    {i}. Path: {d.get('path', 'unknown')}"
                    if "code" in d:
                        log_message += f"\n       Code: {d['code']}"
                    if "message" in d:
                        log_message += f"\n       Message: {d['message']}"

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
            and error.additional_properties
        ):
            nested_name, nested_msg, _, _ = _extract_nested_error(
                error.additional_properties
            )
            if nested_name is not None:
                error_name = nested_name
            if nested_msg is not None:
                error_message = nested_msg

        # Use fallback values if still None
        if error_name is None:
            error_name = "(not provided)"
        if error_message is None:
            error_message = "(not provided)"

        log_message += f"\n  Error: {error_name} - {error_message}"

        if error.additional_properties:
            sanitized = _sanitize_body(error.additional_properties)
            formatted = ", ".join(f"{k}: {v!r}" for k, v in sanitized.items())
            log_message += f"\n  Additional info: {formatted}"
        self.logger.error(log_message)


class PaginationTransport(AsyncBaseTransport):
    """
    Transport layer that adds automatic pagination for GET requests.

    This transport wraps another transport and automatically collects all pages
    for GET requests by default. Inherits from ``AsyncBaseTransport`` (not
    ``AsyncHTTPTransport``) so we don't spin up an unused connection pool
    inside this layer; all I/O goes through the wrapped transport.

    Auto-pagination behavior:
    - ON by default for GET requests with NO page parameter in URL
    - Uses 250 items per page (Katana's max) when no limit specified by caller
    - If caller specifies a limit, that limit is used (caller's choice)
    - ANY explicit `page` parameter in URL disables auto-pagination (e.g., `?page=1`)
    - Disabled when request has `extensions={"auto_pagination": False}`
    - Only applies to GET requests (POST, PUT, etc. are never paginated)

    Controlling pagination limits:
    - `max_pages` (constructor): Maximum number of pages to fetch
    - `max_items` (extension): Maximum total items to collect, e.g.,
      `extensions={"max_items": 200}` stops after 200 items
    """

    def __init__(
        self,
        wrapped_transport: AsyncBaseTransport | None = None,
        max_pages: int = 100,
        logger: Logger | None = None,
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
        if wrapped_transport is None:
            wrapped_transport = AsyncHTTPTransport(**kwargs)

        self._wrapped_transport = wrapped_transport
        self.max_pages = max_pages
        self.logger: Logger = logger or logging.getLogger(__name__)

    async def aclose(self) -> None:
        """Propagate close down the wrapped chain so inner transports release resources."""
        await self._wrapped_transport.aclose()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle request with automatic pagination for GET requests.

        Auto-pagination is ON by default for GET requests. It is disabled when:
        - `extensions={"auto_pagination": False}` is set, OR
        - ANY explicit `page` parameter is in the URL (e.g., `?page=1` or `?page=2`)

        To get auto-pagination, simply don't pass a page parameter. The transport
        will automatically use 250 items per page (Katana's max) unless you specify
        a limit, in which case your limit will be respected.
        """
        # Check if auto-pagination is explicitly disabled via request extensions
        auto_pagination = request.extensions.get("auto_pagination", True)

        # ANY page param in URL disables auto-pagination - caller wants specific page
        has_explicit_page = "page" in request.url.params

        # Only paginate GET requests when auto_pagination is enabled and no explicit page
        should_paginate = (
            request.method == "GET" and auto_pagination and not has_explicit_page
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
            request: The HTTP request to handle (must be a GET request).

        Returns:
            A combined HTTP response containing data from all collected pages with
            pagination metadata in the response body.

        Note:
            - Auto-pagination is ON by default for all GET requests
            - If response has no pagination info, returns the single response as-is
            - The response contains an 'auto_paginated' flag in the pagination metadata
            - Data from all pages is combined into a single 'data' array
            - Use `extensions={"max_items": N}` to limit total items collected
        """
        all_data: list[Any] = []
        current_page = 1
        total_pages: int | None = None
        page_num = 1
        response: httpx.Response | None = None
        original_is_raw_list = False

        # Get max_items limit from extensions (None = unlimited)
        max_items: int | None = request.extensions.get("max_items")

        # Parse initial parameters, preserving multi-value query params
        # (e.g., ids=1&ids=2&ids=3). Using multi_items() instead of dict()
        # to avoid losing duplicate keys.
        base_params = [
            (k, v)
            for k, v in request.url.params.multi_items()
            if k not in ("page", "limit")
        ]

        # Get caller's limit or default to 250 (Katana's max) for efficiency
        original_limit = request.url.params.get("limit")
        try:
            page_size = int(original_limit) if original_limit else 250
            if page_size <= 0:
                self.logger.warning(
                    "Invalid limit parameter %r (must be positive), using default 250",
                    original_limit,
                )
                page_size = 250
        except (ValueError, TypeError):
            self.logger.warning(
                "Invalid limit parameter %r, using default 250", original_limit
            )
            page_size = 250

        self.logger.info("Auto-paginating request: %s", _sanitize_url(str(request.url)))

        for page_num in range(1, self.max_pages + 1):
            # Determine limit for this request
            if max_items is not None:
                remaining = max_items - len(all_data)
                if remaining <= 0:
                    break
                current_limit = str(min(page_size, remaining))
            else:
                current_limit = str(page_size)

            # Build params with updated page/limit, preserving all multi-value params
            url_params = [
                *base_params,
                ("page", str(page_num)),
                ("limit", current_limit),
            ]

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

                # Track original response format on first page
                if page_num == 1:
                    original_is_raw_list = isinstance(data, list)

                # Extract pagination info from headers or response body
                pagination_info = self._extract_pagination_info(response, data)

                if pagination_info:
                    current_page = pagination_info.get("page", page_num)
                    total_pages = pagination_info.get("total_pages")

                    # Extract the actual data items
                    if isinstance(data, list):
                        items = data
                    else:
                        items = data.get("data", [])
                    all_data.extend(items)

                    # Check max_items limit
                    if max_items is not None and len(all_data) >= max_items:
                        all_data = all_data[:max_items]  # Truncate to exact limit
                        self.logger.info(
                            "Reached max_items limit (%d), stopping pagination",
                            max_items,
                        )
                        break

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
                    # No pagination info - return response preserving its shape
                    self.logger.info(
                        "No pagination info found, returning single-page response"
                    )
                    # Apply max_items truncation if set
                    if max_items is not None:
                        if isinstance(data, list) and len(data) > max_items:
                            truncated = json.dumps(data[:max_items]).encode()
                            headers = dict(response.headers)
                            headers.pop("content-encoding", None)
                            headers.pop("content-length", None)
                            return httpx.Response(
                                status_code=200,
                                headers=headers,
                                content=truncated,
                                request=request,
                            )
                        if isinstance(data, dict) and "data" in data:
                            items = data["data"]
                            if isinstance(items, list) and len(items) > max_items:
                                data["data"] = items[:max_items]
                                truncated = json.dumps(data).encode()
                                headers = dict(response.headers)
                                headers.pop("content-encoding", None)
                                headers.pop("content-length", None)
                                return httpx.Response(
                                    status_code=200,
                                    headers=headers,
                                    content=truncated,
                                    request=request,
                                )
                    return response

            except (json.JSONDecodeError, KeyError) as e:
                self.logger.warning("Failed to parse paginated response: %s", e)
                return response

        # Ensure we have a response at this point
        if response is None:
            msg = "No response available after pagination"
            raise RuntimeError(msg)

        # Create a combined response, preserving the original response shape
        if original_is_raw_list:
            # Original endpoint returned a raw JSON list - preserve that format
            combined_content = json.dumps(all_data).encode()
        else:
            combined_data: dict[str, Any] = {"data": all_data}
            # Add pagination metadata
            if total_pages:
                combined_data["pagination"] = {
                    "total_pages": total_pages,
                    "collected_pages": page_num,
                    "total_items": len(all_data),
                    "auto_paginated": True,
                }
            combined_content = json.dumps(combined_data).encode()

        # Remove content-encoding headers to avoid compression issues
        headers = dict(response.headers)
        headers.pop("content-encoding", None)
        headers.pop("content-length", None)  # Will be recalculated

        combined_response = httpx.Response(
            status_code=200,
            headers=headers,
            content=combined_content,
            request=request,
        )

        self.logger.info(
            "Auto-pagination complete: collected %d items from %d pages",
            len(all_data),
            page_num,
        )

        return combined_response

    def _normalize_pagination_values(
        self, pagination_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert pagination values from strings to appropriate Python types.

        JSON parsing may return numeric values as strings (e.g., "41" instead of 41).
        String comparison produces incorrect results: "5" >= "41" is True because
        "5" > "4" lexicographically. This method ensures all numeric pagination
        fields are proper integers for correct comparisons.

        Additionally, boolean fields like first_page and last_page may come as
        string values ("true"/"false") and are converted to Python booleans.

        Args:
            pagination_info: Dictionary containing pagination metadata.

        Returns:
            Dictionary with numeric fields converted to integers and boolean
            fields converted to booleans.
        """
        # Fields that should be integers for pagination comparisons
        numeric_fields = [
            "page",
            "total_pages",
            "total_items",
            "limit",
            "offset",
            "count",
            "per_page",
            "current_page",
            "total_records",
        ]

        # Fields that should be booleans (API returns "true"/"false" strings)
        boolean_fields = [
            "first_page",
            "last_page",
        ]

        result = pagination_info.copy()

        # Convert numeric fields
        for field in numeric_fields:
            if field in result:
                value = result[field]
                # Convert string numbers to integers
                if isinstance(value, str):
                    try:
                        result[field] = int(value)
                    except ValueError:
                        self.logger.warning(
                            "Invalid pagination value for %s: %r, removing field",
                            field,
                            value,
                        )
                        # Remove invalid field so fallback values are used
                        del result[field]
                # Already an int or float - ensure it's int
                elif isinstance(value, float):
                    # Warn if float has a fractional part (unexpected for pagination)
                    if value != int(value):
                        self.logger.warning(
                            "Pagination value %s has fractional part: %r, truncating to %d",
                            field,
                            value,
                            int(value),
                        )
                    result[field] = int(value)
                # If it's already an int, leave it as is

        # Convert boolean fields ("true"/"false" strings to Python booleans)
        for field in boolean_fields:
            if field in result:
                value = result[field]
                if isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value == "true":
                        result[field] = True
                    elif lower_value == "false":
                        result[field] = False
                    else:
                        self.logger.warning(
                            "Invalid boolean pagination value for %s: %r, removing field",
                            field,
                            value,
                        )
                        del result[field]
                elif not isinstance(value, bool):
                    # Unexpected type - convert truthy/falsy to bool
                    result[field] = bool(value)

        return result

    def _extract_pagination_info(
        self, response: httpx.Response, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Extract pagination information from response headers or body.

        Note:
            All numeric pagination values (page, total_pages, total_items, etc.)
            are converted to integers to ensure correct comparisons. This is important
            because JSON parsing may return string values, and string comparison
            (e.g., "5" >= "41") produces incorrect results.
        """
        pagination_info: dict[str, Any] = {}

        # Check for X-Pagination header (JSON format)
        if "X-Pagination" in response.headers:
            try:
                header_data = json.loads(response.headers["X-Pagination"])
                # Validate that parsed JSON is a dictionary
                if not isinstance(header_data, dict):
                    self.logger.warning(
                        "X-Pagination header is not a JSON object: %r", header_data
                    )
                else:
                    # Convert numeric string values to integers to avoid string comparison bugs
                    # (e.g., "5" >= "41" is True in string comparison but should be False)
                    pagination_info = self._normalize_pagination_values(header_data)
                    # Only return early if we got valid pagination data
                    if pagination_info:
                        return pagination_info
            except json.JSONDecodeError:
                pass

        # Check for individual headers (with validation for malformed values)
        if "X-Total-Pages" in response.headers:
            try:
                pagination_info["total_pages"] = int(response.headers["X-Total-Pages"])
            except ValueError:
                self.logger.warning(
                    "Invalid X-Total-Pages header value: %s",
                    response.headers["X-Total-Pages"],
                )
        if "X-Current-Page" in response.headers:
            try:
                pagination_info["page"] = int(response.headers["X-Current-Page"])
            except ValueError:
                self.logger.warning(
                    "Invalid X-Current-Page header value: %s",
                    response.headers["X-Current-Page"],
                )

        # Check for pagination in response body
        if "pagination" in data:
            page_data = data["pagination"]
            if isinstance(page_data, dict):
                # page_data is dict from JSON response; iterate to build typed dict
                pagination_info.update({str(k): v for k, v in page_data.items()})
        elif (
            "meta" in data
            and isinstance(data["meta"], dict)
            and "pagination" in data["meta"]
        ):
            meta_pagination = data["meta"]["pagination"]
            if isinstance(meta_pagination, dict):
                pagination_info.update({str(k): v for k, v in meta_pagination.items()})

        # Normalize all numeric values to ensure correct comparisons
        if pagination_info:
            pagination_info = self._normalize_pagination_values(pagination_info)

        return pagination_info if pagination_info else None


# Bucket identifier for pyrate's per-name limiter. We have a single global
# budget, so all requests share one bucket name.
_RATE_LIMIT_BUCKET_NAME = "katana"

# Spec-documented response headers we observe — see
# ``docs/katana-openapi.yaml`` (``X-Pagination`` siblings under ``components/headers``).
_HEADER_REMAINING = "X-Ratelimit-Remaining"
_HEADER_RESET = "X-Ratelimit-Reset"


class RateLimitTransport(AsyncBaseTransport):
    """Proactive rate-limiter that respects Katana's X-Ratelimit-* headers.

    Wraps another transport and gates each request through a pyrate-limiter
    token bucket sized for Katana's documented rate limit (60 req/min by
    default, ``X-Ratelimit-Limit`` per the spec). After every response the
    transport reads ``X-Ratelimit-Remaining`` / ``X-Ratelimit-Reset`` and
    adapts:

    - **Sync down**: when the server reports fewer remaining tokens than our
      local estimate (e.g., another client is sharing the API key), drain
      the local bucket to match. We never sync *up* — the server is
      authoritative on the lower bound only.
    - **Reset gate**: when remaining hits 0, an ``asyncio.Event`` blocks all
      future requests until ``X-Ratelimit-Reset`` elapses. This prevents
      pyrate's bucket from racing ahead of Katana's window.

    Stack placement is innermost (above the base ``AsyncHTTPTransport``):
    every actual HTTP request — including retries from ``RetryTransport``
    above and per-page paginated fetches from ``PaginationTransport`` —
    consumes one token, matching how Katana counts requests server-side.

    ``Retry-After`` waiting on 429 responses stays in ``RetryTransport``
    (urllib3.Retry honors the header via ``respect_retry_after_header=True``).
    Sleeping in this transport on 429 would double-delay; we only update the
    reset gate from headers and let retry handle the actual wait.

    Out-of-order responses are handled correctly: the sync-down logic only
    fires when the response's ``remaining`` is *below* the current estimate,
    so a delayed earlier response with a higher ``remaining`` value won't
    overwrite a fresher (lower) estimate.

    Inherits from ``AsyncBaseTransport`` (not ``AsyncHTTPTransport``) because
    we delegate every request to ``_wrapped_transport`` — there's no need to
    spin up an unused connection pool inside this layer.
    """

    def __init__(
        self,
        wrapped_transport: AsyncBaseTransport | None = None,
        *,
        requests_per_minute: int = 60,
        logger: Logger | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the rate-limit transport.

        Args:
            wrapped_transport: The transport to wrap. If None, creates a new
                AsyncHTTPTransport.
            requests_per_minute: Steady-state request budget. Must be ``> 0``;
                callers wanting to disable the limiter entirely should omit
                this transport from the chain rather than passing 0.
            logger: Logger instance for capturing state changes. If None,
                creates a default logger.
            **kwargs: Additional arguments passed to AsyncHTTPTransport if
                wrapped_transport is None.
        """
        if requests_per_minute <= 0:
            msg = (
                f"requests_per_minute must be positive, got {requests_per_minute}; "
                "to disable rate limiting, omit this transport from the chain"
            )
            raise ValueError(msg)
        if wrapped_transport is None:
            wrapped_transport = AsyncHTTPTransport(**kwargs)
        self._wrapped_transport = wrapped_transport
        self._rpm = requests_per_minute
        self._limiter = Limiter(
            Rate(requests_per_minute, Duration.MINUTE), buffer_ms=50
        )
        self._reset_gate = asyncio.Event()
        self._reset_gate.set()  # initially open — no active reset window
        self._reset_handle: asyncio.TimerHandle | None = None
        # Epoch-ms deadline of the active gate (or ``None`` when the gate is
        # open). Tracks the *latest* observed reset so out-of-order responses
        # with an earlier deadline can't shorten the gate, and so a timer
        # callback whose deadline has been superseded can no-op.
        self._reset_until_epoch_ms: int | None = None
        self._release_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._estimated_remaining = requests_per_minute
        self.logger: Logger = logger or logging.getLogger(__name__)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Acquire a token, forward the request, and observe rate-limit headers."""
        # Block on any active reset window (set when remaining hit 0 on a
        # prior response). Acts as the override on top of pyrate's bucket
        # so we don't fire the burst-budget into a window the server has
        # already declared exhausted.
        await self._reset_gate.wait()

        await self._limiter.try_acquire_async(name=_RATE_LIMIT_BUCKET_NAME)

        # Re-check the gate after acquiring. While this request was queued
        # on pyrate's bucket, a concurrent response observer may have seen
        # ``X-Ratelimit-Remaining: 0`` and engaged the gate; without the
        # second wait, we'd slip past it into the now-exhausted window.
        # Loop until the gate is stably open through both checks: an even
        # later engage during this wait should re-block us. The acquired
        # token is held across the wait — pyrate refills its bucket over
        # the window naturally, so this is not a wasted budget.
        while not self._reset_gate.is_set():
            await self._reset_gate.wait()

        # Optimistically debit our local estimate to match what the server
        # is about to see. Without this, the server's ``X-Ratelimit-Remaining``
        # response would always be one lower than our untouched estimate,
        # causing ``_observe_response`` to drain a redundant token on every
        # request and effectively halve our usable budget. The lock keeps
        # the debit and any concurrent sync-down consistent.
        async with self._lock:
            self._estimated_remaining = max(0, self._estimated_remaining - 1)

        response = await self._wrapped_transport.handle_async_request(request)

        await self._observe_response(response)
        return response

    async def _observe_response(self, response: httpx.Response) -> None:
        """Parse rate-limit headers and update local state.

        Defensive: many endpoints (auth flows, redirects, error pages) omit
        these headers — silent no-op when absent. Only successful API
        responses on the rate-limited paths populate them.
        """
        remaining_str = response.headers.get(_HEADER_REMAINING)
        reset_str = response.headers.get(_HEADER_RESET)
        if remaining_str is None or reset_str is None:
            return

        try:
            remaining = int(remaining_str)
            reset_epoch_ms = int(reset_str)
        except (ValueError, TypeError):
            self.logger.warning(
                "Invalid rate-limit headers: remaining=%r reset=%r",
                remaining_str,
                reset_str,
            )
            return

        # Stale-window guard: if the response's reset deadline is already in
        # the past, this response describes a window that has rolled. Acting
        # on its ``remaining`` (drain or gate-engage) would clamp the local
        # limiter based on outdated state — and under the never-sync-up rule
        # that artificial clamp can persist for the rest of the process.
        # Drop the entire observation rather than just suppressing one path.
        now_ms = int(time.time() * 1000)
        if reset_epoch_ms <= now_ms:
            return

        # Skip the lock entirely when no update is possible — sync-down is
        # only triggered by ``remaining < estimate`` and the reset gate only
        # by ``remaining == 0``. Lock-free fast path for the common case
        # where the server has at least as much budget as we think we do.
        if remaining > 0 and remaining >= self._estimated_remaining:
            return

        async with self._lock:
            # Sync down only — out-of-order responses with a higher
            # ``remaining`` value must not overwrite a fresher (lower) estimate.
            #
            # When remaining=0, the reset gate alone is enough: it blocks
            # until the server's window rolls. We deliberately do *not*
            # drain pyrate's bucket here, because doing so would deplete
            # pyrate of its tokens (e.g., a single response with
            # remaining=0 would consume the rest of pyrate's burst budget),
            # forcing the next request to wait pyrate's full window after
            # the gate opens — even though Katana's window has already
            # rolled. Sub-zero pyrate state and the gate are redundant; the
            # gate is the override.
            if 0 < remaining < self._estimated_remaining:
                drain = self._estimated_remaining - remaining
                # Best-effort: pyrate may have already drifted, so non-blocking
                # drain.
                await self._limiter.try_acquire_async(
                    name=_RATE_LIMIT_BUCKET_NAME, weight=drain, blocking=False
                )
                self._estimated_remaining = remaining
                self.logger.info(
                    "Rate limit synced down: drained %d tokens, remote remaining=%d",
                    drain,
                    remaining,
                )

            if remaining == 0:
                self._engage_reset_gate(reset_epoch_ms)

    def _engage_reset_gate(self, reset_epoch_ms: int) -> None:
        """Close the reset gate until ``reset_epoch_ms`` arrives.

        Called under ``self._lock`` from ``_observe_response``.

        Two guards on the deadline:

        - **Stale earlier resets**: if there's already an active gate with a
          *later* deadline, ignore this engage. Otherwise an earlier-window
          response could shorten the gate and let requests through before
          the server's true reset.
        - **Fresh later resets**: cancel the existing timer and reschedule
          for the new (later) deadline.

        Past-due resets are filtered by ``_observe_response`` before reaching
        this method (stale-window guard); the redundant ``wait_ms <= 0``
        check below is defensive in case future callers bypass that filter.

        ``_estimated_remaining = 0`` is pinned only after the gate actually
        engages, so a stale ``remaining=0`` response can't permanently stick
        the estimate at 0 (which under the never-sync-up rule would silently
        disable sync-down for the rest of the client's lifetime).
        """
        now_ms = int(time.time() * 1000)
        wait_ms = reset_epoch_ms - now_ms
        if wait_ms <= 0:
            return  # Reset already passed; nothing to gate against.

        # If a gate is already engaged for a *later* deadline, keep it.
        if (
            self._reset_until_epoch_ms is not None
            and reset_epoch_ms <= self._reset_until_epoch_ms
        ):
            return

        wait_s = wait_ms / 1000.0
        self._reset_until_epoch_ms = reset_epoch_ms
        self._estimated_remaining = 0

        if self._reset_gate.is_set():
            self._reset_gate.clear()
            self.logger.info(
                "Rate limit reset gate engaged for %.2fs (server reports remaining=0)",
                wait_s,
            )

        # Cancel any prior pending release so the (later) deadline replaces it.
        if self._reset_handle is not None and not self._reset_handle.cancelled():
            self._reset_handle.cancel()

        loop = asyncio.get_running_loop()
        self._reset_handle = loop.call_later(
            wait_s, self._schedule_release, reset_epoch_ms
        )

    def _schedule_release(self, deadline_epoch_ms: int) -> None:
        """Sync callback fired by ``loop.call_later`` at the deadline.

        Spawns the async release helper so we can take ``self._lock`` for
        the state mutation. Passes the deadline through so the helper can
        verify this firing wasn't superseded by a later ``_engage_reset_gate``
        call (in which case ``_reset_handle`` was replaced and we'd race
        with whichever timer fires last). Stores the task reference so
        Python doesn't garbage-collect the coroutine before it runs (asyncio
        only holds weak refs to background tasks).
        """
        task = asyncio.create_task(self._release_reset_gate(deadline_epoch_ms))
        self._release_task = task
        task.add_done_callback(self._clear_release_task)

    def _clear_release_task(self, task: asyncio.Task[None]) -> None:
        """Drop our strong reference once the release helper completes — but only if it's still the current one.

        Without the identity check, a stale callback can clear a fresher
        in-flight task: timer A fires, spawns task A, and stores it as
        ``self._release_task``; while task A is waiting on ``self._lock``,
        a later ``_engage_reset_gate`` schedules timer B, which fires and
        overwrites ``self._release_task = task_B``. When task A completes
        (its deadline-mismatch no-op path), its ``add_done_callback``
        would naively set ``self._release_task = None``, losing the
        reference to the still-running task B and causing ``aclose()`` to
        skip cancelling it.
        """
        if self._release_task is task:
            self._release_task = None

    async def _release_reset_gate(self, deadline_epoch_ms: int) -> None:
        """Reopen the gate and reset estimate, atomically.

        Ignores stale firings: if a subsequent ``_engage_reset_gate`` replaced
        the deadline, our ``deadline_epoch_ms`` no longer matches
        ``self._reset_until_epoch_ms`` and we leave the gate alone — the
        replacement timer will fire later and own the release.
        """
        async with self._lock:
            if self._reset_until_epoch_ms != deadline_epoch_ms:
                # A fresher engage replaced this deadline; let its timer run.
                return
            self._reset_until_epoch_ms = None
            self._reset_handle = None
            self._estimated_remaining = self._rpm
            self._reset_gate.set()
            self.logger.info("Rate limit reset gate released")

    async def aclose(self) -> None:
        """Cancel the pending reset timer and any in-flight release, then close the wrapped transport.

        Two cancellation paths must run before delegating ``aclose`` down
        the chain:

        1. ``_reset_handle`` — the ``loop.call_later`` callback. If it
           fires after the loop is cleaned up, we get scheduling errors.
        2. ``_release_task`` — the async ``_release_reset_gate`` task
           spawned when the timer fired. If the timer fired *just before*
           shutdown, the task may still be running (waiting on
           ``self._lock``); without explicit cancel + await, asyncio
           emits "Task was destroyed but it is pending" and the task can
           race with the wrapped transport's own shutdown.
        """
        if self._reset_handle is not None and not self._reset_handle.cancelled():
            self._reset_handle.cancel()
        self._reset_handle = None

        if self._release_task is not None and not self._release_task.done():
            self._release_task.cancel()
            # Suppress the cancellation so it doesn't propagate; we just
            # want the task off the loop before we close the wrapped
            # transport.
            with contextlib.suppress(asyncio.CancelledError):
                await self._release_task
        self._release_task = None

        await self._wrapped_transport.aclose()


def ResilientAsyncTransport(
    max_retries: int = 5,
    max_pages: int = 100,
    logger: Logger | None = None,
    *,
    requests_per_minute: int | None = 60,
    **kwargs: Any,
) -> RetryTransport:
    """
    Factory function that creates a chained transport with error logging,
    pagination, rate limiting, and retry capabilities.

    This function chains multiple transport layers (innermost → outermost):
    1. AsyncHTTPTransport (base HTTP transport)
    2. RateLimitTransport (proactive 60-req/min throttle, header-aware)
    3. ErrorLoggingTransport (logs detailed 4xx errors)
    4. PaginationTransport (auto-collects paginated responses)
    5. RetryTransport (handles retries with Retry-After header support)

    The rate limiter is innermost (above the base) because Katana counts
    *every* HTTP request — retries from the outer ``RetryTransport`` and
    individual paginated pages from ``PaginationTransport`` all consume
    server-side budget. Placing the limiter higher up would under-count.

    Args:
        max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
        max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
        requests_per_minute: Steady-state request budget for the rate-limit
            transport. Defaults to 60 (Katana's documented default). Pass ``None``
            to omit the rate-limit layer entirely (e.g. when the caller is
            responsible for throttling, or for tests that need raw throughput).
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
    resolved_logger: Logger = (
        logger if logger is not None else logging.getLogger(__name__)
    )

    # Build the transport chain from inside out:
    # 1. Base AsyncHTTPTransport
    inner_transport: AsyncBaseTransport = AsyncHTTPTransport(**kwargs)

    # 2. Wrap with rate limiting (innermost wrapping layer — every actual
    #    HTTP request, including retries and per-page paginated fetches,
    #    consumes one token. ``None`` skips this layer entirely.)
    if requests_per_minute is not None:
        inner_transport = RateLimitTransport(
            wrapped_transport=inner_transport,
            requests_per_minute=requests_per_minute,
            logger=resolved_logger,
        )

    # 3. Wrap with error logging
    error_logging_transport = ErrorLoggingTransport(
        wrapped_transport=inner_transport,
        logger=resolved_logger,
    )

    # 4. Wrap with pagination
    pagination_transport = PaginationTransport(
        wrapped_transport=error_logging_transport,
        max_pages=max_pages,
        logger=resolved_logger,
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
    - Auto-pagination ON by default for GET requests (collects all pages automatically)
    - Uses 250 items per page (Katana's max) for efficient pagination
    - Rich logging and observability
    - Minimal configuration - just works out of the box

    Auto-pagination behavior:
    - ON by default for GET requests with NO page parameter
    - Uses 250 items per page when no limit specified by caller
    - If caller specifies a limit, that limit is used per page
    - ANY explicit `page` parameter disables auto-pagination (e.g., `page=1`)
    - Disabled per-request via extensions: `extensions={"auto_pagination": False}`
    - Control max pages via `max_pages` constructor parameter
    - Limit total items via extensions: `extensions={"max_items": 200}`

    Usage:
        async with KatanaClient() as client:
            from katana_public_api_client.api.product import get_all_products

            # Auto-pagination is ON - all pages collected automatically
            # Uses 250 items per page for efficiency
            response = await get_all_products.asyncio_detailed(
                client=client,  # Pass client directly - no .client needed!
            )

            # Use a custom limit per page (100 instead of 250)
            response = await get_all_products.asyncio_detailed(
                client=client,
                limit=100,   # Use 100 per page
            )

            # Get a specific page only (ANY page param disables auto-pagination)
            response = await get_all_products.asyncio_detailed(
                client=client,
                page=2,      # Get page 2 only
                limit=50
            )

            # Limit total items collected (via httpx client)
            httpx_client = client.get_async_httpx_client()
            response = await httpx_client.get(
                "/products",
                extensions={"max_items": 200}   # Stop after 200 items
            )

            # Control max pages globally
            client_limited = KatanaClient(max_pages=5)  # Limit to 5 pages max
    """

    @staticmethod
    def _read_from_netrc(base_url: str) -> str | None:
        """
        Read API key from ~/.netrc file.

        Args:
            base_url: The base URL to extract the hostname from.

        Returns:
            The API key (password field) from netrc, or None if not found.

        Note:
            The password field in netrc is used to store the API token since
            Katana API uses bearer token authentication, not HTTP Basic Auth.
        """
        try:
            # Extract hostname from base_url - handle both full URLs and bare hostnames
            parsed = urlparse(base_url)
            host: str | None = None

            if parsed.hostname:
                # URL with scheme (e.g., "https://api.katanamrp.com/v1")
                host = parsed.hostname
            else:
                # Try parsing as URL without scheme (e.g., "api.katanamrp.com/v1")
                parsed_with_scheme = urlparse(f"https://{base_url}")
                if parsed_with_scheme.hostname:
                    host = parsed_with_scheme.hostname
                else:
                    # Final fallback: treat as bare hostname (e.g., "api.example.com")
                    # Extract just the hostname part before any path
                    host = base_url.split("/")[0] if base_url else None

            # If we couldn't extract a valid hostname, return None
            if not host:
                return None

            netrc_path = Path.home() / ".netrc"
            if not netrc_path.exists():
                return None

            # Warn if .netrc is readable by group or others (POSIX only)
            if os.name != "nt":
                mode = netrc_path.stat().st_mode
                if mode & 0o077:
                    import warnings

                    warnings.warn(
                        f"~/.netrc has insecure permissions ({oct(mode & 0o777)}). "
                        "This may expose your API key. Run: chmod 600 ~/.netrc",
                        stacklevel=2,
                    )

            auth = netrc.netrc(str(netrc_path))
            authenticators = auth.authenticators(host)

            if authenticators:
                # Return password field (which contains our API token)
                # netrc returns (login, account, password)
                _login, _account, password = authenticators
                return password
        except (FileNotFoundError, netrc.NetrcParseError, OSError):
            # Silently ignore netrc errors - it's an optional source
            pass

        return None

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 5,
        max_pages: int = 100,
        logger: Logger | None = None,
        *,
        requests_per_minute: int | None = 60,
        **httpx_kwargs: Any,
    ):
        """
        Initialize the Katana API client with automatic resilience features.

        Args:
            api_key: Katana API key. If None, will try to load from KATANA_API_KEY env var,
                .env file, or ~/.netrc file (in that order).
            base_url: Base URL for the Katana API. Defaults to https://api.katanamrp.com/v1
            timeout: Request timeout in seconds. Defaults to 30.0.
            max_retries: Maximum number of retry attempts for failed requests. Defaults to 5.
            max_pages: Maximum number of pages to collect during auto-pagination. Defaults to 100.
            requests_per_minute: Steady-state request budget for the proactive
                rate limiter. Defaults to 60 (Katana's documented limit). Set to
                ``None`` to disable the rate limiter entirely (e.g. when callers
                want to manage throttling themselves, or for tests that need raw
                throughput). When the limiter is active, every actual HTTP
                request — including retries and per-page paginated fetches —
                consumes one token, and the transport adapts to the server's
                ``X-Ratelimit-Remaining`` / ``X-Ratelimit-Reset`` headers.
            logger: Any object whose debug/info/warning/error methods accept
                (msg, *args, **kwargs) — the standard logging.Logger call convention
                (e.g. logging.Logger, structlog.BoundLogger). If None, creates a
                default stdlib logger.
            **httpx_kwargs: Additional arguments passed to the base AsyncHTTPTransport.
                Common parameters include:
                - http2 (bool): Enable HTTP/2 support
                - limits (httpx.Limits): Connection pool limits
                - verify (bool | str | ssl.SSLContext): SSL certificate verification
                - cert (str | tuple): Client-side certificates
                - trust_env (bool): Trust environment variables for proxy configuration
                - event_hooks (dict): Custom event hooks (will be merged with built-in hooks)

        Raises:
            ValueError: If no API key is provided via api_key param, KATANA_API_KEY env var,
                .env file, or ~/.netrc file.

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

        # Determine base_url early so we can use it for netrc lookup
        base_url = (
            base_url or os.getenv("KATANA_BASE_URL") or "https://api.katanamrp.com/v1"
        )

        # Setup credentials with priority: param > env (including .env) > netrc
        api_key = (
            api_key or os.getenv("KATANA_API_KEY") or self._read_from_netrc(base_url)
        )

        if not api_key:
            raise ValueError(
                "API key required via: api_key param, KATANA_API_KEY env var, "
                ".env file, or ~/.netrc"
            )

        self.logger: Logger = logger or logging.getLogger(__name__)
        self.max_pages = max_pages

        # Warn if SSL verification is disabled — risk of MITM attacks
        if httpx_kwargs.get("verify") is False:
            self.logger.warning(
                "SSL certificate verification is disabled (verify=False). "
                "This exposes the connection to MITM attacks. "
                "Only use this for local development."
            )

        # Domain class instances (lazy-loaded)
        self._products: Products | None = None
        self._materials: Materials | None = None
        self._variants: Variants | None = None
        self._services: Services | None = None
        self._api_namespace: ApiNamespace | None = None

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
                requests_per_minute=requests_per_minute,
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

    # Domain properties for ergonomic access
    @property
    def products(self) -> Products:
        """Access product catalog operations.

        Returns:
            Products instance for product CRUD and search operations.

        Example:
            >>> async with KatanaClient() as client:
            ...     # Product CRUD
            ...     products = await client.products.list(is_sellable=True)
            ...     product = await client.products.get(123)
            ...     results = await client.products.search("widget")
        """
        if self._products is None:
            self._products = Products(self)
        return self._products

    @property
    def materials(self) -> Materials:
        """Access material catalog operations.

        Returns:
            Materials instance for material CRUD operations.

        Example:
            >>> async with KatanaClient() as client:
            ...     materials = await client.materials.list()
            ...     material = await client.materials.get(123)
        """
        if self._materials is None:
            self._materials = Materials(self)
        return self._materials

    @property
    def variants(self) -> Variants:
        """Access variant catalog operations.

        Returns:
            Variants instance for variant CRUD operations.

        Example:
            >>> async with KatanaClient() as client:
            ...     variants = await client.variants.list()
            ...     variant = await client.variants.get(123)
        """
        if self._variants is None:
            self._variants = Variants(self)
        return self._variants

    @property
    def services(self) -> Services:
        """Access service catalog operations.

        Returns:
            Services instance for service CRUD operations.

        Example:
            >>> async with KatanaClient() as client:
            ...     services = await client.services.list()
            ...     service = await client.services.get(123)
        """
        if self._services is None:
            self._services = Services(self)
        return self._services

    @property
    def api(self) -> ApiNamespace:
        """Thin CRUD wrappers for all API resources.  Returns raw attrs models.

        Example:
            >>> async with KatanaClient() as client:
            ...     products = await client.api.products.list(is_sellable=True)
            ...     product = await client.api.products.get(123)
            ...     await client.api.products.delete(123)
        """
        if self._api_namespace is None:
            self._api_namespace = ApiNamespace(self)
        return self._api_namespace

    # Event hooks for observability
    async def _capture_pagination_metadata(self, response: httpx.Response) -> None:
        """Capture and store pagination metadata from response headers."""
        if response.status_code == HTTPStatus.OK:
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
            f"{_sanitize_url(str(response.request.url))} ({duration:.2f}s)"
        )
