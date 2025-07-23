from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_purchase_order_response_401 import DeletePurchaseOrderResponse401
from ...models.delete_purchase_order_response_404 import DeletePurchaseOrderResponse404
from ...models.delete_purchase_order_response_429 import DeletePurchaseOrderResponse429
from ...models.delete_purchase_order_response_500 import DeletePurchaseOrderResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/purchase_orders/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = DeletePurchaseOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeletePurchaseOrderResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeletePurchaseOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeletePurchaseOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
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
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
]:
    """Delete purchase order

     Deletes a single purchase order by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeletePurchaseOrderResponse401, DeletePurchaseOrderResponse404, DeletePurchaseOrderResponse429, DeletePurchaseOrderResponse500]]
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
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
    | None
):
    """Delete purchase order

     Deletes a single purchase order by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeletePurchaseOrderResponse401, DeletePurchaseOrderResponse404, DeletePurchaseOrderResponse429, DeletePurchaseOrderResponse500]
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
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
]:
    """Delete purchase order

     Deletes a single purchase order by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeletePurchaseOrderResponse401, DeletePurchaseOrderResponse404, DeletePurchaseOrderResponse429, DeletePurchaseOrderResponse500]]
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
    | DeletePurchaseOrderResponse401
    | DeletePurchaseOrderResponse404
    | DeletePurchaseOrderResponse429
    | DeletePurchaseOrderResponse500
    | None
):
    """Delete purchase order

     Deletes a single purchase order by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeletePurchaseOrderResponse401, DeletePurchaseOrderResponse404, DeletePurchaseOrderResponse429, DeletePurchaseOrderResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
