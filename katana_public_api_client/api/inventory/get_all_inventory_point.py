from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_inventory_point_extend_item import GetAllInventoryPointExtendItem
from ...models.inventory_list_response import InventoryListResponse


def _get_kwargs(
    *,
    location_id: Unset | int = UNSET,
    variant_id: Unset | int = UNSET,
    include_archived: Unset | bool = UNSET,
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["location_id"] = location_id

    params["variant_id"] = variant_id

    params["include_archived"] = include_archived

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
) -> ErrorResponse | InventoryListResponse | None:
    if response.status_code == 200:
        response_200 = InventoryListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | InventoryListResponse]:
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
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[ErrorResponse | InventoryListResponse]:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, InventoryListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
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
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> ErrorResponse | InventoryListResponse | None:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, InventoryListResponse]
    """

    return sync_detailed(
        client=client,
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
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
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> Response[ErrorResponse | InventoryListResponse]:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, InventoryListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        variant_id=variant_id,
        include_archived=include_archived,
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
    extend: Unset | list[GetAllInventoryPointExtendItem] = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
) -> ErrorResponse | InventoryListResponse | None:
    """List current inventory

     Returns a list for current inventory. The inventory is returned in sorted order, with the oldest
    locations appearing first.

    Args:
        location_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):
        include_archived (Union[Unset, bool]):
        extend (Union[Unset, list[GetAllInventoryPointExtendItem]]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, InventoryListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            location_id=location_id,
            variant_id=variant_id,
            include_archived=include_archived,
            extend=extend,
            limit=limit,
            page=page,
        )
    ).parsed
