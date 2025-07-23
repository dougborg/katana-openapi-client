from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sales_order_response_401 import GetSalesOrderResponse401
from ...models.get_sales_order_response_404 import GetSalesOrderResponse404
from ...models.get_sales_order_response_429 import GetSalesOrderResponse429
from ...models.get_sales_order_response_500 import GetSalesOrderResponse500
from ...models.sales_order import SalesOrder
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/sales_orders/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
    | None
):
    if response.status_code == 200:
        response_200 = SalesOrder.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetSalesOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = GetSalesOrderResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = GetSalesOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetSalesOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
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
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
]:
    """Retrieve a sales order

     Retrieves a sales order by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesOrderResponse401, GetSalesOrderResponse404, GetSalesOrderResponse429, GetSalesOrderResponse500, SalesOrder]]
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
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
    | None
):
    """Retrieve a sales order

     Retrieves a sales order by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesOrderResponse401, GetSalesOrderResponse404, GetSalesOrderResponse429, GetSalesOrderResponse500, SalesOrder]
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
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
]:
    """Retrieve a sales order

     Retrieves a sales order by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesOrderResponse401, GetSalesOrderResponse404, GetSalesOrderResponse429, GetSalesOrderResponse500, SalesOrder]]
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
    GetSalesOrderResponse401
    | GetSalesOrderResponse404
    | GetSalesOrderResponse429
    | GetSalesOrderResponse500
    | SalesOrder
    | None
):
    """Retrieve a sales order

     Retrieves a sales order by ID.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesOrderResponse401, GetSalesOrderResponse404, GetSalesOrderResponse429, GetSalesOrderResponse500, SalesOrder]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
