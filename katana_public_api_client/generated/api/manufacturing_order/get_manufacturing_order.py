from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_manufacturing_order_response_401 import (
    GetManufacturingOrderResponse401,
)
from ...models.get_manufacturing_order_response_429 import (
    GetManufacturingOrderResponse429,
)
from ...models.get_manufacturing_order_response_500 import (
    GetManufacturingOrderResponse500,
)
from ...models.manufacturing_order import ManufacturingOrder
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/manufacturing_orders/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrder.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetManufacturingOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetManufacturingOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetManufacturingOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
]:
    """Retrieve a manufacturing order

     Retrieves the details of an existing manufacturing order based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderResponse401, GetManufacturingOrderResponse429, GetManufacturingOrderResponse500, ManufacturingOrder]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    """Retrieve a manufacturing order

     Retrieves the details of an existing manufacturing order based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderResponse401, GetManufacturingOrderResponse429, GetManufacturingOrderResponse500, ManufacturingOrder]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
]:
    """Retrieve a manufacturing order

     Retrieves the details of an existing manufacturing order based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderResponse401, GetManufacturingOrderResponse429, GetManufacturingOrderResponse500, ManufacturingOrder]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetManufacturingOrderResponse401
    | GetManufacturingOrderResponse429
    | GetManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    """Retrieve a manufacturing order

     Retrieves the details of an existing manufacturing order based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderResponse401, GetManufacturingOrderResponse429, GetManufacturingOrderResponse500, ManufacturingOrder]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
