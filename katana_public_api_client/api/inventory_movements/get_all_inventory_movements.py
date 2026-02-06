import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_inventory_movements_resource_type import (
    GetAllInventoryMovementsResourceType,
)
from ...models.inventory_movement_list_response import InventoryMovementListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    variant_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    resource_type: GetAllInventoryMovementsResourceType | Unset = UNSET,
    resource_id: int | Unset = UNSET,
    caused_by_order_no: str | Unset = UNSET,
    caused_by_resource_id: int | Unset = UNSET,
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

    json_variant_ids: list[int] | Unset = UNSET
    if not isinstance(variant_ids, Unset):
        json_variant_ids = variant_ids

    params["variant_ids"] = json_variant_ids

    params["location_id"] = location_id

    json_resource_type: str | Unset = UNSET
    if not isinstance(resource_type, Unset):
        json_resource_type = resource_type.value

    params["resource_type"] = json_resource_type

    params["resource_id"] = resource_id

    params["caused_by_order_no"] = caused_by_order_no

    params["caused_by_resource_id"] = caused_by_resource_id

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
        "url": "/inventory_movements",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | InventoryMovementListResponse | None:
    if response.status_code == 200:
        response_200 = InventoryMovementListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | InventoryMovementListResponse]:
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
    variant_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    resource_type: GetAllInventoryMovementsResourceType | Unset = UNSET,
    resource_id: int | Unset = UNSET,
    caused_by_order_no: str | Unset = UNSET,
    caused_by_resource_id: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | InventoryMovementListResponse]:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in
    sorted order, with the most recent movements appearing first.

    Args:
        ids (list[int] | Unset):
        variant_ids (list[int] | Unset):
        location_id (int | Unset):
        resource_type (GetAllInventoryMovementsResourceType | Unset):
        resource_id (int | Unset):
        caused_by_order_no (str | Unset):
        caused_by_resource_id (int | Unset):
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
        Response[ErrorResponse | InventoryMovementListResponse]
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
    ids: list[int] | Unset = UNSET,
    variant_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    resource_type: GetAllInventoryMovementsResourceType | Unset = UNSET,
    resource_id: int | Unset = UNSET,
    caused_by_order_no: str | Unset = UNSET,
    caused_by_resource_id: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | InventoryMovementListResponse | None:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in
    sorted order, with the most recent movements appearing first.

    Args:
        ids (list[int] | Unset):
        variant_ids (list[int] | Unset):
        location_id (int | Unset):
        resource_type (GetAllInventoryMovementsResourceType | Unset):
        resource_id (int | Unset):
        caused_by_order_no (str | Unset):
        caused_by_resource_id (int | Unset):
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
        ErrorResponse | InventoryMovementListResponse
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
    ids: list[int] | Unset = UNSET,
    variant_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    resource_type: GetAllInventoryMovementsResourceType | Unset = UNSET,
    resource_id: int | Unset = UNSET,
    caused_by_order_no: str | Unset = UNSET,
    caused_by_resource_id: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | InventoryMovementListResponse]:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in
    sorted order, with the most recent movements appearing first.

    Args:
        ids (list[int] | Unset):
        variant_ids (list[int] | Unset):
        location_id (int | Unset):
        resource_type (GetAllInventoryMovementsResourceType | Unset):
        resource_id (int | Unset):
        caused_by_order_no (str | Unset):
        caused_by_resource_id (int | Unset):
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
        Response[ErrorResponse | InventoryMovementListResponse]
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
    ids: list[int] | Unset = UNSET,
    variant_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    resource_type: GetAllInventoryMovementsResourceType | Unset = UNSET,
    resource_id: int | Unset = UNSET,
    caused_by_order_no: str | Unset = UNSET,
    caused_by_resource_id: int | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | InventoryMovementListResponse | None:
    """List all inventory movements

     Returns a list of inventory movements created by your Katana resources. The inventory movements are
    returned in
    sorted order, with the most recent movements appearing first.

    Args:
        ids (list[int] | Unset):
        variant_ids (list[int] | Unset):
        location_id (int | Unset):
        resource_type (GetAllInventoryMovementsResourceType | Unset):
        resource_id (int | Unset):
        caused_by_order_no (str | Unset):
        caused_by_resource_id (int | Unset):
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
        ErrorResponse | InventoryMovementListResponse
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
