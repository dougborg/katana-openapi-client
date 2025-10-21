import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.stocktake_row_list_response import StocktakeRowListResponse


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    stocktake_ids: Unset | list[int] = UNSET,
    batch_id: Unset | int = UNSET,
    stock_adjustment_id: Unset | float = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["variant_id"] = variant_id

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_stocktake_ids: Unset | list[int] = UNSET
    if not isinstance(stocktake_ids, Unset):
        json_stocktake_ids = stocktake_ids

    params["stocktake_ids"] = json_stocktake_ids

    params["batch_id"] = batch_id

    params["stock_adjustment_id"] = stock_adjustment_id

    params["include_deleted"] = include_deleted

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
        "url": "/stocktake_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | StocktakeRowListResponse | None:
    if response.status_code == 200:
        response_200 = StocktakeRowListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 429:
        response_429 = ErrorResponse.from_dict(response.json())

        return response_429

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | StocktakeRowListResponse]:
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
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    stocktake_ids: Unset | list[int] = UNSET,
    batch_id: Unset | int = UNSET,
    stock_adjustment_id: Unset | float = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | StocktakeRowListResponse]:
    """List stocktake rows

     Returns a list of stocktake rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        stocktake_ids (Union[Unset, list[int]]):
        batch_id (Union[Unset, int]):
        stock_adjustment_id (Union[Unset, float]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, StocktakeRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        stocktake_ids=stocktake_ids,
        batch_id=batch_id,
        stock_adjustment_id=stock_adjustment_id,
        include_deleted=include_deleted,
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    stocktake_ids: Unset | list[int] = UNSET,
    batch_id: Unset | int = UNSET,
    stock_adjustment_id: Unset | float = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | StocktakeRowListResponse | None:
    """List stocktake rows

     Returns a list of stocktake rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        stocktake_ids (Union[Unset, list[int]]):
        batch_id (Union[Unset, int]):
        stock_adjustment_id (Union[Unset, float]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, StocktakeRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        stocktake_ids=stocktake_ids,
        batch_id=batch_id,
        stock_adjustment_id=stock_adjustment_id,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    stocktake_ids: Unset | list[int] = UNSET,
    batch_id: Unset | int = UNSET,
    stock_adjustment_id: Unset | float = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | StocktakeRowListResponse]:
    """List stocktake rows

     Returns a list of stocktake rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        stocktake_ids (Union[Unset, list[int]]):
        batch_id (Union[Unset, int]):
        stock_adjustment_id (Union[Unset, float]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, StocktakeRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        stocktake_ids=stocktake_ids,
        batch_id=batch_id,
        stock_adjustment_id=stock_adjustment_id,
        include_deleted=include_deleted,
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    stocktake_ids: Unset | list[int] = UNSET,
    batch_id: Unset | int = UNSET,
    stock_adjustment_id: Unset | float = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | StocktakeRowListResponse | None:
    """List stocktake rows

     Returns a list of stocktake rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        stocktake_ids (Union[Unset, list[int]]):
        batch_id (Union[Unset, int]):
        stock_adjustment_id (Union[Unset, float]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, StocktakeRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            variant_id=variant_id,
            ids=ids,
            stocktake_ids=stocktake_ids,
            batch_id=batch_id,
            stock_adjustment_id=stock_adjustment_id,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
