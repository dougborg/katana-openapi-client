from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_stock_transfers_response_401 import (
    GetAllStockTransfersResponse401,
)
from ...models.get_all_stock_transfers_response_429 import (
    GetAllStockTransfersResponse429,
)
from ...models.get_all_stock_transfers_response_500 import (
    GetAllStockTransfersResponse500,
)
from ...models.stock_transfer_list_response import StockTransferListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    from_location_id: Unset | int = UNSET,
    to_location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["from_location_id"] = from_location_id

    params["to_location_id"] = to_location_id

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/stock_transfers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
    | None
):
    if response.status_code == 200:
        response_200 = StockTransferListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllStockTransfersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllStockTransfersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllStockTransfersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    from_location_id: Unset | int = UNSET,
    to_location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
]:
    """List all stock transfers

     Returns a list of stock transfers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        from_location_id (Union[Unset, int]):
        to_location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllStockTransfersResponse401, GetAllStockTransfersResponse429, GetAllStockTransfersResponse500, StockTransferListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    from_location_id: Unset | int = UNSET,
    to_location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
    | None
):
    """List all stock transfers

     Returns a list of stock transfers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        from_location_id (Union[Unset, int]):
        to_location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllStockTransfersResponse401, GetAllStockTransfersResponse429, GetAllStockTransfersResponse500, StockTransferListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    from_location_id: Unset | int = UNSET,
    to_location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
]:
    """List all stock transfers

     Returns a list of stock transfers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        from_location_id (Union[Unset, int]):
        to_location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllStockTransfersResponse401, GetAllStockTransfersResponse429, GetAllStockTransfersResponse500, StockTransferListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        from_location_id=from_location_id,
        to_location_id=to_location_id,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    from_location_id: Unset | int = UNSET,
    to_location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllStockTransfersResponse401
    | GetAllStockTransfersResponse429
    | GetAllStockTransfersResponse500
    | StockTransferListResponse
    | None
):
    """List all stock transfers

     Returns a list of stock transfers.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        from_location_id (Union[Unset, int]):
        to_location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllStockTransfersResponse401, GetAllStockTransfersResponse429, GetAllStockTransfersResponse500, StockTransferListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            include_deleted=include_deleted,
        )
    ).parsed
