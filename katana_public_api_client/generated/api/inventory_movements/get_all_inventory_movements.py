import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_inventory_movements_resource_type import (
    GetAllInventoryMovementsResourceType,
)
from ...models.get_all_inventory_movements_response_401 import (
    GetAllInventoryMovementsResponse401,
)
from ...models.get_all_inventory_movements_response_429 import (
    GetAllInventoryMovementsResponse429,
)
from ...models.get_all_inventory_movements_response_500 import (
    GetAllInventoryMovementsResponse500,
)
from ...models.inventory_movement_list_response import InventoryMovementListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    variant_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    resource_type: Unset | GetAllInventoryMovementsResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    caused_by_order_no: Unset | str = UNSET,
    caused_by_resource_id: Unset | int = UNSET,
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

    json_variant_ids: Unset | list[int] = UNSET
    if not isinstance(variant_ids, Unset):
        json_variant_ids = variant_ids

    params["variant_ids"] = json_variant_ids

    params["location_id"] = location_id

    json_resource_type: Unset | str = UNSET
    if not isinstance(resource_type, Unset):
        json_resource_type = resource_type.value

    params["resource_type"] = json_resource_type

    params["resource_id"] = resource_id

    params["caused_by_order_no"] = caused_by_order_no

    params["caused_by_resource_id"] = caused_by_resource_id

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
        "url": "/inventory_movements",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
    | None
):
    if response.status_code == 200:
        response_200 = InventoryMovementListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllInventoryMovementsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllInventoryMovementsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllInventoryMovementsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
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
    variant_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    resource_type: Unset | GetAllInventoryMovementsResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    caused_by_order_no: Unset | str = UNSET,
    caused_by_resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
]:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in sorted order, with the most recent movements appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        resource_type (Union[Unset, GetAllInventoryMovementsResourceType]):
        resource_id (Union[Unset, int]):
        caused_by_order_no (Union[Unset, str]):
        caused_by_resource_id (Union[Unset, int]):
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
        Response[Union[GetAllInventoryMovementsResponse401, GetAllInventoryMovementsResponse429, GetAllInventoryMovementsResponse500, InventoryMovementListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        variant_ids=variant_ids,
        location_id=location_id,
        resource_type=resource_type,
        resource_id=resource_id,
        caused_by_order_no=caused_by_order_no,
        caused_by_resource_id=caused_by_resource_id,
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
    variant_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    resource_type: Unset | GetAllInventoryMovementsResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    caused_by_order_no: Unset | str = UNSET,
    caused_by_resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
    | None
):
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in sorted order, with the most recent movements appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        resource_type (Union[Unset, GetAllInventoryMovementsResourceType]):
        resource_id (Union[Unset, int]):
        caused_by_order_no (Union[Unset, str]):
        caused_by_resource_id (Union[Unset, int]):
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
        Union[GetAllInventoryMovementsResponse401, GetAllInventoryMovementsResponse429, GetAllInventoryMovementsResponse500, InventoryMovementListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        variant_ids=variant_ids,
        location_id=location_id,
        resource_type=resource_type,
        resource_id=resource_id,
        caused_by_order_no=caused_by_order_no,
        caused_by_resource_id=caused_by_resource_id,
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
    variant_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    resource_type: Unset | GetAllInventoryMovementsResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    caused_by_order_no: Unset | str = UNSET,
    caused_by_resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
]:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in sorted order, with the most recent movements appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        resource_type (Union[Unset, GetAllInventoryMovementsResourceType]):
        resource_id (Union[Unset, int]):
        caused_by_order_no (Union[Unset, str]):
        caused_by_resource_id (Union[Unset, int]):
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
        Response[Union[GetAllInventoryMovementsResponse401, GetAllInventoryMovementsResponse429, GetAllInventoryMovementsResponse500, InventoryMovementListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        variant_ids=variant_ids,
        location_id=location_id,
        resource_type=resource_type,
        resource_id=resource_id,
        caused_by_order_no=caused_by_order_no,
        caused_by_resource_id=caused_by_resource_id,
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
    variant_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    resource_type: Unset | GetAllInventoryMovementsResourceType = UNSET,
    resource_id: Unset | int = UNSET,
    caused_by_order_no: Unset | str = UNSET,
    caused_by_resource_id: Unset | int = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllInventoryMovementsResponse401
    | GetAllInventoryMovementsResponse429
    | GetAllInventoryMovementsResponse500
    | InventoryMovementListResponse
    | None
):
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in sorted order, with the most recent movements appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        variant_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        resource_type (Union[Unset, GetAllInventoryMovementsResourceType]):
        resource_id (Union[Unset, int]):
        caused_by_order_no (Union[Unset, str]):
        caused_by_resource_id (Union[Unset, int]):
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
        Union[GetAllInventoryMovementsResponse401, GetAllInventoryMovementsResponse429, GetAllInventoryMovementsResponse500, InventoryMovementListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            variant_ids=variant_ids,
            location_id=location_id,
            resource_type=resource_type,
            resource_id=resource_id,
            caused_by_order_no=caused_by_order_no,
            caused_by_resource_id=caused_by_resource_id,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
