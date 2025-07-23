from http import HTTPStatus
from typing import Any, Union, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.purchase_order_receive_row import PurchaseOrderReceiveRow
from ...models.receive_purchase_order_response_401 import (
    ReceivePurchaseOrderResponse401,
)
from ...models.receive_purchase_order_response_422 import (
    ReceivePurchaseOrderResponse422,
)
from ...models.receive_purchase_order_response_429 import (
    ReceivePurchaseOrderResponse429,
)
from ...models.receive_purchase_order_response_500 import (
    ReceivePurchaseOrderResponse500,
)
from ...types import Response


def _get_kwargs(
    *,
    body: Union["PurchaseOrderReceiveRow", list["PurchaseOrderReceiveRow"]],
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/purchase_order_receive",
    }

    _kwargs["json"] = None  # type: dict[str, Any] | list[dict[str, Any]]
    if isinstance(body, list):
        _kwargs["json"] = []
        for componentsschemas_purchase_order_receive_request_type_0_item_data in body:
            componentsschemas_purchase_order_receive_request_type_0_item = componentsschemas_purchase_order_receive_request_type_0_item_data.to_dict()
            _kwargs["json"].append(
                componentsschemas_purchase_order_receive_request_type_0_item
            )

    else:
        _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = ReceivePurchaseOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = ReceivePurchaseOrderResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = ReceivePurchaseOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = ReceivePurchaseOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
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
    body: Union["PurchaseOrderReceiveRow", list["PurchaseOrderReceiveRow"]],
) -> Response[
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
]:
    """Receive a purchase order

     If you receive the items on the purchase order, you can mark the purchase order as received.
        This will update the existing purchase order rows quantities to the quantities left unreceived
    and
        create a new rows with the received quantities and dates. If you want to mark all rows as
    received and
        the order doesn't contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
        Reverting the receive must also be done through that endpoint.

    Args:
        body (Union['PurchaseOrderReceiveRow', list['PurchaseOrderReceiveRow']]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ReceivePurchaseOrderResponse401, ReceivePurchaseOrderResponse422, ReceivePurchaseOrderResponse429, ReceivePurchaseOrderResponse500]]
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
    body: Union["PurchaseOrderReceiveRow", list["PurchaseOrderReceiveRow"]],
) -> (
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
    | None
):
    """Receive a purchase order

     If you receive the items on the purchase order, you can mark the purchase order as received.
        This will update the existing purchase order rows quantities to the quantities left unreceived
    and
        create a new rows with the received quantities and dates. If you want to mark all rows as
    received and
        the order doesn't contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
        Reverting the receive must also be done through that endpoint.

    Args:
        body (Union['PurchaseOrderReceiveRow', list['PurchaseOrderReceiveRow']]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ReceivePurchaseOrderResponse401, ReceivePurchaseOrderResponse422, ReceivePurchaseOrderResponse429, ReceivePurchaseOrderResponse500]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: Union["PurchaseOrderReceiveRow", list["PurchaseOrderReceiveRow"]],
) -> Response[
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
]:
    """Receive a purchase order

     If you receive the items on the purchase order, you can mark the purchase order as received.
        This will update the existing purchase order rows quantities to the quantities left unreceived
    and
        create a new rows with the received quantities and dates. If you want to mark all rows as
    received and
        the order doesn't contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
        Reverting the receive must also be done through that endpoint.

    Args:
        body (Union['PurchaseOrderReceiveRow', list['PurchaseOrderReceiveRow']]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ReceivePurchaseOrderResponse401, ReceivePurchaseOrderResponse422, ReceivePurchaseOrderResponse429, ReceivePurchaseOrderResponse500]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: Union["PurchaseOrderReceiveRow", list["PurchaseOrderReceiveRow"]],
) -> (
    Any
    | ReceivePurchaseOrderResponse401
    | ReceivePurchaseOrderResponse422
    | ReceivePurchaseOrderResponse429
    | ReceivePurchaseOrderResponse500
    | None
):
    """Receive a purchase order

     If you receive the items on the purchase order, you can mark the purchase order as received.
        This will update the existing purchase order rows quantities to the quantities left unreceived
    and
        create a new rows with the received quantities and dates. If you want to mark all rows as
    received and
        the order doesn't contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
        Reverting the receive must also be done through that endpoint.

    Args:
        body (Union['PurchaseOrderReceiveRow', list['PurchaseOrderReceiveRow']]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ReceivePurchaseOrderResponse401, ReceivePurchaseOrderResponse422, ReceivePurchaseOrderResponse429, ReceivePurchaseOrderResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
