"""Utility functions for working with Katana API responses.

This module provides convenient helpers for unwrapping API responses,
handling errors, extracting data, and formatting display values.
"""

import json
from collections.abc import Callable
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Literal, NoReturn, overload

from .client_types import Response, Unset
from .domain.converters import unwrap_unset
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

if TYPE_CHECKING:
    from .models.variant_response import VariantResponse


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
        self.validation_errors = unwrap_unset(
            getattr(error_response, "details", None), []
        )

    def __str__(self) -> str:
        """Format validation error with Ajv-keyword-specific details.

        Each detail's typed subtype is dispatched into a keyword-specific
        renderer that consults ``info.*`` for keyword metadata (limit,
        pattern, allowed values, etc.). Unknown keywords route to
        ``GenericValidationError`` and render through a fallback that
        surfaces ``path``/``code``/``message`` plus any ``info`` captured
        in ``additional_properties``.
        """
        msg = super().__str__()

        if self.validation_errors:
            error_details = []
            for detail in self.validation_errors:
                error_details.append(_format_ajv_detail(detail))
            if error_details:
                msg += "\n" + "\n".join(error_details)

        return msg


def _format_ajv_detail(detail: Any) -> str:
    """Render an Ajv ``ValidationErrorDetail`` as a single human-readable line.

    Dispatches by typed subtype (one branch per Ajv keyword), with a fallback
    for ``GenericValidationError`` and any subtype whose wire payload didn't
    match its declared schema (e.g. a future Ajv keyword we haven't typed yet,
    or a typed subtype where deserialization fell back to Generic).
    """
    field = detail.path.lstrip("/") if hasattr(detail, "path") else "?"

    # ── String / format keywords ────────────────────────────────────────────
    if isinstance(detail, MaxLengthValidationError):
        return f"  Field '{field}' must not exceed {detail.info.limit} characters"
    if isinstance(detail, MinLengthValidationError):
        return f"  Field '{field}' must be at least {detail.info.limit} characters"
    if isinstance(detail, FormatValidationError):
        return f"  Field '{field}' must match format: {detail.info.format_}"
    if isinstance(detail, PatternValidationError):
        return f"  Field '{field}' must match pattern: {detail.info.pattern}"

    # ── Numeric keywords ────────────────────────────────────────────────────
    if isinstance(detail, MinimumValidationError):
        return f"  Field '{field}' must be >= {detail.info.limit}"
    if isinstance(detail, MaximumValidationError):
        return f"  Field '{field}' must be <= {detail.info.limit}"
    if isinstance(detail, ExclusiveMinimumValidationError):
        return f"  Field '{field}' must be > {detail.info.limit}"
    if isinstance(detail, ExclusiveMaximumValidationError):
        return f"  Field '{field}' must be < {detail.info.limit}"
    if isinstance(detail, MultipleOfValidationError):
        return f"  Field '{field}' must be a multiple of {detail.info.multiple_of}"

    # ── Array keywords ──────────────────────────────────────────────────────
    if isinstance(detail, MinItemsValidationError):
        return f"  Field '{field}' must have at least {detail.info.limit} items"
    if isinstance(detail, MaxItemsValidationError):
        return f"  Field '{field}' must have at most {detail.info.limit} items"
    if isinstance(detail, UniqueItemsValidationError):
        return (
            f"  Field '{field}' contains duplicate items "
            f"at indices {detail.info.i} and {detail.info.j}"
        )

    # ── Object keywords ─────────────────────────────────────────────────────
    if isinstance(detail, RequiredValidationError):
        return f"  Missing required field: '{detail.info.missing_property}'"
    if isinstance(detail, AdditionalPropertiesValidationError):
        return (
            f"  Field '{field}' has unexpected property: "
            f"'{detail.info.additional_property}'"
        )
    if isinstance(detail, DependenciesValidationError):
        return (
            f"  Field '{field}' has property '{detail.info.property_}' "
            f"but is missing dependent property '{detail.info.missing_property}'"
        )

    # ── Type / composition keywords ─────────────────────────────────────────
    if isinstance(detail, TypeValidationError):
        return f"  Field '{field}' must be of type: {detail.info.type_}"
    if isinstance(detail, EnumValidationError):
        return f"  Field '{field}' must be one of: {detail.info.allowed_values}"
    if isinstance(detail, ConstValidationError):
        return f"  Field '{field}' must equal: {detail.info.allowed_value!r}"
    if isinstance(detail, OneOfValidationError):
        passing = detail.info.passing_schemas
        if passing is None:
            return f"  Field '{field}' did not match any allowed schema"
        return (
            f"  Field '{field}' matched multiple allowed schemas "
            f"(indices {passing}); must match exactly one"
        )

    # ── Fallback: GenericValidationError or any future keyword ─────────────
    detail_message = unwrap_unset(getattr(detail, "message", None), None)
    detail_code = unwrap_unset(getattr(detail, "code", None), None)
    extra = getattr(detail, "additional_properties", {}) or {}
    info = extra.get("info") if isinstance(extra, dict) else None
    prefix = f"({detail_code}) " if detail_code else ""
    suffix = f" — info: {info}" if info else ""
    if detail_message:
        return f"  Field '{field}': {prefix}{detail_message}{suffix}"
    return f"  Field '{field}': {prefix}<no message>{suffix}"


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""

    pass


class ServerError(APIError):
    """Raised when server error occurs (5xx)."""

    pass


@overload
def unwrap[T](
    response: Response[T],
    *,
    raise_on_error: Literal[True] = True,
) -> T: ...


@overload
def unwrap[T](
    response: Response[T],
    *,
    raise_on_error: Literal[False],
) -> T | None: ...


def unwrap[T](
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
        if not raise_on_error:
            return None
        name, message, parsed_error = _try_parse_error_body(response.content)
        _raise_for_status(response.status_code, name, message, parsed_error)

    # Check if it's an error response — assign to local for type narrowing
    parsed = response.parsed
    if isinstance(parsed, ErrorResponse | DetailedErrorResponse):
        if not raise_on_error:
            return None
        name, message, parsed_error = _extract_error_fields(parsed)
        _raise_for_status(response.status_code, name, message, parsed_error)

    return response.parsed


def _try_parse_error_body(
    content: bytes,
) -> tuple[str, str, ErrorResponse | DetailedErrorResponse | None]:
    """Best-effort parse of an unrecognized response body.

    Used when ``response.parsed`` is None because the OpenAPI spec didn't
    document the status code — the body bytes are still available on the
    Response object, and they're usually a Katana ``ErrorResponse``-shaped
    payload. Returns ``(name, message, error_response)``: when parsing
    succeeds the typed model is included for callers that inspect it; when
    it doesn't, ``message`` falls back to a truncated body snippet so the
    caller still sees something actionable.
    """
    if not content:
        return ("UnexpectedResponse", "<empty response body>", None)

    try:
        body = json.loads(content)
    except (json.JSONDecodeError, ValueError, TypeError, UnicodeDecodeError):
        # TypeError covers callers (notably test mocks) that pass non-bytes
        # content; UnicodeDecodeError covers bytes that aren't valid UTF-8/16/32
        # (json.loads detects encoding from BOM but raises during decode for
        # invalid sequences). Fall back to a stringified snippet so we still
        # surface something rather than crashing the unwrap path.
        try:
            snippet = content.decode("utf-8", errors="replace").strip()
        except (AttributeError, UnicodeDecodeError):
            snippet = str(content)[:200]
        return (
            "UnexpectedResponse",
            _truncate(snippet) or "<empty response body>",
            None,
        )

    # Katana wraps errors in {"error": {...}} on some endpoints
    if isinstance(body, dict) and "error" in body and isinstance(body["error"], dict):
        body = body["error"]

    if not isinstance(body, dict):
        return ("UnexpectedResponse", _truncate(json.dumps(body)), None)

    name_raw = body.get("name")
    message_raw = body.get("message")

    # Body parsed as a dict but didn't carry ErrorResponse fields — fall back
    # to surfacing the JSON snippet so the caller can see what Katana sent
    # instead of an opaque "<no error message>" placeholder.
    if name_raw is None and message_raw is None:
        if not body:
            return ("UnexpectedResponse", "<empty response body>", None)
        return ("UnexpectedResponse", _truncate(json.dumps(body)), None)

    name = str(name_raw) if name_raw is not None else "UnexpectedResponse"
    message = (
        str(message_raw) if message_raw is not None else _truncate(json.dumps(body))
    )

    try:
        if "details" in body:
            parsed_error: ErrorResponse | DetailedErrorResponse | None = (
                DetailedErrorResponse.from_dict(body)
            )
        else:
            parsed_error = ErrorResponse.from_dict(body)
    except Exception:
        parsed_error = None

    return (name, message, parsed_error)


def _truncate(snippet: str, limit: int = 200) -> str:
    """Truncate a snippet at ``limit`` chars with an ellipsis marker."""
    if len(snippet) > limit:
        return snippet[:limit] + "…"
    return snippet


def _extract_error_fields(
    parsed: ErrorResponse | DetailedErrorResponse,
) -> tuple[str, str, ErrorResponse | DetailedErrorResponse]:
    """Pull (name, message, parsed_error) from a parsed Katana error.

    Handles the nested-under-``"error"`` wrapping that some Katana endpoints
    use — when present, name/message come from the inner object and the
    returned parsed_error is also re-parsed from the inner object so callers
    inspecting ``APIError.error_response`` see the actual structured fields
    instead of an outer envelope where everything is UNSET.
    """
    name = parsed.name if not isinstance(parsed.name, Unset) else "Unknown"
    message = (
        parsed.message
        if not isinstance(parsed.message, Unset)
        else "No error message provided"
    )

    nested = parsed.additional_properties
    if isinstance(nested, dict) and "error" in nested:
        nested_error = nested["error"]
        if isinstance(nested_error, dict):
            name = str(nested_error.get("name", name))
            message = str(nested_error.get("message", message))
            # Re-parse the inner object so error_response carries the real
            # name/message/statusCode rather than the UNSET-everything outer
            # envelope. Use DetailedErrorResponse when "details" is present
            # so validation details survive the unwrap.
            if "details" in nested_error:
                parsed = DetailedErrorResponse.from_dict(nested_error)
            else:
                parsed = ErrorResponse.from_dict(nested_error)

    return (name, message, parsed)


def _raise_for_status(
    status_code: int,
    name: str,
    message: str,
    parsed_error: ErrorResponse | DetailedErrorResponse | None,
) -> NoReturn:
    """Raise the right APIError subclass for this status code."""
    full_message = f"{name}: {message}"

    if status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(full_message, status_code, parsed_error)
    if status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
        detailed = (
            parsed_error if isinstance(parsed_error, DetailedErrorResponse) else None
        )
        raise ValidationError(full_message, status_code, detailed)
    if status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise RateLimitError(full_message, status_code, parsed_error)
    if 500 <= status_code < 600:
        raise ServerError(full_message, status_code, parsed_error)
    raise APIError(full_message, status_code, parsed_error)


@overload
def unwrap_data[T](
    response: Response[T],
    *,
    raise_on_error: Literal[True] = True,
    default: None = None,
) -> Any: ...


@overload
def unwrap_data[T](
    response: Response[T],
    *,
    raise_on_error: Literal[False],
    default: None = None,
) -> Any | None: ...


@overload
def unwrap_data[T, DataT](
    response: Response[T],
    *,
    raise_on_error: bool = False,
    default: list[DataT],
) -> Any: ...


def unwrap_data[T, DataT](
    response: Response[T],
    *,
    raise_on_error: bool = True,
    default: list[DataT] | None = None,
) -> Any | None:
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


@overload
def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: Literal[True] = True,
) -> ExpectedT: ...


@overload
def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: Literal[False],
) -> ExpectedT | None: ...


def unwrap_as[T, ExpectedT](
    response: Response[T],
    expected_type: type[ExpectedT],
    *,
    raise_on_error: bool = True,
) -> ExpectedT | None:
    """Unwrap a Response and validate the parsed data is of the expected type.

    This is a convenience function that combines unwrap() with type validation.
    It's useful when you expect a specific model type from an API response.

    Args:
        response: The Response object from an API call
        expected_type: The expected type of the parsed response
        raise_on_error: If True, raise exceptions on error status codes.
            If False, returns None on error instead of raising.

    Returns:
        The parsed response data, typed as ExpectedT (or ExpectedT | None if
        raise_on_error=False)

    Raises:
        Same exceptions as unwrap(), plus:
        TypeError: If the parsed response is not of the expected type

    Example:
        ```python
        from katana_public_api_client import KatanaClient
        from katana_public_api_client.api.sales_order import get_sales_order
        from katana_public_api_client.models import SalesOrder
        from katana_public_api_client.utils import unwrap_as

        async with KatanaClient() as client:
            response = await get_sales_order.asyncio_detailed(
                client=client, id=123
            )
            order = unwrap_as(response, SalesOrder)  # Type-safe SalesOrder
            print(order.order_no)
        ```
    """
    result = unwrap(response, raise_on_error=raise_on_error)
    if result is None:
        if raise_on_error:
            raise TypeError(
                f"Expected {expected_type.__name__}, got None from response"
            )
        return None

    if not isinstance(result, expected_type):
        raise TypeError(
            f"Expected {expected_type.__name__}, got {type(result).__name__}"
        )
    return result


def get_error_message[T](response: Response[T]) -> str | None:
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

    # Assign to local for type narrowing
    parsed = response.parsed
    if not isinstance(parsed, ErrorResponse | DetailedErrorResponse):
        return None

    error_message = parsed.message if not isinstance(parsed.message, Unset) else None

    # Check nested error format
    nested = parsed.additional_properties
    if isinstance(nested, dict) and "error" in nested:
        nested_error = nested["error"]
        if isinstance(nested_error, dict):
            error_message = str(nested_error.get("message", error_message))

    return error_message


def handle_response[T](
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


def get_variant_display_name(variant: "VariantResponse") -> str:
    """Build the full variant display name matching Katana UI format.

    Format: "{Product/Material Name} / {Config Value 1} / {Config Value 2} / ..."

    Example: "Premium 140 / Glossy Black / Large / Type A"

    Takes a `VariantResponse` (the discriminated-union variant schema with
    typed `product_or_material: Material | Product | Unset`). Variants returned
    *without* `?extend=product_or_material` have `product_or_material` UNSET, in
    which case the display name falls back to empty string.

    Args:
        variant: VariantResponse fetched with `?extend=product_or_material`.

    Returns:
        Formatted variant name with config values, or empty string if no name available.

    Example:
        ```python
        from katana_public_api_client import KatanaClient
        from katana_public_api_client.api.variant import get_all_variants
        from katana_public_api_client.models.get_all_variants_extend_item import (
            GetAllVariantsExtendItem,
        )
        from katana_public_api_client.utils import (
            get_variant_display_name,
            unwrap_data,
        )

        async with KatanaClient() as client:
            response = await get_all_variants.asyncio_detailed(
                client=client,
                extend=[GetAllVariantsExtendItem.PRODUCT_OR_MATERIAL],
            )
            for variant in unwrap_data(response):
                print(get_variant_display_name(variant))
                # e.g. "Premium 140 / Glossy Black / Large / Type A"
        ```
    """
    product_or_material = unwrap_unset(variant.product_or_material, None)
    base_name = ""
    if product_or_material is not None:
        base_name = unwrap_unset(product_or_material.name, "") or ""

    if not base_name:
        return ""

    parts: list[str] = [str(base_name)]
    config_attributes = unwrap_unset(variant.config_attributes, [])
    for attr in config_attributes or []:
        config_value = unwrap_unset(attr.config_value, None)
        if config_value:
            parts.append(str(config_value))

    return " / ".join(parts)


__all__ = [
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "get_variant_display_name",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_data",
]
