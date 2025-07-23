from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_sales_order_response_401 import DeleteSalesOrderResponse401
from ...models.delete_sales_order_response_404 import DeleteSalesOrderResponse404
from ...models.delete_sales_order_response_429 import DeleteSalesOrderResponse429
from ...models.delete_sales_order_response_500 import DeleteSalesOrderResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/sales_orders/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
    | None
):
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200
    if response.status_code == 401:
        response_401 = DeleteSalesOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteSalesOrderResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteSalesOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteSalesOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
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
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
]:
    """Delete a sales order

     Deletes a sales order.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteSalesOrderResponse401, DeleteSalesOrderResponse404, DeleteSalesOrderResponse429, DeleteSalesOrderResponse500]]
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
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
    | None
):
    """Delete a sales order

     Deletes a sales order.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteSalesOrderResponse401, DeleteSalesOrderResponse404, DeleteSalesOrderResponse429, DeleteSalesOrderResponse500]
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
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
]:
    """Delete a sales order

     Deletes a sales order.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteSalesOrderResponse401, DeleteSalesOrderResponse404, DeleteSalesOrderResponse429, DeleteSalesOrderResponse500]]
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
    Any
    | DeleteSalesOrderResponse401
    | DeleteSalesOrderResponse404
    | DeleteSalesOrderResponse429
    | DeleteSalesOrderResponse500
    | None
):
    """Delete a sales order

     Deletes a sales order.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteSalesOrderResponse401, DeleteSalesOrderResponse404, DeleteSalesOrderResponse429, DeleteSalesOrderResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
