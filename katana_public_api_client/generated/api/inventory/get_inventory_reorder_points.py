from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.inventory_reorder_point_list_response import InventoryReorderPointListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    variant_ids: Union[Unset, list[int]] = UNSET,
    location_ids: Union[Unset, list[int]] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_variant_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(variant_ids, Unset):
        json_variant_ids = variant_ids

    params["variant_ids"] = json_variant_ids

    json_location_ids: Union[Unset, list[int]] = UNSET
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, InventoryReorderPointListResponse]]:
    if response.status_code == 200:
        response_200 = InventoryReorderPointListResponse.from_dict(response.json())

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, InventoryReorderPointListResponse]]:
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
    variant_ids: Union[Unset, list[int]] = UNSET,
    location_ids: Union[Unset, list[int]] = UNSET,
) -> Response[Union[ErrorResponse, InventoryReorderPointListResponse]]:
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
        Response[Union[ErrorResponse, InventoryReorderPointListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    variant_ids: Union[Unset, list[int]] = UNSET,
    location_ids: Union[Unset, list[int]] = UNSET,
) -> Optional[Union[ErrorResponse, InventoryReorderPointListResponse]]:
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
        Union[ErrorResponse, InventoryReorderPointListResponse]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    variant_ids: Union[Unset, list[int]] = UNSET,
    location_ids: Union[Unset, list[int]] = UNSET,
) -> Response[Union[ErrorResponse, InventoryReorderPointListResponse]]:
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
        Response[Union[ErrorResponse, InventoryReorderPointListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    variant_ids: Union[Unset, list[int]] = UNSET,
    location_ids: Union[Unset, list[int]] = UNSET,
) -> Optional[Union[ErrorResponse, InventoryReorderPointListResponse]]:
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
        Union[ErrorResponse, InventoryReorderPointListResponse]
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
