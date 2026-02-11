import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_sales_order_addresses_entity_type import (
    GetAllSalesOrderAddressesEntityType,
)
from ...models.sales_order_address_list_response import SalesOrderAddressListResponse


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    entity_type: GetAllSalesOrderAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    company: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    line_1: str | Unset = UNSET,
    line_2: str | Unset = UNSET,
    city: str | Unset = UNSET,
    state: str | Unset = UNSET,
    zip_: str | Unset = UNSET,
    country: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_entity_type: str | Unset = UNSET
    if not isinstance(entity_type, Unset):
        json_entity_type = entity_type.value

    params["entity_type"] = json_entity_type

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_sales_order_ids: list[int] | Unset = UNSET
    if not isinstance(sales_order_ids, Unset):
        json_sales_order_ids = sales_order_ids

    params["sales_order_ids"] = json_sales_order_ids

    params["company"] = company

    params["first_name"] = first_name

    params["last_name"] = last_name

    params["line_1"] = line_1

    params["line_2"] = line_2

    params["city"] = city

    params["state"] = state

    params["zip"] = zip_

    params["country"] = country

    params["phone"] = phone

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
        "url": "/sales_order_addresses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesOrderAddressListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderAddressListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | SalesOrderAddressListResponse]:
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
    entity_type: GetAllSalesOrderAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    company: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    line_1: str | Unset = UNSET,
    line_2: str | Unset = UNSET,
    city: str | Unset = UNSET,
    state: str | Unset = UNSET,
    zip_: str | Unset = UNSET,
    country: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderAddressListResponse]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllSalesOrderAddressesEntityType | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        company (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        line_1 (str | Unset):
        line_2 (str | Unset):
        city (str | Unset):
        state (str | Unset):
        zip_ (str | Unset):
        country (str | Unset):
        phone (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderAddressListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        sales_order_ids=sales_order_ids,
        company=company,
        first_name=first_name,
        last_name=last_name,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
        phone=phone,
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
    entity_type: GetAllSalesOrderAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    company: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    line_1: str | Unset = UNSET,
    line_2: str | Unset = UNSET,
    city: str | Unset = UNSET,
    state: str | Unset = UNSET,
    zip_: str | Unset = UNSET,
    country: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesOrderAddressListResponse | None:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllSalesOrderAddressesEntityType | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        company (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        line_1 (str | Unset):
        line_2 (str | Unset):
        city (str | Unset):
        state (str | Unset):
        zip_ (str | Unset):
        country (str | Unset):
        phone (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderAddressListResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        sales_order_ids=sales_order_ids,
        company=company,
        first_name=first_name,
        last_name=last_name,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
        phone=phone,
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
    entity_type: GetAllSalesOrderAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    company: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    line_1: str | Unset = UNSET,
    line_2: str | Unset = UNSET,
    city: str | Unset = UNSET,
    state: str | Unset = UNSET,
    zip_: str | Unset = UNSET,
    country: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderAddressListResponse]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllSalesOrderAddressesEntityType | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        company (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        line_1 (str | Unset):
        line_2 (str | Unset):
        city (str | Unset):
        state (str | Unset):
        zip_ (str | Unset):
        country (str | Unset):
        phone (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderAddressListResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        sales_order_ids=sales_order_ids,
        company=company,
        first_name=first_name,
        last_name=last_name,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
        phone=phone,
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
    entity_type: GetAllSalesOrderAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    sales_order_ids: list[int] | Unset = UNSET,
    company: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    line_1: str | Unset = UNSET,
    line_2: str | Unset = UNSET,
    city: str | Unset = UNSET,
    state: str | Unset = UNSET,
    zip_: str | Unset = UNSET,
    country: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesOrderAddressListResponse | None:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllSalesOrderAddressesEntityType | Unset):
        ids (list[int] | Unset):
        sales_order_ids (list[int] | Unset):
        company (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        line_1 (str | Unset):
        line_2 (str | Unset):
        city (str | Unset):
        state (str | Unset):
        zip_ (str | Unset):
        country (str | Unset):
        phone (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderAddressListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            entity_type=entity_type,
            ids=ids,
            sales_order_ids=sales_order_ids,
            company=company,
            first_name=first_name,
            last_name=last_name,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            phone=phone,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
