import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_purchase_order_rows_response_401 import (
    GetAllPurchaseOrderRowsResponse401,
)
from ...models.get_all_purchase_order_rows_response_429 import (
    GetAllPurchaseOrderRowsResponse429,
)
from ...models.get_all_purchase_order_rows_response_500 import (
    GetAllPurchaseOrderRowsResponse500,
)
from ...models.purchase_order_row_list_response import PurchaseOrderRowListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    purchase_order_id: Unset | float = UNSET,
    variant_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    group_id: Unset | float = UNSET,
    purchase_uom: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["purchase_order_id"] = purchase_order_id

    params["variant_id"] = variant_id

    params["tax_rate_id"] = tax_rate_id

    params["group_id"] = group_id

    params["purchase_uom"] = purchase_uom

    params["include_deleted"] = include_deleted

    params["limit"] = limit

    params["page"] = page

    json_created_at_min: Unset | str = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: Unset | str = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: Unset | str = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: Unset | str = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/purchase_order_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderRowListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllPurchaseOrderRowsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllPurchaseOrderRowsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllPurchaseOrderRowsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
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
    ids: Unset | list[int] = UNSET,
    purchase_order_id: Unset | float = UNSET,
    variant_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    group_id: Unset | float = UNSET,
    purchase_uom: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
]:
    """List all purchase order rows

     Returns a list of purchase order rows you've previously created.
      The purchase order rows are returned in sorted order, with the most recent rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        purchase_order_id (Union[Unset, float]):
        variant_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        group_id (Union[Unset, float]):
        purchase_uom (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPurchaseOrderRowsResponse401, GetAllPurchaseOrderRowsResponse429, GetAllPurchaseOrderRowsResponse500, PurchaseOrderRowListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        purchase_order_id=purchase_order_id,
        variant_id=variant_id,
        tax_rate_id=tax_rate_id,
        group_id=group_id,
        purchase_uom=purchase_uom,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    purchase_order_id: Unset | float = UNSET,
    variant_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    group_id: Unset | float = UNSET,
    purchase_uom: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
    | None
):
    """List all purchase order rows

     Returns a list of purchase order rows you've previously created.
      The purchase order rows are returned in sorted order, with the most recent rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        purchase_order_id (Union[Unset, float]):
        variant_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        group_id (Union[Unset, float]):
        purchase_uom (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPurchaseOrderRowsResponse401, GetAllPurchaseOrderRowsResponse429, GetAllPurchaseOrderRowsResponse500, PurchaseOrderRowListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        purchase_order_id=purchase_order_id,
        variant_id=variant_id,
        tax_rate_id=tax_rate_id,
        group_id=group_id,
        purchase_uom=purchase_uom,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    purchase_order_id: Unset | float = UNSET,
    variant_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    group_id: Unset | float = UNSET,
    purchase_uom: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
]:
    """List all purchase order rows

     Returns a list of purchase order rows you've previously created.
      The purchase order rows are returned in sorted order, with the most recent rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        purchase_order_id (Union[Unset, float]):
        variant_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        group_id (Union[Unset, float]):
        purchase_uom (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPurchaseOrderRowsResponse401, GetAllPurchaseOrderRowsResponse429, GetAllPurchaseOrderRowsResponse500, PurchaseOrderRowListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        purchase_order_id=purchase_order_id,
        variant_id=variant_id,
        tax_rate_id=tax_rate_id,
        group_id=group_id,
        purchase_uom=purchase_uom,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    ids: Unset | list[int] = UNSET,
    purchase_order_id: Unset | float = UNSET,
    variant_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    group_id: Unset | float = UNSET,
    purchase_uom: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllPurchaseOrderRowsResponse401
    | GetAllPurchaseOrderRowsResponse429
    | GetAllPurchaseOrderRowsResponse500
    | PurchaseOrderRowListResponse
    | None
):
    """List all purchase order rows

     Returns a list of purchase order rows you've previously created.
      The purchase order rows are returned in sorted order, with the most recent rows appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        purchase_order_id (Union[Unset, float]):
        variant_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        group_id (Union[Unset, float]):
        purchase_uom (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPurchaseOrderRowsResponse401, GetAllPurchaseOrderRowsResponse429, GetAllPurchaseOrderRowsResponse500, PurchaseOrderRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            purchase_order_id=purchase_order_id,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            group_id=group_id,
            purchase_uom=purchase_uom,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
