import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.find_purchase_orders_billing_status import (
    FindPurchaseOrdersBillingStatus,
)
from ...models.find_purchase_orders_entity_type import FindPurchaseOrdersEntityType
from ...models.find_purchase_orders_extend_item import FindPurchaseOrdersExtendItem
from ...models.find_purchase_orders_status import FindPurchaseOrdersStatus
from ...models.purchase_order_list_response import PurchaseOrderListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    order_no: str | Unset = UNSET,
    entity_type: FindPurchaseOrdersEntityType | Unset = UNSET,
    status: FindPurchaseOrdersStatus | Unset = UNSET,
    billing_status: FindPurchaseOrdersBillingStatus | Unset = UNSET,
    currency: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tracking_location_id: float | Unset = UNSET,
    supplier_id: float | Unset = UNSET,
    extend: list[FindPurchaseOrdersExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
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

    params["order_no"] = order_no

    json_entity_type: str | Unset = UNSET
    if not isinstance(entity_type, Unset):
        json_entity_type = entity_type.value

    params["entity_type"] = json_entity_type

    json_status: str | Unset = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    json_billing_status: str | Unset = UNSET
    if not isinstance(billing_status, Unset):
        json_billing_status = billing_status.value

    params["billing_status"] = json_billing_status

    params["currency"] = currency

    params["location_id"] = location_id

    params["tracking_location_id"] = tracking_location_id

    params["supplier_id"] = supplier_id

    json_extend: list[str] | Unset = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

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
        "url": "/purchase_orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | PurchaseOrderListResponse | None:
    if response.status_code == 200:
        response_200 = PurchaseOrderListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | PurchaseOrderListResponse]:
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
    order_no: str | Unset = UNSET,
    entity_type: FindPurchaseOrdersEntityType | Unset = UNSET,
    status: FindPurchaseOrdersStatus | Unset = UNSET,
    billing_status: FindPurchaseOrdersBillingStatus | Unset = UNSET,
    currency: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tracking_location_id: float | Unset = UNSET,
    supplier_id: float | Unset = UNSET,
    extend: list[FindPurchaseOrdersExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | PurchaseOrderListResponse]:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (list[int] | Unset):
        order_no (str | Unset):
        entity_type (FindPurchaseOrdersEntityType | Unset):
        status (FindPurchaseOrdersStatus | Unset):
        billing_status (FindPurchaseOrdersBillingStatus | Unset):
        currency (str | Unset):
        location_id (int | Unset):
        tracking_location_id (float | Unset):
        supplier_id (float | Unset):
        extend (list[FindPurchaseOrdersExtendItem] | Unset):
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
        Response[ErrorResponse | PurchaseOrderListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        order_no=order_no,
        entity_type=entity_type,
        status=status,
        billing_status=billing_status,
        currency=currency,
        location_id=location_id,
        tracking_location_id=tracking_location_id,
        supplier_id=supplier_id,
        extend=extend,
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
    order_no: str | Unset = UNSET,
    entity_type: FindPurchaseOrdersEntityType | Unset = UNSET,
    status: FindPurchaseOrdersStatus | Unset = UNSET,
    billing_status: FindPurchaseOrdersBillingStatus | Unset = UNSET,
    currency: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tracking_location_id: float | Unset = UNSET,
    supplier_id: float | Unset = UNSET,
    extend: list[FindPurchaseOrdersExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | PurchaseOrderListResponse | None:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (list[int] | Unset):
        order_no (str | Unset):
        entity_type (FindPurchaseOrdersEntityType | Unset):
        status (FindPurchaseOrdersStatus | Unset):
        billing_status (FindPurchaseOrdersBillingStatus | Unset):
        currency (str | Unset):
        location_id (int | Unset):
        tracking_location_id (float | Unset):
        supplier_id (float | Unset):
        extend (list[FindPurchaseOrdersExtendItem] | Unset):
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
        ErrorResponse | PurchaseOrderListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        order_no=order_no,
        entity_type=entity_type,
        status=status,
        billing_status=billing_status,
        currency=currency,
        location_id=location_id,
        tracking_location_id=tracking_location_id,
        supplier_id=supplier_id,
        extend=extend,
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
    order_no: str | Unset = UNSET,
    entity_type: FindPurchaseOrdersEntityType | Unset = UNSET,
    status: FindPurchaseOrdersStatus | Unset = UNSET,
    billing_status: FindPurchaseOrdersBillingStatus | Unset = UNSET,
    currency: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tracking_location_id: float | Unset = UNSET,
    supplier_id: float | Unset = UNSET,
    extend: list[FindPurchaseOrdersExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | PurchaseOrderListResponse]:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (list[int] | Unset):
        order_no (str | Unset):
        entity_type (FindPurchaseOrdersEntityType | Unset):
        status (FindPurchaseOrdersStatus | Unset):
        billing_status (FindPurchaseOrdersBillingStatus | Unset):
        currency (str | Unset):
        location_id (int | Unset):
        tracking_location_id (float | Unset):
        supplier_id (float | Unset):
        extend (list[FindPurchaseOrdersExtendItem] | Unset):
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
        Response[ErrorResponse | PurchaseOrderListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        order_no=order_no,
        entity_type=entity_type,
        status=status,
        billing_status=billing_status,
        currency=currency,
        location_id=location_id,
        tracking_location_id=tracking_location_id,
        supplier_id=supplier_id,
        extend=extend,
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
    order_no: str | Unset = UNSET,
    entity_type: FindPurchaseOrdersEntityType | Unset = UNSET,
    status: FindPurchaseOrdersStatus | Unset = UNSET,
    billing_status: FindPurchaseOrdersBillingStatus | Unset = UNSET,
    currency: str | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tracking_location_id: float | Unset = UNSET,
    supplier_id: float | Unset = UNSET,
    extend: list[FindPurchaseOrdersExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | PurchaseOrderListResponse | None:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (list[int] | Unset):
        order_no (str | Unset):
        entity_type (FindPurchaseOrdersEntityType | Unset):
        status (FindPurchaseOrdersStatus | Unset):
        billing_status (FindPurchaseOrdersBillingStatus | Unset):
        currency (str | Unset):
        location_id (int | Unset):
        tracking_location_id (float | Unset):
        supplier_id (float | Unset):
        extend (list[FindPurchaseOrdersExtendItem] | Unset):
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
        ErrorResponse | PurchaseOrderListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            order_no=order_no,
            entity_type=entity_type,
            status=status,
            billing_status=billing_status,
            currency=currency,
            location_id=location_id,
            tracking_location_id=tracking_location_id,
            supplier_id=supplier_id,
            extend=extend,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
