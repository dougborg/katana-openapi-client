from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_negative_stock_response_401 import GetAllNegativeStockResponse401
from ...models.get_all_negative_stock_response_429 import GetAllNegativeStockResponse429
from ...models.get_all_negative_stock_response_500 import GetAllNegativeStockResponse500
from ...models.negative_stock_list_response import NegativeStockListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    latest_negative_stock_date_max: Unset | str = UNSET,
    latest_negative_stock_date_min: Unset | str = UNSET,
    name: Unset | str = UNSET,
    sku: Unset | str = UNSET,
    category: Unset | str = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["location_id"] = location_id

    params["variant_id"] = variant_id

    params["latest_negative_stock_date_max"] = latest_negative_stock_date_max

    params["latest_negative_stock_date_min"] = latest_negative_stock_date_min

    params["name"] = name

    params["sku"] = sku

    params["category"] = category

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/negative_stock",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
    | None
):
    if response.status_code == 200:
        response_200 = NegativeStockListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllNegativeStockResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllNegativeStockResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllNegativeStockResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
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
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    latest_negative_stock_date_max: Unset | str = UNSET,
    latest_negative_stock_date_min: Unset | str = UNSET,
    name: Unset | str = UNSET,
    sku: Unset | str = UNSET,
    category: Unset | str = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
]:
    """List all variants with negative stock

     Returns a list of variants with negative stock balance.
      Each variant has a date of the latest stock movement that resulted in negative stock balance.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        latest_negative_stock_date_max (Union[Unset, str]):
        latest_negative_stock_date_min (Union[Unset, str]):
        name (Union[Unset, str]):
        sku (Union[Unset, str]):
        category (Union[Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllNegativeStockResponse401, GetAllNegativeStockResponse429, GetAllNegativeStockResponse500, NegativeStockListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        latest_negative_stock_date_max=latest_negative_stock_date_max,
        latest_negative_stock_date_min=latest_negative_stock_date_min,
        name=name,
        sku=sku,
        category=category,
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
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    latest_negative_stock_date_max: Unset | str = UNSET,
    latest_negative_stock_date_min: Unset | str = UNSET,
    name: Unset | str = UNSET,
    sku: Unset | str = UNSET,
    category: Unset | str = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
    | None
):
    """List all variants with negative stock

     Returns a list of variants with negative stock balance.
      Each variant has a date of the latest stock movement that resulted in negative stock balance.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        latest_negative_stock_date_max (Union[Unset, str]):
        latest_negative_stock_date_min (Union[Unset, str]):
        name (Union[Unset, str]):
        sku (Union[Unset, str]):
        category (Union[Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllNegativeStockResponse401, GetAllNegativeStockResponse429, GetAllNegativeStockResponse500, NegativeStockListResponse]
    """

    return sync_detailed(
        client=client,
        location_id=location_id,
        variant_id=variant_id,
        latest_negative_stock_date_max=latest_negative_stock_date_max,
        latest_negative_stock_date_min=latest_negative_stock_date_min,
        name=name,
        sku=sku,
        category=category,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    latest_negative_stock_date_max: Unset | str = UNSET,
    latest_negative_stock_date_min: Unset | str = UNSET,
    name: Unset | str = UNSET,
    sku: Unset | str = UNSET,
    category: Unset | str = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
]:
    """List all variants with negative stock

     Returns a list of variants with negative stock balance.
      Each variant has a date of the latest stock movement that resulted in negative stock balance.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        latest_negative_stock_date_max (Union[Unset, str]):
        latest_negative_stock_date_min (Union[Unset, str]):
        name (Union[Unset, str]):
        sku (Union[Unset, str]):
        category (Union[Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllNegativeStockResponse401, GetAllNegativeStockResponse429, GetAllNegativeStockResponse500, NegativeStockListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        latest_negative_stock_date_max=latest_negative_stock_date_max,
        latest_negative_stock_date_min=latest_negative_stock_date_min,
        name=name,
        sku=sku,
        category=category,
        limit=limit,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    latest_negative_stock_date_max: Unset | str = UNSET,
    latest_negative_stock_date_min: Unset | str = UNSET,
    name: Unset | str = UNSET,
    sku: Unset | str = UNSET,
    category: Unset | str = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllNegativeStockResponse401
    | GetAllNegativeStockResponse429
    | GetAllNegativeStockResponse500
    | NegativeStockListResponse
    | None
):
    """List all variants with negative stock

     Returns a list of variants with negative stock balance.
      Each variant has a date of the latest stock movement that resulted in negative stock balance.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        latest_negative_stock_date_max (Union[Unset, str]):
        latest_negative_stock_date_min (Union[Unset, str]):
        name (Union[Unset, str]):
        sku (Union[Unset, str]):
        category (Union[Unset, str]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllNegativeStockResponse401, GetAllNegativeStockResponse429, GetAllNegativeStockResponse500, NegativeStockListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            location_id=location_id,
            variant_id=variant_id,
            latest_negative_stock_date_max=latest_negative_stock_date_max,
            latest_negative_stock_date_min=latest_negative_stock_date_min,
            name=name,
            sku=sku,
            category=category,
            limit=limit,
            page=page,
        )
    ).parsed
