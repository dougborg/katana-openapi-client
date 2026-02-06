import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_sales_order_rows_extend_item import (
    GetAllSalesOrderRowsExtendItem,
)
from ...models.get_all_sales_order_rows_product_availability import (
    GetAllSalesOrderRowsProductAvailability,
)
from ...models.sales_order_row_list_response import SalesOrderRowListResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    linked_manufacturing_order_id: int | Unset = UNSET,
    product_availability: GetAllSalesOrderRowsProductAvailability | Unset = UNSET,
    extend: list[GetAllSalesOrderRowsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["variant_id"] = variant_id

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_sales_order_ids: list[int] | Unset = UNSET
    if not isinstance(sales_order_ids, Unset):
        json_sales_order_ids = sales_order_ids

    params["sales_order_ids"] = json_sales_order_ids

    params["location_id"] = location_id

    params["tax_rate_id"] = tax_rate_id

    params["linked_manufacturing_order_id"] = linked_manufacturing_order_id

    json_product_availability: str | Unset = UNSET
    if not isinstance(product_availability, Unset):
        json_product_availability = product_availability.value

    params["product_availability"] = json_product_availability

    json_extend: list[str] | Unset = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params["include_deleted"] = include_deleted

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
        "url": "/sales_order_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesOrderRowListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderRowListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | SalesOrderRowListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    linked_manufacturing_order_id: int | Unset = UNSET,
    product_availability: GetAllSalesOrderRowsProductAvailability | Unset = UNSET,
    extend: list[GetAllSalesOrderRowsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderRowListResponse]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        variant_id (int | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        location_id (int | Unset):
        tax_rate_id (float | Unset):
        linked_manufacturing_order_id (int | Unset):
        product_availability (GetAllSalesOrderRowsProductAvailability | Unset):
        extend (list[GetAllSalesOrderRowsExtendItem] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderRowListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        sales_order_ids=sales_order_ids,
        location_id=location_id,
        tax_rate_id=tax_rate_id,
        linked_manufacturing_order_id=linked_manufacturing_order_id,
        product_availability=product_availability,
        extend=extend,
        include_deleted=include_deleted,
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    linked_manufacturing_order_id: int | Unset = UNSET,
    product_availability: GetAllSalesOrderRowsProductAvailability | Unset = UNSET,
    extend: list[GetAllSalesOrderRowsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesOrderRowListResponse | None:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        variant_id (int | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        location_id (int | Unset):
        tax_rate_id (float | Unset):
        linked_manufacturing_order_id (int | Unset):
        product_availability (GetAllSalesOrderRowsProductAvailability | Unset):
        extend (list[GetAllSalesOrderRowsExtendItem] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderRowListResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        sales_order_ids=sales_order_ids,
        location_id=location_id,
        tax_rate_id=tax_rate_id,
        linked_manufacturing_order_id=linked_manufacturing_order_id,
        product_availability=product_availability,
        extend=extend,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    linked_manufacturing_order_id: int | Unset = UNSET,
    product_availability: GetAllSalesOrderRowsProductAvailability | Unset = UNSET,
    extend: list[GetAllSalesOrderRowsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderRowListResponse]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        variant_id (int | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        location_id (int | Unset):
        tax_rate_id (float | Unset):
        linked_manufacturing_order_id (int | Unset):
        product_availability (GetAllSalesOrderRowsProductAvailability | Unset):
        extend (list[GetAllSalesOrderRowsExtendItem] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderRowListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        variant_id=variant_id,
        ids=ids,
        sales_order_ids=sales_order_ids,
        location_id=location_id,
        tax_rate_id=tax_rate_id,
        linked_manufacturing_order_id=linked_manufacturing_order_id,
        product_availability=product_availability,
        extend=extend,
        include_deleted=include_deleted,
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    variant_id: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    location_id: int | Unset = UNSET,
    tax_rate_id: float | Unset = UNSET,
    linked_manufacturing_order_id: int | Unset = UNSET,
    product_availability: GetAllSalesOrderRowsProductAvailability | Unset = UNSET,
    extend: list[GetAllSalesOrderRowsExtendItem] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesOrderRowListResponse | None:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        variant_id (int | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        location_id (int | Unset):
        tax_rate_id (float | Unset):
        linked_manufacturing_order_id (int | Unset):
        product_availability (GetAllSalesOrderRowsProductAvailability | Unset):
        extend (list[GetAllSalesOrderRowsExtendItem] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderRowListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            variant_id=variant_id,
            ids=ids,
            sales_order_ids=sales_order_ids,
            location_id=location_id,
            tax_rate_id=tax_rate_id,
            linked_manufacturing_order_id=linked_manufacturing_order_id,
            product_availability=product_availability,
            extend=extend,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
