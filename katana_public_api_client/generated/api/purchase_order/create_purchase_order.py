from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_purchase_order_request import CreatePurchaseOrderRequest
from ...models.create_purchase_order_response_401 import CreatePurchaseOrderResponse401
from ...models.create_purchase_order_response_422 import CreatePurchaseOrderResponse422
from ...models.create_purchase_order_response_429 import CreatePurchaseOrderResponse429
from ...models.create_purchase_order_response_500 import CreatePurchaseOrderResponse500
from ...models.purchase_order import PurchaseOrder
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePurchaseOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/purchase_orders",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrder.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreatePurchaseOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePurchaseOrderResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePurchaseOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePurchaseOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
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
    body: CreatePurchaseOrderRequest,
) -> Response[
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
]:
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePurchaseOrderResponse401, CreatePurchaseOrderResponse422, CreatePurchaseOrderResponse429, CreatePurchaseOrderResponse500, PurchaseOrder]]
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
    body: CreatePurchaseOrderRequest,
) -> (
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
    | None
):
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePurchaseOrderResponse401, CreatePurchaseOrderResponse422, CreatePurchaseOrderResponse429, CreatePurchaseOrderResponse500, PurchaseOrder]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRequest,
) -> Response[
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
]:
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePurchaseOrderResponse401, CreatePurchaseOrderResponse422, CreatePurchaseOrderResponse429, CreatePurchaseOrderResponse500, PurchaseOrder]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRequest,
) -> (
    CreatePurchaseOrderResponse401
    | CreatePurchaseOrderResponse422
    | CreatePurchaseOrderResponse429
    | CreatePurchaseOrderResponse500
    | PurchaseOrder
    | None
):
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePurchaseOrderResponse401, CreatePurchaseOrderResponse422, CreatePurchaseOrderResponse429, CreatePurchaseOrderResponse500, PurchaseOrder]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
