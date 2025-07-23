import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.find_purchase_orders_billing_status import (
    FindPurchaseOrdersBillingStatus,
)
from ...models.find_purchase_orders_entity_type import FindPurchaseOrdersEntityType
from ...models.find_purchase_orders_extend_item import FindPurchaseOrdersExtendItem
from ...models.find_purchase_orders_response_401 import FindPurchaseOrdersResponse401
from ...models.find_purchase_orders_response_429 import FindPurchaseOrdersResponse429
from ...models.find_purchase_orders_response_500 import FindPurchaseOrdersResponse500
from ...models.find_purchase_orders_status import FindPurchaseOrdersStatus
from ...models.purchase_order_list_response import PurchaseOrderListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    entity_type: Unset | FindPurchaseOrdersEntityType = UNSET,
    status: Unset | FindPurchaseOrdersStatus = UNSET,
    billing_status: Unset | FindPurchaseOrdersBillingStatus = UNSET,
    currency: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    tracking_location_id: Unset | float = UNSET,
    supplier_id: Unset | float = UNSET,
    extend: Unset | list[FindPurchaseOrdersExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
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

    params["order_no"] = order_no

    json_entity_type: Unset | str = UNSET
    if not isinstance(entity_type, Unset):
        json_entity_type = entity_type.value

    params["entity_type"] = json_entity_type

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    json_billing_status: Unset | str = UNSET
    if not isinstance(billing_status, Unset):
        json_billing_status = billing_status.value

    params["billing_status"] = json_billing_status

    params["currency"] = currency

    params["location_id"] = location_id

    params["tracking_location_id"] = tracking_location_id

    params["supplier_id"] = supplier_id

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params["include_deleted"] = include_deleted

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
        "url": "/purchase_orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
    | None
):
    if response.status_code == 200:
        response_200 = PurchaseOrderListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = FindPurchaseOrdersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = FindPurchaseOrdersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = FindPurchaseOrdersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
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
    order_no: Unset | str = UNSET,
    entity_type: Unset | FindPurchaseOrdersEntityType = UNSET,
    status: Unset | FindPurchaseOrdersStatus = UNSET,
    billing_status: Unset | FindPurchaseOrdersBillingStatus = UNSET,
    currency: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    tracking_location_id: Unset | float = UNSET,
    supplier_id: Unset | float = UNSET,
    extend: Unset | list[FindPurchaseOrdersExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
]:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        entity_type (Union[Unset, FindPurchaseOrdersEntityType]):
        status (Union[Unset, FindPurchaseOrdersStatus]):
        billing_status (Union[Unset, FindPurchaseOrdersBillingStatus]):
        currency (Union[Unset, str]):
        location_id (Union[Unset, int]):
        tracking_location_id (Union[Unset, float]):
        supplier_id (Union[Unset, float]):
        extend (Union[Unset, list[FindPurchaseOrdersExtendItem]]):
        include_deleted (Union[Unset, bool]):
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
        Response[Union[FindPurchaseOrdersResponse401, FindPurchaseOrdersResponse429, FindPurchaseOrdersResponse500, PurchaseOrderListResponse]]
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
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    entity_type: Unset | FindPurchaseOrdersEntityType = UNSET,
    status: Unset | FindPurchaseOrdersStatus = UNSET,
    billing_status: Unset | FindPurchaseOrdersBillingStatus = UNSET,
    currency: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    tracking_location_id: Unset | float = UNSET,
    supplier_id: Unset | float = UNSET,
    extend: Unset | list[FindPurchaseOrdersExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
    | None
):
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        entity_type (Union[Unset, FindPurchaseOrdersEntityType]):
        status (Union[Unset, FindPurchaseOrdersStatus]):
        billing_status (Union[Unset, FindPurchaseOrdersBillingStatus]):
        currency (Union[Unset, str]):
        location_id (Union[Unset, int]):
        tracking_location_id (Union[Unset, float]):
        supplier_id (Union[Unset, float]):
        extend (Union[Unset, list[FindPurchaseOrdersExtendItem]]):
        include_deleted (Union[Unset, bool]):
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
        Union[FindPurchaseOrdersResponse401, FindPurchaseOrdersResponse429, FindPurchaseOrdersResponse500, PurchaseOrderListResponse]
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
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    entity_type: Unset | FindPurchaseOrdersEntityType = UNSET,
    status: Unset | FindPurchaseOrdersStatus = UNSET,
    billing_status: Unset | FindPurchaseOrdersBillingStatus = UNSET,
    currency: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    tracking_location_id: Unset | float = UNSET,
    supplier_id: Unset | float = UNSET,
    extend: Unset | list[FindPurchaseOrdersExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
]:
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        entity_type (Union[Unset, FindPurchaseOrdersEntityType]):
        status (Union[Unset, FindPurchaseOrdersStatus]):
        billing_status (Union[Unset, FindPurchaseOrdersBillingStatus]):
        currency (Union[Unset, str]):
        location_id (Union[Unset, int]):
        tracking_location_id (Union[Unset, float]):
        supplier_id (Union[Unset, float]):
        extend (Union[Unset, list[FindPurchaseOrdersExtendItem]]):
        include_deleted (Union[Unset, bool]):
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
        Response[Union[FindPurchaseOrdersResponse401, FindPurchaseOrdersResponse429, FindPurchaseOrdersResponse500, PurchaseOrderListResponse]]
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
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    entity_type: Unset | FindPurchaseOrdersEntityType = UNSET,
    status: Unset | FindPurchaseOrdersStatus = UNSET,
    billing_status: Unset | FindPurchaseOrdersBillingStatus = UNSET,
    currency: Unset | str = UNSET,
    location_id: Unset | int = UNSET,
    tracking_location_id: Unset | float = UNSET,
    supplier_id: Unset | float = UNSET,
    extend: Unset | list[FindPurchaseOrdersExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    FindPurchaseOrdersResponse401
    | FindPurchaseOrdersResponse429
    | FindPurchaseOrdersResponse500
    | PurchaseOrderListResponse
    | None
):
    """List all purchase orders

     Returns a list of purchase orders you've previously created. The purchase orders are returned in
    sorted
        order, with the most recent purchase orders appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        entity_type (Union[Unset, FindPurchaseOrdersEntityType]):
        status (Union[Unset, FindPurchaseOrdersStatus]):
        billing_status (Union[Unset, FindPurchaseOrdersBillingStatus]):
        currency (Union[Unset, str]):
        location_id (Union[Unset, int]):
        tracking_location_id (Union[Unset, float]):
        supplier_id (Union[Unset, float]):
        extend (Union[Unset, list[FindPurchaseOrdersExtendItem]]):
        include_deleted (Union[Unset, bool]):
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
        Union[FindPurchaseOrdersResponse401, FindPurchaseOrdersResponse429, FindPurchaseOrdersResponse500, PurchaseOrderListResponse]
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
