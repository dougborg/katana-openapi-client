from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.purchase_order_row import PurchaseOrderRow
from ...models.update_purchase_order_row_request import UpdatePurchaseOrderRowRequest
from ...models.update_purchase_order_row_response_401 import (
    UpdatePurchaseOrderRowResponse401,
)
from ...models.update_purchase_order_row_response_422 import (
    UpdatePurchaseOrderRowResponse422,
)
from ...models.update_purchase_order_row_response_429 import (
    UpdatePurchaseOrderRowResponse429,
)
from ...models.update_purchase_order_row_response_500 import (
    UpdatePurchaseOrderRowResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdatePurchaseOrderRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/purchase_order_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = UpdatePurchaseOrderRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = UpdatePurchaseOrderRowResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = UpdatePurchaseOrderRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdatePurchaseOrderRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
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
    body: UpdatePurchaseOrderRowRequest,
) -> Response[
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
]:
    """Update a purchase order row

     Updates the specified purchase order row by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[PurchaseOrderRow, UpdatePurchaseOrderRowResponse401, UpdatePurchaseOrderRowResponse422, UpdatePurchaseOrderRowResponse429, UpdatePurchaseOrderRowResponse500]]
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
    body: UpdatePurchaseOrderRowRequest,
) -> (
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
    | None
):
    """Update a purchase order row

     Updates the specified purchase order row by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[PurchaseOrderRow, UpdatePurchaseOrderRowResponse401, UpdatePurchaseOrderRowResponse422, UpdatePurchaseOrderRowResponse429, UpdatePurchaseOrderRowResponse500]
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
    body: UpdatePurchaseOrderRowRequest,
) -> Response[
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
]:
    """Update a purchase order row

     Updates the specified purchase order row by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[PurchaseOrderRow, UpdatePurchaseOrderRowResponse401, UpdatePurchaseOrderRowResponse422, UpdatePurchaseOrderRowResponse429, UpdatePurchaseOrderRowResponse500]]
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
    body: UpdatePurchaseOrderRowRequest,
) -> (
    PurchaseOrderRow
    | UpdatePurchaseOrderRowResponse401
    | UpdatePurchaseOrderRowResponse422
    | UpdatePurchaseOrderRowResponse429
    | UpdatePurchaseOrderRowResponse500
    | None
):
    """Update a purchase order row

     Updates the specified purchase order row by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[PurchaseOrderRow, UpdatePurchaseOrderRowResponse401, UpdatePurchaseOrderRowResponse422, UpdatePurchaseOrderRowResponse429, UpdatePurchaseOrderRowResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
