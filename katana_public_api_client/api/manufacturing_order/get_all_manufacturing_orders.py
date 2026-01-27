import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_manufacturing_orders_status import (
    GetAllManufacturingOrdersStatus,
)
from ...models.manufacturing_order_list_response import ManufacturingOrderListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    status: GetAllManufacturingOrdersStatus | Unset = UNSET,
    order_no: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    is_linked_to_sales_order: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params["order_no"] = order_no

    params["location_id"] = location_id

    params["is_linked_to_sales_order"] = is_linked_to_sales_order

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

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/manufacturing_orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrderListResponse | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrderListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | ManufacturingOrderListResponse]:
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
    status: GetAllManufacturingOrdersStatus | Unset = UNSET,
    order_no: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    is_linked_to_sales_order: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> Response[ErrorResponse | ManufacturingOrderListResponse]:
    """List all manufacturing orders

     Returns a list of manufacturing orders you've previously created.
      The manufacturing orders are returned in sorted order, with the most recent manufacturing orders
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        status (GetAllManufacturingOrdersStatus | Unset):
        order_no (str | Unset):
        location_id (int | Unset):
        is_linked_to_sales_order (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | ManufacturingOrderListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        status=status,
        order_no=order_no,
        location_id=location_id,
        is_linked_to_sales_order=is_linked_to_sales_order,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    ids: list[int] | Unset = UNSET,
    status: GetAllManufacturingOrdersStatus | Unset = UNSET,
    order_no: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    is_linked_to_sales_order: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> ErrorResponse | ManufacturingOrderListResponse | None:
    """List all manufacturing orders

     Returns a list of manufacturing orders you've previously created.
      The manufacturing orders are returned in sorted order, with the most recent manufacturing orders
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        status (GetAllManufacturingOrdersStatus | Unset):
        order_no (str | Unset):
        location_id (int | Unset):
        is_linked_to_sales_order (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | ManufacturingOrderListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        status=status,
        order_no=order_no,
        location_id=location_id,
        is_linked_to_sales_order=is_linked_to_sales_order,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    ids: list[int] | Unset = UNSET,
    status: GetAllManufacturingOrdersStatus | Unset = UNSET,
    order_no: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    is_linked_to_sales_order: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> Response[ErrorResponse | ManufacturingOrderListResponse]:
    """List all manufacturing orders

     Returns a list of manufacturing orders you've previously created.
      The manufacturing orders are returned in sorted order, with the most recent manufacturing orders
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        status (GetAllManufacturingOrdersStatus | Unset):
        order_no (str | Unset):
        location_id (int | Unset):
        is_linked_to_sales_order (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | ManufacturingOrderListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        status=status,
        order_no=order_no,
        location_id=location_id,
        is_linked_to_sales_order=is_linked_to_sales_order,
        limit=limit,
        page=page,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    ids: list[int] | Unset = UNSET,
    status: GetAllManufacturingOrdersStatus | Unset = UNSET,
    order_no: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    is_linked_to_sales_order: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> ErrorResponse | ManufacturingOrderListResponse | None:
    """List all manufacturing orders

     Returns a list of manufacturing orders you've previously created.
      The manufacturing orders are returned in sorted order, with the most recent manufacturing orders
    appearing
      first.

    Args:
        ids (list[int] | Unset):
        status (GetAllManufacturingOrdersStatus | Unset):
        order_no (str | Unset):
        location_id (int | Unset):
        is_linked_to_sales_order (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | ManufacturingOrderListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            status=status,
            order_no=order_no,
            location_id=location_id,
            is_linked_to_sales_order=is_linked_to_sales_order,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            include_deleted=include_deleted,
        )
    ).parsed
