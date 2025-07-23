from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_inventory_reorder_points_response_401 import (
    GetInventoryReorderPointsResponse401,
)
from ...models.get_inventory_reorder_points_response_429 import (
    GetInventoryReorderPointsResponse429,
)
from ...models.get_inventory_reorder_points_response_500 import (
    GetInventoryReorderPointsResponse500,
)
from ...models.inventory_reorder_point_list_response import (
    InventoryReorderPointListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_ids: Unset | list[int] = UNSET,
    location_ids: Unset | list[int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_variant_ids: Unset | list[int] = UNSET
    if not isinstance(variant_ids, Unset):
        json_variant_ids = variant_ids

    params["variant_ids"] = json_variant_ids

    json_location_ids: Unset | list[int] = UNSET
    if not isinstance(location_ids, Unset):
        json_location_ids = location_ids

    params["location_ids"] = json_location_ids

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/inventory_reorder_points",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
    | None
):
    if response.status_code == 200:
        response_200 = InventoryReorderPointListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetInventoryReorderPointsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetInventoryReorderPointsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetInventoryReorderPointsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
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
    variant_ids: Unset | list[int] = UNSET,
    location_ids: Unset | list[int] = UNSET,
) -> Response[
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
]:
    """List all inventory reorder points

     Retrieves a list of inventory reorder points.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_ids (Union[Unset, list[int]]):
        location_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetInventoryReorderPointsResponse401, GetInventoryReorderPointsResponse429, GetInventoryReorderPointsResponse500, InventoryReorderPointListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_ids=variant_ids,
        location_ids=location_ids,
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
    variant_ids: Unset | list[int] = UNSET,
    location_ids: Unset | list[int] = UNSET,
) -> (
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
    | None
):
    """List all inventory reorder points

     Retrieves a list of inventory reorder points.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_ids (Union[Unset, list[int]]):
        location_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetInventoryReorderPointsResponse401, GetInventoryReorderPointsResponse429, GetInventoryReorderPointsResponse500, InventoryReorderPointListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        variant_ids=variant_ids,
        location_ids=location_ids,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_ids: Unset | list[int] = UNSET,
    location_ids: Unset | list[int] = UNSET,
) -> Response[
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
]:
    """List all inventory reorder points

     Retrieves a list of inventory reorder points.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_ids (Union[Unset, list[int]]):
        location_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetInventoryReorderPointsResponse401, GetInventoryReorderPointsResponse429, GetInventoryReorderPointsResponse500, InventoryReorderPointListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_ids=variant_ids,
        location_ids=location_ids,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_ids: Unset | list[int] = UNSET,
    location_ids: Unset | list[int] = UNSET,
) -> (
    GetInventoryReorderPointsResponse401
    | GetInventoryReorderPointsResponse429
    | GetInventoryReorderPointsResponse500
    | InventoryReorderPointListResponse
    | None
):
    """List all inventory reorder points

     Retrieves a list of inventory reorder points.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_ids (Union[Unset, list[int]]):
        location_ids (Union[Unset, list[int]]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetInventoryReorderPointsResponse401, GetInventoryReorderPointsResponse429, GetInventoryReorderPointsResponse500, InventoryReorderPointListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            variant_ids=variant_ids,
            location_ids=location_ids,
        )
    ).parsed
