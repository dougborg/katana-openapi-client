import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.location_list_response import LocationListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    legal_name: str | Unset = UNSET,
    address_id: int | Unset = UNSET,
    sales_allowed: bool | Unset = UNSET,
    manufacturing_allowed: bool | Unset = UNSET,
    purchases_allowed: bool | Unset = UNSET,
    rank: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: list[int] | Unset = UNSET
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

    json_created_at_min: str | Unset = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: str | Unset = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: str | Unset = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: str | Unset = UNSET
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
) -> ErrorResponse | LocationListResponse | None:
    if response.status_code == 200:
        response_200 = LocationListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | LocationListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    legal_name: str | Unset = UNSET,
    address_id: int | Unset = UNSET,
    sales_allowed: bool | Unset = UNSET,
    manufacturing_allowed: bool | Unset = UNSET,
    purchases_allowed: bool | Unset = UNSET,
    rank: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | LocationListResponse]:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most
    recent locations appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        legal_name (str | Unset):
        address_id (int | Unset):
        sales_allowed (bool | Unset):
        manufacturing_allowed (bool | Unset):
        purchases_allowed (bool | Unset):
        rank (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | LocationListResponse]
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    legal_name: str | Unset = UNSET,
    address_id: int | Unset = UNSET,
    sales_allowed: bool | Unset = UNSET,
    manufacturing_allowed: bool | Unset = UNSET,
    purchases_allowed: bool | Unset = UNSET,
    rank: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | LocationListResponse | None:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most
    recent locations appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        legal_name (str | Unset):
        address_id (int | Unset):
        sales_allowed (bool | Unset):
        manufacturing_allowed (bool | Unset):
        purchases_allowed (bool | Unset):
        rank (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | LocationListResponse
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    legal_name: str | Unset = UNSET,
    address_id: int | Unset = UNSET,
    sales_allowed: bool | Unset = UNSET,
    manufacturing_allowed: bool | Unset = UNSET,
    purchases_allowed: bool | Unset = UNSET,
    rank: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | LocationListResponse]:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most
    recent locations appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        legal_name (str | Unset):
        address_id (int | Unset):
        sales_allowed (bool | Unset):
        manufacturing_allowed (bool | Unset):
        purchases_allowed (bool | Unset):
        rank (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | LocationListResponse]
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
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    legal_name: str | Unset = UNSET,
    address_id: int | Unset = UNSET,
    sales_allowed: bool | Unset = UNSET,
    manufacturing_allowed: bool | Unset = UNSET,
    purchases_allowed: bool | Unset = UNSET,
    rank: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | LocationListResponse | None:
    """List all locations

     Returns a list of locations you've previously created. The locations are returned in sorted order,
    with the most
    recent locations appearing first.

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        legal_name (str | Unset):
        address_id (int | Unset):
        sales_allowed (bool | Unset):
        manufacturing_allowed (bool | Unset):
        purchases_allowed (bool | Unset):
        rank (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | LocationListResponse
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
