from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_inventory_safety_stock_level_response_401 import (
    CreateInventorySafetyStockLevelResponse401,
)
from ...models.create_inventory_safety_stock_level_response_422 import (
    CreateInventorySafetyStockLevelResponse422,
)
from ...models.create_inventory_safety_stock_level_response_429 import (
    CreateInventorySafetyStockLevelResponse429,
)
from ...models.create_inventory_safety_stock_level_response_500 import (
    CreateInventorySafetyStockLevelResponse500,
)
from ...models.inventory_safety_stock_level import InventorySafetyStockLevel
from ...types import Response


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
) -> (
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
    | None
):
    if response.status_code == 200:
        response_200 = InventorySafetyStockLevel.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateInventorySafetyStockLevelResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 422:
        response_422 = CreateInventorySafetyStockLevelResponse422.from_dict(
            response.json()
        )

        return response_422
    if response.status_code == 429:
        response_429 = CreateInventorySafetyStockLevelResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = CreateInventorySafetyStockLevelResponse500.from_dict(
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
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
]:
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
) -> Response[
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
]:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateInventorySafetyStockLevelResponse401, CreateInventorySafetyStockLevelResponse422, CreateInventorySafetyStockLevelResponse429, CreateInventorySafetyStockLevelResponse500, InventorySafetyStockLevel]]
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
) -> (
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
    | None
):
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateInventorySafetyStockLevelResponse401, CreateInventorySafetyStockLevelResponse422, CreateInventorySafetyStockLevelResponse429, CreateInventorySafetyStockLevelResponse500, InventorySafetyStockLevel]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InventorySafetyStockLevel,
) -> Response[
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
]:
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateInventorySafetyStockLevelResponse401, CreateInventorySafetyStockLevelResponse422, CreateInventorySafetyStockLevelResponse429, CreateInventorySafetyStockLevelResponse500, InventorySafetyStockLevel]]
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
) -> (
    CreateInventorySafetyStockLevelResponse401
    | CreateInventorySafetyStockLevelResponse422
    | CreateInventorySafetyStockLevelResponse429
    | CreateInventorySafetyStockLevelResponse500
    | InventorySafetyStockLevel
    | None
):
    """Update the safety stock level

     Update an item's safety stock level within a certain location and variant combination.

    Args:
        body (InventorySafetyStockLevel):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateInventorySafetyStockLevelResponse401, CreateInventorySafetyStockLevelResponse422, CreateInventorySafetyStockLevelResponse429, CreateInventorySafetyStockLevelResponse500, InventorySafetyStockLevel]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
