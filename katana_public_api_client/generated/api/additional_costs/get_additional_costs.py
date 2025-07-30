import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.additional_cost_list_response import AdditionalCostListResponse
from ...models.get_additional_costs_response_401 import GetAdditionalCostsResponse401
from ...models.get_additional_costs_response_429 import GetAdditionalCostsResponse429
from ...models.get_additional_costs_response_500 import GetAdditionalCostsResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

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

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["name"] = name

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/additional_costs",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
    | None
):
    if response.status_code == 200:
        response_200 = AdditionalCostListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAdditionalCostsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAdditionalCostsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAdditionalCostsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
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
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
]:
    """List all additional costs

     Returns a list of additional costs you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[AdditionalCostListResponse, GetAdditionalCostsResponse401, GetAdditionalCostsResponse429, GetAdditionalCostsResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ids=ids,
        name=name,
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
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
    | None
):
    """List all additional costs

     Returns a list of additional costs you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[AdditionalCostListResponse, GetAdditionalCostsResponse401, GetAdditionalCostsResponse429, GetAdditionalCostsResponse500]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ids=ids,
        name=name,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
]:
    """List all additional costs

     Returns a list of additional costs you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[AdditionalCostListResponse, GetAdditionalCostsResponse401, GetAdditionalCostsResponse429, GetAdditionalCostsResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        ids=ids,
        name=name,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    AdditionalCostListResponse
    | GetAdditionalCostsResponse401
    | GetAdditionalCostsResponse429
    | GetAdditionalCostsResponse500
    | None
):
    """List all additional costs

     Returns a list of additional costs you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[AdditionalCostListResponse, GetAdditionalCostsResponse401, GetAdditionalCostsResponse429, GetAdditionalCostsResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            ids=ids,
            name=name,
            include_deleted=include_deleted,
        )
    ).parsed
