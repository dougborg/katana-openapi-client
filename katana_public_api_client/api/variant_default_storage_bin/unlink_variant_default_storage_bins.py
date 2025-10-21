from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.unlink_variant_bin_location_request import (
    UnlinkVariantBinLocationRequest,
)


def _get_kwargs(
    *,
    body: list["UnlinkVariantBinLocationRequest"],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/unlink_variant_bin_locations",
    }

    _kwargs["json"] = []
    for componentsschemas_unlink_variant_bin_location_list_request_item_data in body:
        componentsschemas_unlink_variant_bin_location_list_request_item = componentsschemas_unlink_variant_bin_location_list_request_item_data.to_dict()
        _kwargs["json"].append(
            componentsschemas_unlink_variant_bin_location_list_request_item
        )

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = DetailedErrorResponse.from_dict(response.json())

        return response_422

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']): Batch request to remove variant storage
            bin assignments for multiple location-variant combinations Example: [{'location_id': 1,
            'variant_id': 3001}, {'location_id': 1, 'variant_id': 3002}].

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, DetailedErrorResponse, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']): Batch request to remove variant storage
            bin assignments for multiple location-variant combinations Example: [{'location_id': 1,
            'variant_id': 3001}, {'location_id': 1, 'variant_id': 3002}].

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, DetailedErrorResponse, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> Response[Any | DetailedErrorResponse | ErrorResponse]:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']): Batch request to remove variant storage
            bin assignments for multiple location-variant combinations Example: [{'location_id': 1,
            'variant_id': 3001}, {'location_id': 1, 'variant_id': 3002}].

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Any, DetailedErrorResponse, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: list["UnlinkVariantBinLocationRequest"],
) -> Any | DetailedErrorResponse | ErrorResponse | None:
    """Unlink variant default storage bins

     Bulk operation for unlinking variants from the default storage bins available in a specific
    location.
      The endpoint accepts up to 500 variant bin location objects.

    Args:
        body (list['UnlinkVariantBinLocationRequest']): Batch request to remove variant storage
            bin assignments for multiple location-variant combinations Example: [{'location_id': 1,
            'variant_id': 3001}, {'location_id': 1, 'variant_id': 3002}].

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Any, DetailedErrorResponse, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
