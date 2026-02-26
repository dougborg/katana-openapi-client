import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_sales_orders_product_availability import (
    GetAllSalesOrdersProductAvailability,
)
from ...models.ingredient_availability import IngredientAvailability
from ...models.sales_order_list_response import SalesOrderListResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    order_no: str | Unset = UNSET,
    customer_id: int | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    production_status: str | Unset = UNSET,
    invoicing_status: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    source: str | Unset = UNSET,
    ecommerce_store_name: str | Unset = UNSET,
    ecommerce_order_id: str | Unset = UNSET,
    ecommerce_order_type: str | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    product_availability: GetAllSalesOrdersProductAvailability | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

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

    params["order_no"] = order_no

    params["customer_id"] = customer_id

    params["location_id"] = location_id

    params["status"] = status

    params["production_status"] = production_status

    params["invoicing_status"] = invoicing_status

    params["currency"] = currency

    params["source"] = source

    params["ecommerce_store_name"] = ecommerce_store_name

    params["ecommerce_order_id"] = ecommerce_order_id

    params["ecommerce_order_type"] = ecommerce_order_type

    json_ingredient_availability: str | Unset = UNSET
    if not isinstance(ingredient_availability, Unset):
        json_ingredient_availability = ingredient_availability.value

    params["ingredient_availability"] = json_ingredient_availability

    json_product_availability: str | Unset = UNSET
    if not isinstance(product_availability, Unset):
        json_product_availability = product_availability.value

    params["product_availability"] = json_product_availability

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesOrderListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | SalesOrderListResponse]:
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
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    order_no: str | Unset = UNSET,
    customer_id: int | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    production_status: str | Unset = UNSET,
    invoicing_status: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    source: str | Unset = UNSET,
    ecommerce_store_name: str | Unset = UNSET,
    ecommerce_order_id: str | Unset = UNSET,
    ecommerce_order_type: str | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    product_availability: GetAllSalesOrdersProductAvailability | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderListResponse]:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        order_no (str | Unset):
        customer_id (int | Unset):
        location_id (int | Unset):
        status (str | Unset):
        production_status (str | Unset):
        invoicing_status (str | Unset):
        currency (str | Unset):
        source (str | Unset):
        ecommerce_store_name (str | Unset):
        ecommerce_order_id (str | Unset):
        ecommerce_order_type (str | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
        product_availability (GetAllSalesOrdersProductAvailability | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        production_status=production_status,
        invoicing_status=invoicing_status,
        currency=currency,
        source=source,
        ecommerce_store_name=ecommerce_store_name,
        ecommerce_order_id=ecommerce_order_id,
        ecommerce_order_type=ecommerce_order_type,
        ingredient_availability=ingredient_availability,
        product_availability=product_availability,
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
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    order_no: str | Unset = UNSET,
    customer_id: int | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    production_status: str | Unset = UNSET,
    invoicing_status: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    source: str | Unset = UNSET,
    ecommerce_store_name: str | Unset = UNSET,
    ecommerce_order_id: str | Unset = UNSET,
    ecommerce_order_type: str | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    product_availability: GetAllSalesOrdersProductAvailability | Unset = UNSET,
) -> ErrorResponse | SalesOrderListResponse | None:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        order_no (str | Unset):
        customer_id (int | Unset):
        location_id (int | Unset):
        status (str | Unset):
        production_status (str | Unset):
        invoicing_status (str | Unset):
        currency (str | Unset):
        source (str | Unset):
        ecommerce_store_name (str | Unset):
        ecommerce_order_id (str | Unset):
        ecommerce_order_type (str | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
        product_availability (GetAllSalesOrdersProductAvailability | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderListResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        production_status=production_status,
        invoicing_status=invoicing_status,
        currency=currency,
        source=source,
        ecommerce_store_name=ecommerce_store_name,
        ecommerce_order_id=ecommerce_order_id,
        ecommerce_order_type=ecommerce_order_type,
        ingredient_availability=ingredient_availability,
        product_availability=product_availability,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    order_no: str | Unset = UNSET,
    customer_id: int | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    production_status: str | Unset = UNSET,
    invoicing_status: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    source: str | Unset = UNSET,
    ecommerce_store_name: str | Unset = UNSET,
    ecommerce_order_id: str | Unset = UNSET,
    ecommerce_order_type: str | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    product_availability: GetAllSalesOrdersProductAvailability | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderListResponse]:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        order_no (str | Unset):
        customer_id (int | Unset):
        location_id (int | Unset):
        status (str | Unset):
        production_status (str | Unset):
        invoicing_status (str | Unset):
        currency (str | Unset):
        source (str | Unset):
        ecommerce_store_name (str | Unset):
        ecommerce_order_id (str | Unset):
        ecommerce_order_type (str | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
        product_availability (GetAllSalesOrdersProductAvailability | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        production_status=production_status,
        invoicing_status=invoicing_status,
        currency=currency,
        source=source,
        ecommerce_store_name=ecommerce_store_name,
        ecommerce_order_id=ecommerce_order_id,
        ecommerce_order_type=ecommerce_order_type,
        ingredient_availability=ingredient_availability,
        product_availability=product_availability,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    order_no: str | Unset = UNSET,
    customer_id: int | Unset = UNSET,
    location_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    production_status: str | Unset = UNSET,
    invoicing_status: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    source: str | Unset = UNSET,
    ecommerce_store_name: str | Unset = UNSET,
    ecommerce_order_id: str | Unset = UNSET,
    ecommerce_order_type: str | Unset = UNSET,
    ingredient_availability: IngredientAvailability | Unset = UNSET,
    product_availability: GetAllSalesOrdersProductAvailability | Unset = UNSET,
) -> ErrorResponse | SalesOrderListResponse | None:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        order_no (str | Unset):
        customer_id (int | Unset):
        location_id (int | Unset):
        status (str | Unset):
        production_status (str | Unset):
        invoicing_status (str | Unset):
        currency (str | Unset):
        source (str | Unset):
        ecommerce_store_name (str | Unset):
        ecommerce_order_id (str | Unset):
        ecommerce_order_type (str | Unset):
        ingredient_availability (IngredientAvailability | Unset): Availability status of
            ingredients for production
        product_availability (GetAllSalesOrdersProductAvailability | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            order_no=order_no,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            production_status=production_status,
            invoicing_status=invoicing_status,
            currency=currency,
            source=source,
            ecommerce_store_name=ecommerce_store_name,
            ecommerce_order_id=ecommerce_order_id,
            ecommerce_order_type=ecommerce_order_type,
            ingredient_availability=ingredient_availability,
            product_availability=product_availability,
        )
    ).parsed
