from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_stock_list_response import BatchStockListResponse
from ...models.get_batch_stock_response_401 import GetBatchStockResponse401
from ...models.get_batch_stock_response_429 import GetBatchStockResponse429
from ...models.get_batch_stock_response_500 import GetBatchStockResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    batch_id: Unset | int = UNSET,
    batch_number: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    batch_barcode: Unset | str = UNSET,
    batch_created_at_min: Unset | str = UNSET,
    batch_created_at_max: Unset | str = UNSET,
    include_empty: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["batch_id"] = batch_id

    params["batch_number"] = batch_number

    params["location_id"] = location_id

    params["variant_id"] = variant_id

    params["batch_barcode"] = batch_barcode

    params["batch_created_at_min"] = batch_created_at_min

    params["batch_created_at_max"] = batch_created_at_max

    params["include_empty"] = include_empty

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/batch_stocks",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
    | None
):
    if response.status_code == 200:
        response_200 = BatchStockListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetBatchStockResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetBatchStockResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetBatchStockResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
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
    batch_id: Unset | int = UNSET,
    batch_number: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    batch_barcode: Unset | str = UNSET,
    batch_created_at_min: Unset | str = UNSET,
    batch_created_at_max: Unset | str = UNSET,
    include_empty: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
]:
    """List current batch stock

     Returns a list for current batch stock. The inventory is returned in sorted order, based on
    location_id ASC, variant_id ASC, and batch_id DESC.

    Args:
        batch_id (Union[Unset, int]):
        batch_number (Union[Unset, str]):
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        batch_barcode (Union[Unset, str]):
        batch_created_at_min (Union[Unset, str]):
        batch_created_at_max (Union[Unset, str]):
        include_empty (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchStockListResponse, GetBatchStockResponse401, GetBatchStockResponse429, GetBatchStockResponse500]]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
        batch_number=batch_number,
        location_id=location_id,
        variant_id=variant_id,
        batch_barcode=batch_barcode,
        batch_created_at_min=batch_created_at_min,
        batch_created_at_max=batch_created_at_max,
        include_empty=include_empty,
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
    batch_id: Unset | int = UNSET,
    batch_number: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    batch_barcode: Unset | str = UNSET,
    batch_created_at_min: Unset | str = UNSET,
    batch_created_at_max: Unset | str = UNSET,
    include_empty: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
    | None
):
    """List current batch stock

     Returns a list for current batch stock. The inventory is returned in sorted order, based on
    location_id ASC, variant_id ASC, and batch_id DESC.

    Args:
        batch_id (Union[Unset, int]):
        batch_number (Union[Unset, str]):
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        batch_barcode (Union[Unset, str]):
        batch_created_at_min (Union[Unset, str]):
        batch_created_at_max (Union[Unset, str]):
        include_empty (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchStockListResponse, GetBatchStockResponse401, GetBatchStockResponse429, GetBatchStockResponse500]
    """

    return sync_detailed(
        client=client,
        batch_id=batch_id,
        batch_number=batch_number,
        location_id=location_id,
        variant_id=variant_id,
        batch_barcode=batch_barcode,
        batch_created_at_min=batch_created_at_min,
        batch_created_at_max=batch_created_at_max,
        include_empty=include_empty,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    batch_id: Unset | int = UNSET,
    batch_number: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    batch_barcode: Unset | str = UNSET,
    batch_created_at_min: Unset | str = UNSET,
    batch_created_at_max: Unset | str = UNSET,
    include_empty: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
]:
    """List current batch stock

     Returns a list for current batch stock. The inventory is returned in sorted order, based on
    location_id ASC, variant_id ASC, and batch_id DESC.

    Args:
        batch_id (Union[Unset, int]):
        batch_number (Union[Unset, str]):
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        batch_barcode (Union[Unset, str]):
        batch_created_at_min (Union[Unset, str]):
        batch_created_at_max (Union[Unset, str]):
        include_empty (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchStockListResponse, GetBatchStockResponse401, GetBatchStockResponse429, GetBatchStockResponse500]]
    """

    kwargs = _get_kwargs(
        batch_id=batch_id,
        batch_number=batch_number,
        location_id=location_id,
        variant_id=variant_id,
        batch_barcode=batch_barcode,
        batch_created_at_min=batch_created_at_min,
        batch_created_at_max=batch_created_at_max,
        include_empty=include_empty,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    batch_id: Unset | int = UNSET,
    batch_number: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    batch_barcode: Unset | str = UNSET,
    batch_created_at_min: Unset | str = UNSET,
    batch_created_at_max: Unset | str = UNSET,
    include_empty: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    BatchStockListResponse
    | GetBatchStockResponse401
    | GetBatchStockResponse429
    | GetBatchStockResponse500
    | None
):
    """List current batch stock

     Returns a list for current batch stock. The inventory is returned in sorted order, based on
    location_id ASC, variant_id ASC, and batch_id DESC.

    Args:
        batch_id (Union[Unset, int]):
        batch_number (Union[Unset, str]):
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        batch_barcode (Union[Unset, str]):
        batch_created_at_min (Union[Unset, str]):
        batch_created_at_max (Union[Unset, str]):
        include_empty (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchStockListResponse, GetBatchStockResponse401, GetBatchStockResponse429, GetBatchStockResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            batch_id=batch_id,
            batch_number=batch_number,
            location_id=location_id,
            variant_id=variant_id,
            batch_barcode=batch_barcode,
            batch_created_at_min=batch_created_at_min,
            batch_created_at_max=batch_created_at_max,
            include_empty=include_empty,
            limit=limit,
            page=page,
        )
    ).parsed
