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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    sales_order_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    linked_manufacturing_order_id: Unset | int = UNSET,
    product_availability: Unset | GetAllSalesOrderRowsProductAvailability = UNSET,
    extend: Unset | list[GetAllSalesOrderRowsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["variant_id"] = variant_id

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_sales_order_ids: Unset | list[int] = UNSET
    if not isinstance(sales_order_ids, Unset):
        json_sales_order_ids = sales_order_ids

    params["sales_order_ids"] = json_sales_order_ids

    params["location_id"] = location_id

    params["tax_rate_id"] = tax_rate_id

    params["linked_manufacturing_order_id"] = linked_manufacturing_order_id

    json_product_availability: Unset | str = UNSET
    if not isinstance(product_availability, Unset):
        json_product_availability = product_availability.value

    params["product_availability"] = json_product_availability

    json_extend: Unset | list[str] = UNSET
    if not isinstance(extend, Unset):
        json_extend = []
        for extend_item_data in extend:
            extend_item = extend_item_data.value
            json_extend.append(extend_item)

    params["extend"] = json_extend

    params["include_deleted"] = include_deleted

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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    sales_order_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    linked_manufacturing_order_id: Unset | int = UNSET,
    product_availability: Unset | GetAllSalesOrderRowsProductAvailability = UNSET,
    extend: Unset | list[GetAllSalesOrderRowsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | SalesOrderRowListResponse]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        sales_order_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        linked_manufacturing_order_id (Union[Unset, int]):
        product_availability (Union[Unset, GetAllSalesOrderRowsProductAvailability]):
        extend (Union[Unset, list[GetAllSalesOrderRowsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderRowListResponse]]
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    sales_order_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    linked_manufacturing_order_id: Unset | int = UNSET,
    product_availability: Unset | GetAllSalesOrderRowsProductAvailability = UNSET,
    extend: Unset | list[GetAllSalesOrderRowsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | SalesOrderRowListResponse | None:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        sales_order_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        linked_manufacturing_order_id (Union[Unset, int]):
        product_availability (Union[Unset, GetAllSalesOrderRowsProductAvailability]):
        extend (Union[Unset, list[GetAllSalesOrderRowsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderRowListResponse]
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    sales_order_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    linked_manufacturing_order_id: Unset | int = UNSET,
    product_availability: Unset | GetAllSalesOrderRowsProductAvailability = UNSET,
    extend: Unset | list[GetAllSalesOrderRowsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | SalesOrderRowListResponse]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        sales_order_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        linked_manufacturing_order_id (Union[Unset, int]):
        product_availability (Union[Unset, GetAllSalesOrderRowsProductAvailability]):
        extend (Union[Unset, list[GetAllSalesOrderRowsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderRowListResponse]]
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    variant_id: Unset | int = UNSET,
    ids: Unset | list[int] = UNSET,
    sales_order_ids: Unset | list[int] = UNSET,
    location_id: Unset | int = UNSET,
    tax_rate_id: Unset | float = UNSET,
    linked_manufacturing_order_id: Unset | int = UNSET,
    product_availability: Unset | GetAllSalesOrderRowsProductAvailability = UNSET,
    extend: Unset | list[GetAllSalesOrderRowsExtendItem] = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | SalesOrderRowListResponse | None:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        variant_id (Union[Unset, int]):
        ids (Union[Unset, list[int]]):
        sales_order_ids (Union[Unset, list[int]]):
        location_id (Union[Unset, int]):
        tax_rate_id (Union[Unset, float]):
        linked_manufacturing_order_id (Union[Unset, int]):
        product_availability (Union[Unset, GetAllSalesOrderRowsProductAvailability]):
        extend (Union[Unset, list[GetAllSalesOrderRowsExtendItem]]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderRowListResponse]
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
