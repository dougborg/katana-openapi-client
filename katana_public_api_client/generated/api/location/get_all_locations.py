import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_locations_response_200 import GetAllLocationsResponse200
from ...models.get_all_locations_response_401 import GetAllLocationsResponse401
from ...models.get_all_locations_response_429 import GetAllLocationsResponse429
from ...models.get_all_locations_response_500 import GetAllLocationsResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    legal_name: Unset | str = UNSET,
    address_id: Unset | int = UNSET,
    sales_allowed: Unset | bool = UNSET,
    manufacturing_allowed: Unset | bool = UNSET,
    purchases_allowed: Unset | bool = UNSET,
    rank: Unset | int = UNSET,
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

    params["name"] = name

    params["legal_name"] = legal_name

    params["address_id"] = address_id

    params["sales_allowed"] = sales_allowed

    params["manufacturing_allowed"] = manufacturing_allowed

    params["purchases_allowed"] = purchases_allowed

    params["rank"] = rank

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
        "url": "/locations",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = GetAllLocationsResponse200.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllLocationsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllLocationsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllLocationsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
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
    name: Unset | str = UNSET,
    legal_name: Unset | str = UNSET,
    address_id: Unset | int = UNSET,
    sales_allowed: Unset | bool = UNSET,
    manufacturing_allowed: Unset | bool = UNSET,
    purchases_allowed: Unset | bool = UNSET,
    rank: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
]:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most recent locations appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        legal_name (Union[Unset, str]):
        address_id (Union[Unset, int]):
        sales_allowed (Union[Unset, bool]):
        manufacturing_allowed (Union[Unset, bool]):
        purchases_allowed (Union[Unset, bool]):
        rank (Union[Unset, int]):
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
        Response[Union[GetAllLocationsResponse200, GetAllLocationsResponse401, GetAllLocationsResponse429, GetAllLocationsResponse500]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        legal_name=legal_name,
        address_id=address_id,
        sales_allowed=sales_allowed,
        manufacturing_allowed=manufacturing_allowed,
        purchases_allowed=purchases_allowed,
        rank=rank,
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
    name: Unset | str = UNSET,
    legal_name: Unset | str = UNSET,
    address_id: Unset | int = UNSET,
    sales_allowed: Unset | bool = UNSET,
    manufacturing_allowed: Unset | bool = UNSET,
    purchases_allowed: Unset | bool = UNSET,
    rank: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
    | None
):
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most recent locations appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        legal_name (Union[Unset, str]):
        address_id (Union[Unset, int]):
        sales_allowed (Union[Unset, bool]):
        manufacturing_allowed (Union[Unset, bool]):
        purchases_allowed (Union[Unset, bool]):
        rank (Union[Unset, int]):
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
        Union[GetAllLocationsResponse200, GetAllLocationsResponse401, GetAllLocationsResponse429, GetAllLocationsResponse500]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        name=name,
        legal_name=legal_name,
        address_id=address_id,
        sales_allowed=sales_allowed,
        manufacturing_allowed=manufacturing_allowed,
        purchases_allowed=purchases_allowed,
        rank=rank,
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
    name: Unset | str = UNSET,
    legal_name: Unset | str = UNSET,
    address_id: Unset | int = UNSET,
    sales_allowed: Unset | bool = UNSET,
    manufacturing_allowed: Unset | bool = UNSET,
    purchases_allowed: Unset | bool = UNSET,
    rank: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
]:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most recent locations appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        legal_name (Union[Unset, str]):
        address_id (Union[Unset, int]):
        sales_allowed (Union[Unset, bool]):
        manufacturing_allowed (Union[Unset, bool]):
        purchases_allowed (Union[Unset, bool]):
        rank (Union[Unset, int]):
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
        Response[Union[GetAllLocationsResponse200, GetAllLocationsResponse401, GetAllLocationsResponse429, GetAllLocationsResponse500]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        legal_name=legal_name,
        address_id=address_id,
        sales_allowed=sales_allowed,
        manufacturing_allowed=manufacturing_allowed,
        purchases_allowed=purchases_allowed,
        rank=rank,
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
    name: Unset | str = UNSET,
    legal_name: Unset | str = UNSET,
    address_id: Unset | int = UNSET,
    sales_allowed: Unset | bool = UNSET,
    manufacturing_allowed: Unset | bool = UNSET,
    purchases_allowed: Unset | bool = UNSET,
    rank: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllLocationsResponse200
    | GetAllLocationsResponse401
    | GetAllLocationsResponse429
    | GetAllLocationsResponse500
    | None
):
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most recent locations appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        legal_name (Union[Unset, str]):
        address_id (Union[Unset, int]):
        sales_allowed (Union[Unset, bool]):
        manufacturing_allowed (Union[Unset, bool]):
        purchases_allowed (Union[Unset, bool]):
        rank (Union[Unset, int]):
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
        Union[GetAllLocationsResponse200, GetAllLocationsResponse401, GetAllLocationsResponse429, GetAllLocationsResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            name=name,
            legal_name=legal_name,
            address_id=address_id,
            sales_allowed=sales_allowed,
            manufacturing_allowed=manufacturing_allowed,
            purchases_allowed=purchases_allowed,
            rank=rank,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
