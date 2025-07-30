from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_purchase_order_row_request import CreatePurchaseOrderRowRequest
from ...models.create_purchase_order_row_response_401 import (
    CreatePurchaseOrderRowResponse401,
)
from ...models.create_purchase_order_row_response_422 import (
    CreatePurchaseOrderRowResponse422,
)
from ...models.create_purchase_order_row_response_429 import (
    CreatePurchaseOrderRowResponse429,
)
from ...models.create_purchase_order_row_response_500 import (
    CreatePurchaseOrderRowResponse500,
)
from ...models.purchase_order_row import PurchaseOrderRow
from ...types import Response


def _get_kwargs(
    *,
    body: CreatePurchaseOrderRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/purchase_order_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreatePurchaseOrderRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreatePurchaseOrderRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreatePurchaseOrderRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreatePurchaseOrderRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
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
    body: CreatePurchaseOrderRowRequest,
) -> Response[
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
]:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePurchaseOrderRowResponse401, CreatePurchaseOrderRowResponse422, CreatePurchaseOrderRowResponse429, CreatePurchaseOrderRowResponse500, PurchaseOrderRow]]
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
    body: CreatePurchaseOrderRowRequest,
) -> (
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePurchaseOrderRowResponse401, CreatePurchaseOrderRowResponse422, CreatePurchaseOrderRowResponse429, CreatePurchaseOrderRowResponse500, PurchaseOrderRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRowRequest,
) -> Response[
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
]:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreatePurchaseOrderRowResponse401, CreatePurchaseOrderRowResponse422, CreatePurchaseOrderRowResponse429, CreatePurchaseOrderRowResponse500, PurchaseOrderRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRowRequest,
) -> (
    CreatePurchaseOrderRowResponse401
    | CreatePurchaseOrderRowResponse422
    | CreatePurchaseOrderRowResponse429
    | CreatePurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreatePurchaseOrderRowResponse401, CreatePurchaseOrderRowResponse422, CreatePurchaseOrderRowResponse429, CreatePurchaseOrderRowResponse500, PurchaseOrderRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
