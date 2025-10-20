"""Utility functions for working with Katana API responses.

This module provides convenient helpers for unwrapping API responses,
handling errors, and extracting data in a type-safe manner.
"""

from collections.abc import Callable
from http import HTTPStatus
from typing import Any, TypeVar, overload

from .client_types import Response, Unset
from .models.detailed_error_response import DetailedErrorResponse
from .models.error_response import ErrorResponse

T = TypeVar("T")
DataT = TypeVar("DataT")


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_response: ErrorResponse | DetailedErrorResponse | None = None,
    ):
        """Initialize API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_response: The error response object from the API
        """
        super().__init__(message)
        self.status_code = status_code
        self.error_response = error_response


class AuthenticationError(APIError):
    """Raised when authentication fails (401)."""

    pass


class ValidationError(APIError):
    """Raised when request validation fails (422)."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_response: DetailedErrorResponse | None = None,
    ):
        """Initialize validation error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code (should be 422)
            error_response: The detailed error response with validation details
        """
        super().__init__(message, status_code, error_response)
        self.validation_errors = (
            error_response.details if error_response and error_response.details else []
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""

    pass


class ServerError(APIError):
    """Raised when server error occurs (5xx)."""

    pass


@overload
def unwrap(
    response: Response[T],
    *,
    raise_on_error: bool = True,
) -> T: ...


@overload
def unwrap(
    response: Response[T],
    *,
    raise_on_error: bool = False,
) -> T | None: ...


def unwrap(
    response: Response[T],
    *,
    raise_on_error: bool = True,
) -> T | None:
    """Unwrap a Response object and return the parsed data or raise an error.

    This is the main utility function for handling API responses. It automatically
    raises appropriate exceptions for error responses and returns the parsed data
    for successful responses.

    Args:
        response: The Response object from an API call
        raise_on_error: If True, raise exceptions on error status codes.
                        If False, return None on errors.

    Returns:
        The parsed response data

    Raises:
        AuthenticationError: When status is 401
        ValidationError: When status is 422
        RateLimitError: When status is 429
        ServerError: When status is 5xx
        APIError: For other error status codes

    Example:
        ```python
        from katana_public_api_client import KatanaClient
        from katana_public_api_client.api.product import get_all_products
        from katana_public_api_client.utils import unwrap

        async with KatanaClient() as client:
            response = await get_all_products.asyncio_detailed(client=client)
            product_list = unwrap(
                response
            )  # Raises on error, returns parsed data
            products = product_list.data  # List of Product objects
        ```
    """
    if response.parsed is None:
        if raise_on_error:
            raise APIError(
                f"No parsed response data for status {response.status_code}",
                response.status_code,
            )
        return None

    # Check if it's an error response
    if isinstance(response.parsed, ErrorResponse | DetailedErrorResponse):
        if not raise_on_error:
            return None

        error_name = (
            response.parsed.name
            if not isinstance(response.parsed.name, Unset)
            else "Unknown"
        )
        error_message = (
            response.parsed.message
            if not isinstance(response.parsed.message, Unset)
            else "No error message provided"
        )

        # Handle nested error format
        if hasattr(response.parsed, "additional_properties"):
            nested = response.parsed.additional_properties
            if isinstance(nested, dict) and "error" in nested:
                nested_error = nested["error"]
                if isinstance(nested_error, dict):
                    error_name = nested_error.get("name", error_name)
                    error_message = nested_error.get("message", error_message)

        message = f"{error_name}: {error_message}"

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise AuthenticationError(message, response.status_code, response.parsed)
        elif response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
            # ValidationError expects DetailedErrorResponse, but response.parsed could be ErrorResponse
            detailed_error = (
                response.parsed
                if isinstance(response.parsed, DetailedErrorResponse)
                else None
            )
            raise ValidationError(
                message,
                response.status_code,
                detailed_error,
            )
        elif response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError(message, response.status_code, response.parsed)
        elif 500 <= response.status_code < 600:
            raise ServerError(message, response.status_code, response.parsed)
        else:
            raise APIError(message, response.status_code, response.parsed)

    return response.parsed


@overload
def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = True,
    default: None = None,
) -> list[Any]: ...


@overload
def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = False,
    default: None = None,
) -> list[Any] | None: ...


@overload
def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = False,
    default: list[DataT],
) -> list[Any]: ...


def unwrap_data(
    response: Response[T],
    *,
    raise_on_error: bool = True,
    default: list[DataT] | None = None,
) -> list[Any] | None:
    """Unwrap a Response and extract the data list from list responses.

    This is a convenience function that unwraps the response and extracts
    the `.data` field from list response objects (like ProductListResponse,
    WebhookListResponse, etc.).

    Args:
        response: The Response object from an API call
        raise_on_error: If True, raise exceptions on error status codes.
                        If False, return default on errors.
        default: Default value to return if data is not available

    Returns:
        List of data objects, or default if not available

    Raises:
        Same exceptions as unwrap()

    Example:
        ```python
        from katana_public_api_client import KatanaClient
        from katana_public_api_client.api.product import get_all_products
        from katana_public_api_client.utils import unwrap_data

        async with KatanaClient() as client:
            response = await get_all_products.asyncio_detailed(client=client)
            products = unwrap_data(response)  # Directly get list of Products
            for product in products:
                print(product.name)
        ```
    """
    try:
        parsed = unwrap(response, raise_on_error=raise_on_error)
    except APIError:
        if raise_on_error:
            raise
        return default

    if parsed is None:
        return default

    # Extract data field if it exists
    data = getattr(parsed, "data", None)
    if isinstance(data, Unset):
        return default if default is not None else []
    if data is not None:
        return data

    # If there's no data field and no default, wrap the object in a list
    if default is not None:
        return default

    # If it's not a list response, return it as a single-item list
    return [parsed]


def is_success(response: Response[Any]) -> bool:
    """Check if a response was successful (2xx status code).

    Args:
        response: The Response object to check

    Returns:
        True if status code is 2xx, False otherwise

    Example:
        ```python
        response = await some_api_call.asyncio_detailed(client=client)
        if is_success(response):
            data = unwrap_data(response)
        else:
            print(f"Error: {response.status_code}")
        ```
    """
    return 200 <= response.status_code < 300


def is_error(response: Response[Any]) -> bool:
    """Check if a response was an error (4xx or 5xx status code).

    Args:
        response: The Response object to check

    Returns:
        True if status code is 4xx or 5xx, False otherwise
    """
    return response.status_code >= 400


def get_error_message(response: Response[T]) -> str | None:
    """Extract error message from an error response.

    Args:
        response: The Response object (typically an error response)

    Returns:
        Error message string, or None if no error message found

    Example:
        ```python
        response = await some_api_call.asyncio_detailed(client=client)
        if is_error(response):
            error_msg = get_error_message(response)
            print(f"API Error: {error_msg}")
        ```
    """
    if response.parsed is None:
        return None

    if not isinstance(response.parsed, ErrorResponse | DetailedErrorResponse):
        return None

    error_message = (
        response.parsed.message
        if not isinstance(response.parsed.message, Unset)
        else None
    )

    # Check nested error format
    if hasattr(response.parsed, "additional_properties"):
        nested = response.parsed.additional_properties
        if isinstance(nested, dict) and "error" in nested:
            nested_error = nested["error"]
            if isinstance(nested_error, dict):
                error_message = nested_error.get("message", error_message)

    return error_message


def handle_response(
    response: Response[T],
    *,
    on_success: Callable[[T], Any] | None = None,
    on_error: Callable[[APIError], Any] | None = None,
    raise_on_error: bool = False,
) -> Any:
    """Handle a response with custom success and error handlers.

    This function provides a convenient way to handle both success and error
    cases with custom callbacks.

    Args:
        response: The Response object from an API call
        on_success: Callback function to call with parsed data on success
        on_error: Callback function to call with APIError on error
        raise_on_error: If True, raise the error even if on_error is provided

    Returns:
        Result of on_success callback, result of on_error callback, or None

    Example:
        ```python
        def handle_products(product_list):
            print(f"Got {len(product_list.data)} products")
            return product_list.data


        def handle_error(error):
            print(f"Error: {error}")
            return []


        response = await get_all_products.asyncio_detailed(client=client)
        products = handle_response(
            response, on_success=handle_products, on_error=handle_error
        )
        ```
    """
    try:
        data = unwrap(response, raise_on_error=True)
        if on_success:
            return on_success(data)
        return data
    except APIError as e:
        if raise_on_error:
            raise
        if on_error:
            return on_error(e)
        return None


__all__ = [
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_data",
]
