from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.inventory_safety_stock_level import InventorySafetyStockLevel


def _get_kwargs(
    *,
    body: InventorySafetyStockLevel,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/inventory_safety_stock_levels",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel | None:
    if response.status_code == 200:
        response_200 = InventorySafetyStockLevel.from_dict(response.json())

        return response_200

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
) -> Response[DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InventorySafetyStockLevel,
) -> Response[DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel]:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel): Safety stock level configuration to maintain minimum
            inventory buffers and prevent stockouts Example: {'location_id': 1, 'variant_id': 3001,
            'value': 25.0}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, InventorySafetyStockLevel]]
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
    body: InventorySafetyStockLevel,
) -> DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel | None:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel): Safety stock level configuration to maintain minimum
            inventory buffers and prevent stockouts Example: {'location_id': 1, 'variant_id': 3001,
            'value': 25.0}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, InventorySafetyStockLevel]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InventorySafetyStockLevel,
) -> Response[DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel]:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel): Safety stock level configuration to maintain minimum
            inventory buffers and prevent stockouts Example: {'location_id': 1, 'variant_id': 3001,
            'value': 25.0}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, InventorySafetyStockLevel]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: InventorySafetyStockLevel,
) -> DetailedErrorResponse | ErrorResponse | InventorySafetyStockLevel | None:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel): Safety stock level configuration to maintain minimum
            inventory buffers and prevent stockouts Example: {'location_id': 1, 'variant_id': 3001,
            'value': 25.0}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, InventorySafetyStockLevel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
