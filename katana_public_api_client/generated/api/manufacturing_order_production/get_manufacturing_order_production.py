from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_manufacturing_order_production_response_401 import (
    GetManufacturingOrderProductionResponse401,
)
from ...models.get_manufacturing_order_production_response_429 import (
    GetManufacturingOrderProductionResponse429,
)
from ...models.get_manufacturing_order_production_response_500 import (
    GetManufacturingOrderProductionResponse500,
)
from ...models.manufacturing_order_production import ManufacturingOrderProduction
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/manufacturing_order_productions/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderProduction.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetManufacturingOrderProductionResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetManufacturingOrderProductionResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetManufacturingOrderProductionResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
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
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
]:
    """Retrieve a manufacturing order production

     Retrieves the details of an existing manufacturing order production based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderProductionResponse401, GetManufacturingOrderProductionResponse429, GetManufacturingOrderProductionResponse500, ManufacturingOrderProduction]]
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
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    """Retrieve a manufacturing order production

     Retrieves the details of an existing manufacturing order production based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderProductionResponse401, GetManufacturingOrderProductionResponse429, GetManufacturingOrderProductionResponse500, ManufacturingOrderProduction]
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
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
]:
    """Retrieve a manufacturing order production

     Retrieves the details of an existing manufacturing order production based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderProductionResponse401, GetManufacturingOrderProductionResponse429, GetManufacturingOrderProductionResponse500, ManufacturingOrderProduction]]
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
    GetManufacturingOrderProductionResponse401
    | GetManufacturingOrderProductionResponse429
    | GetManufacturingOrderProductionResponse500
    | ManufacturingOrderProduction
    | None
):
    """Retrieve a manufacturing order production

     Retrieves the details of an existing manufacturing order production based on ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderProductionResponse401, GetManufacturingOrderProductionResponse429, GetManufacturingOrderProductionResponse500, ManufacturingOrderProduction]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
