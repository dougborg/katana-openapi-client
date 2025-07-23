from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_stocktakes_response_401 import GetAllStocktakesResponse401
from ...models.get_all_stocktakes_response_429 import GetAllStocktakesResponse429
from ...models.get_all_stocktakes_response_500 import GetAllStocktakesResponse500
from ...models.get_all_stocktakes_status import GetAllStocktakesStatus
from ...models.stocktake_list_response import StocktakeListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllStocktakesStatus = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["location_id"] = location_id

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/stocktakes",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
    | None
):
    if response.status_code == 200:
        response_200 = StocktakeListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllStocktakesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllStocktakesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllStocktakesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
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
    location_id: Unset | int = UNSET,
    status: Unset | GetAllStocktakesStatus = UNSET,
) -> Response[
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
]:
    """List stocktakes

     Returns a list of stocktakes.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllStocktakesStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllStocktakesResponse401, GetAllStocktakesResponse429, GetAllStocktakesResponse500, StocktakeListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        location_id=location_id,
        status=status,
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
    location_id: Unset | int = UNSET,
    status: Unset | GetAllStocktakesStatus = UNSET,
) -> (
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
    | None
):
    """List stocktakes

     Returns a list of stocktakes.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllStocktakesStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllStocktakesResponse401, GetAllStocktakesResponse429, GetAllStocktakesResponse500, StocktakeListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        location_id=location_id,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllStocktakesStatus = UNSET,
) -> Response[
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
]:
    """List stocktakes

     Returns a list of stocktakes.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllStocktakesStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllStocktakesResponse401, GetAllStocktakesResponse429, GetAllStocktakesResponse500, StocktakeListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        location_id=location_id,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllStocktakesStatus = UNSET,
) -> (
    GetAllStocktakesResponse401
    | GetAllStocktakesResponse429
    | GetAllStocktakesResponse500
    | StocktakeListResponse
    | None
):
    """List stocktakes

     Returns a list of stocktakes.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllStocktakesStatus]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllStocktakesResponse401, GetAllStocktakesResponse429, GetAllStocktakesResponse500, StocktakeListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            location_id=location_id,
            status=status,
        )
    ).parsed
