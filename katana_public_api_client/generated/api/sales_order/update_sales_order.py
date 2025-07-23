from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_sales_order_body import UpdateSalesOrderBody
from ...models.update_sales_order_response_401 import UpdateSalesOrderResponse401
from ...models.update_sales_order_response_404 import UpdateSalesOrderResponse404
from ...models.update_sales_order_response_429 import UpdateSalesOrderResponse429
from ...models.update_sales_order_response_500 import UpdateSalesOrderResponse500
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateSalesOrderBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/sales_orders/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
    | None
):
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200
    if response.status_code == 401:
        response_401 = UpdateSalesOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = UpdateSalesOrderResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = UpdateSalesOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateSalesOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
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
    body: UpdateSalesOrderBody,
) -> Response[
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
]:
    """Update a sales order

     Updates a sales order.

    Args:
        id (int):
        body (UpdateSalesOrderBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UpdateSalesOrderResponse401, UpdateSalesOrderResponse404, UpdateSalesOrderResponse429, UpdateSalesOrderResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateSalesOrderBody,
) -> (
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
    | None
):
    """Update a sales order

     Updates a sales order.

    Args:
        id (int):
        body (UpdateSalesOrderBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UpdateSalesOrderResponse401, UpdateSalesOrderResponse404, UpdateSalesOrderResponse429, UpdateSalesOrderResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateSalesOrderBody,
) -> Response[
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
]:
    """Update a sales order

     Updates a sales order.

    Args:
        id (int):
        body (UpdateSalesOrderBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UpdateSalesOrderResponse401, UpdateSalesOrderResponse404, UpdateSalesOrderResponse429, UpdateSalesOrderResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateSalesOrderBody,
) -> (
    Any
    | UpdateSalesOrderResponse401
    | UpdateSalesOrderResponse404
    | UpdateSalesOrderResponse429
    | UpdateSalesOrderResponse500
    | None
):
    """Update a sales order

     Updates a sales order.

    Args:
        id (int):
        body (UpdateSalesOrderBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UpdateSalesOrderResponse401, UpdateSalesOrderResponse404, UpdateSalesOrderResponse429, UpdateSalesOrderResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
