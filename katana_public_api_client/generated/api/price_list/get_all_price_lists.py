from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_price_lists_response_401 import GetAllPriceListsResponse401
from ...models.get_all_price_lists_response_429 import GetAllPriceListsResponse429
from ...models.get_all_price_lists_response_500 import GetAllPriceListsResponse500
from ...models.price_list_list_response import PriceListListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    name: Union[Unset, str] = UNSET,
    currency: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["name"] = name

    params["currency"] = currency

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/price_lists",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    if response.status_code == 200:
        response_200 = PriceListListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllPriceListsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllPriceListsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllPriceListsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    name: Union[Unset, str] = UNSET,
    currency: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Response[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    """List price lists

     Returns a list of price lists.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        currency (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllPriceListsResponse401, GetAllPriceListsResponse429, GetAllPriceListsResponse500, PriceListListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        currency=currency,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    name: Union[Unset, str] = UNSET,
    currency: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Optional[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    """List price lists

     Returns a list of price lists.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        currency (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllPriceListsResponse401, GetAllPriceListsResponse429, GetAllPriceListsResponse500, PriceListListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        currency=currency,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    name: Union[Unset, str] = UNSET,
    currency: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Response[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    """List price lists

     Returns a list of price lists.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        currency (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllPriceListsResponse401, GetAllPriceListsResponse429, GetAllPriceListsResponse500, PriceListListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        currency=currency,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    name: Union[Unset, str] = UNSET,
    currency: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
) -> Optional[
    Union[
        GetAllPriceListsResponse401,
        GetAllPriceListsResponse429,
        GetAllPriceListsResponse500,
        PriceListListResponse,
    ]
]:
    """List price lists

     Returns a list of price lists.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        currency (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllPriceListsResponse401, GetAllPriceListsResponse429, GetAllPriceListsResponse500, PriceListListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            name=name,
            currency=currency,
            include_deleted=include_deleted,
        )
    ).parsed
