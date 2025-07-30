from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_purchase_order_row_response_401 import GetPurchaseOrderRowResponse401
from ...models.get_purchase_order_row_response_429 import GetPurchaseOrderRowResponse429
from ...models.get_purchase_order_row_response_500 import GetPurchaseOrderRowResponse500
from ...models.purchase_order_row import PurchaseOrderRow
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/purchase_order_rows/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetPurchaseOrderRowResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetPurchaseOrderRowResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetPurchaseOrderRowResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
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
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
]:
    """Retrieve a purchase order row

     Retrieves the details of an existing purchase order row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetPurchaseOrderRowResponse401, GetPurchaseOrderRowResponse429, GetPurchaseOrderRowResponse500, PurchaseOrderRow]]
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
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    """Retrieve a purchase order row

     Retrieves the details of an existing purchase order row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetPurchaseOrderRowResponse401, GetPurchaseOrderRowResponse429, GetPurchaseOrderRowResponse500, PurchaseOrderRow]
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
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
]:
    """Retrieve a purchase order row

     Retrieves the details of an existing purchase order row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetPurchaseOrderRowResponse401, GetPurchaseOrderRowResponse429, GetPurchaseOrderRowResponse500, PurchaseOrderRow]]
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
    GetPurchaseOrderRowResponse401
    | GetPurchaseOrderRowResponse429
    | GetPurchaseOrderRowResponse500
    | PurchaseOrderRow
    | None
):
    """Retrieve a purchase order row

     Retrieves the details of an existing purchase order row based on ID

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetPurchaseOrderRowResponse401, GetPurchaseOrderRowResponse429, GetPurchaseOrderRowResponse500, PurchaseOrderRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
