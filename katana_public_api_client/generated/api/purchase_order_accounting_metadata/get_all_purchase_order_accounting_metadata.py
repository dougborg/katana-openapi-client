from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_purchase_order_accounting_metadata_response_401 import (
    GetAllPurchaseOrderAccountingMetadataResponse401,
)
from ...models.get_all_purchase_order_accounting_metadata_response_429 import (
    GetAllPurchaseOrderAccountingMetadataResponse429,
)
from ...models.get_all_purchase_order_accounting_metadata_response_500 import (
    GetAllPurchaseOrderAccountingMetadataResponse500,
)
from ...models.purchase_order_accounting_metadata_list_response import (
    PurchaseOrderAccountingMetadataListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    purchase_order_id: Unset | float = UNSET,
    received_items_group_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["purchase_order_id"] = purchase_order_id

    params["received_items_group_id"] = received_items_group_id

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/purchase_order_accounting_metadata",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderAccountingMetadataListResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = GetAllPurchaseOrderAccountingMetadataResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetAllPurchaseOrderAccountingMetadataResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetAllPurchaseOrderAccountingMetadataResponse500.from_dict(
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
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
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
    purchase_order_id: Unset | float = UNSET,
    received_items_group_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
]:
    """List all purchase order accounting metadata

     Returns a list of purchase order accounting metadata entries.

    Args:
        purchase_order_id (Union[Unset, float]):
        received_items_group_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPurchaseOrderAccountingMetadataResponse401, GetAllPurchaseOrderAccountingMetadataResponse429, GetAllPurchaseOrderAccountingMetadataResponse500, PurchaseOrderAccountingMetadataListResponse]]
    """

    kwargs = _get_kwargs(
        purchase_order_id=purchase_order_id,
        received_items_group_id=received_items_group_id,
        limit=limit,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    purchase_order_id: Unset | float = UNSET,
    received_items_group_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
    | None
):
    """List all purchase order accounting metadata

     Returns a list of purchase order accounting metadata entries.

    Args:
        purchase_order_id (Union[Unset, float]):
        received_items_group_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPurchaseOrderAccountingMetadataResponse401, GetAllPurchaseOrderAccountingMetadataResponse429, GetAllPurchaseOrderAccountingMetadataResponse500, PurchaseOrderAccountingMetadataListResponse]
    """

    return sync_detailed(
        client=client,
        purchase_order_id=purchase_order_id,
        received_items_group_id=received_items_group_id,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    purchase_order_id: Unset | float = UNSET,
    received_items_group_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
]:
    """List all purchase order accounting metadata

     Returns a list of purchase order accounting metadata entries.

    Args:
        purchase_order_id (Union[Unset, float]):
        received_items_group_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPurchaseOrderAccountingMetadataResponse401, GetAllPurchaseOrderAccountingMetadataResponse429, GetAllPurchaseOrderAccountingMetadataResponse500, PurchaseOrderAccountingMetadataListResponse]]
    """

    kwargs = _get_kwargs(
        purchase_order_id=purchase_order_id,
        received_items_group_id=received_items_group_id,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    purchase_order_id: Unset | float = UNSET,
    received_items_group_id: Unset | float = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllPurchaseOrderAccountingMetadataResponse401
    | GetAllPurchaseOrderAccountingMetadataResponse429
    | GetAllPurchaseOrderAccountingMetadataResponse500
    | PurchaseOrderAccountingMetadataListResponse
    | None
):
    """List all purchase order accounting metadata

     Returns a list of purchase order accounting metadata entries.

    Args:
        purchase_order_id (Union[Unset, float]):
        received_items_group_id (Union[Unset, float]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPurchaseOrderAccountingMetadataResponse401, GetAllPurchaseOrderAccountingMetadataResponse429, GetAllPurchaseOrderAccountingMetadataResponse500, PurchaseOrderAccountingMetadataListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            purchase_order_id=purchase_order_id,
            received_items_group_id=received_items_group_id,
            limit=limit,
            page=page,
        )
    ).parsed
