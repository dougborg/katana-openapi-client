from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_inventory_point_extend_item import GetAllInventoryPointExtendItem
from ...models.get_all_inventory_point_response_401 import (
    GetAllInventoryPointResponse401,
)
from ...models.get_all_inventory_point_response_429 import (
    GetAllInventoryPointResponse429,
)
from ...models.get_all_inventory_point_response_500 import (
    GetAllInventoryPointResponse500,
)
from ...models.inventory_list import InventoryList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    include_archived: Unset | bool = UNSET,
    ids: Unset | list[int] = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["location_id"] = location_id

    params["variant_id"] = variant_id

    params["include_archived"] = include_archived

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params["limit"] = limit

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/inventory",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
    | None
):
    if response.status_code == 200:
        response_200 = InventoryList.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllInventoryPointResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllInventoryPointResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllInventoryPointResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
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
    include_archived: Unset | bool = UNSET,
    ids: Unset | list[int] = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
]:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        ids (Union[Unset, list[int]]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllInventoryPointResponse401, GetAllInventoryPointResponse429, GetAllInventoryPointResponse500, InventoryList]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
        ids=ids,
        extend=extend,
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
    include_archived: Unset | bool = UNSET,
    ids: Unset | list[int] = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
    | None
):
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        ids (Union[Unset, list[int]]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllInventoryPointResponse401, GetAllInventoryPointResponse429, GetAllInventoryPointResponse500, InventoryList]
    """

    return sync_detailed(
        client=client,
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
        ids=ids,
        extend=extend,
        limit=limit,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    include_archived: Unset | bool = UNSET,
    ids: Unset | list[int] = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
]:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        ids (Union[Unset, list[int]]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllInventoryPointResponse401, GetAllInventoryPointResponse429, GetAllInventoryPointResponse500, InventoryList]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
        ids=ids,
        extend=extend,
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
    include_archived: Unset | bool = UNSET,
    ids: Unset | list[int] = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> (
    GetAllInventoryPointResponse401
    | GetAllInventoryPointResponse429
    | GetAllInventoryPointResponse500
    | InventoryList
    | None
):
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        ids (Union[Unset, list[int]]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllInventoryPointResponse401, GetAllInventoryPointResponse429, GetAllInventoryPointResponse500, InventoryList]
    """

    return (
        await asyncio_detailed(
            client=client,
            location_id=location_id,
            variant_id=variant_id,
            include_archived=include_archived,
            ids=ids,
            extend=extend,
            limit=limit,
            page=page,
        )
    ).parsed
