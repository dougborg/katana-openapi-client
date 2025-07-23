from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_price_list_rows_response_401 import (
    GetAllPriceListRowsResponse401,
)
from ...models.get_all_price_list_rows_response_429 import (
    GetAllPriceListRowsResponse429,
)
from ...models.get_all_price_list_rows_response_500 import (
    GetAllPriceListRowsResponse500,
)
from ...models.price_list_row_list_response import PriceListRowListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["price_list_id"] = price_list_id

    params["variant_id"] = variant_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/price_list_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
    | None
):
    if response.status_code == 200:
        response_200 = PriceListRowListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllPriceListRowsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllPriceListRowsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllPriceListRowsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
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
    price_list_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
) -> Response[
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
]:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPriceListRowsResponse401, GetAllPriceListRowsResponse429, GetAllPriceListRowsResponse500, PriceListRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        price_list_id=price_list_id,
        variant_id=variant_id,
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
    price_list_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
) -> (
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
    | None
):
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPriceListRowsResponse401, GetAllPriceListRowsResponse429, GetAllPriceListRowsResponse500, PriceListRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        price_list_id=price_list_id,
        variant_id=variant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
) -> Response[
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
]:
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllPriceListRowsResponse401, GetAllPriceListRowsResponse429, GetAllPriceListRowsResponse500, PriceListRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        price_list_id=price_list_id,
        variant_id=variant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    price_list_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
) -> (
    GetAllPriceListRowsResponse401
    | GetAllPriceListRowsResponse429
    | GetAllPriceListRowsResponse500
    | PriceListRowListResponse
    | None
):
    """List price list rows

     Returns a list of price list rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        price_list_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllPriceListRowsResponse401, GetAllPriceListRowsResponse429, GetAllPriceListRowsResponse500, PriceListRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            price_list_id=price_list_id,
            variant_id=variant_id,
        )
    ).parsed
