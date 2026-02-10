import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.customer_address_list_response import CustomerAddressListResponse
from ...models.error_response import ErrorResponse
from ...models.get_all_customer_addresses_entity_type import (
    GetAllCustomerAddressesEntityType,
)


def _get_kwargs(
    *,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    entity_type: GetAllCustomerAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    customer_ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
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

    json_customer_ids: list[int] | Unset = UNSET
    if not isinstance(customer_ids, Unset):
        json_customer_ids = customer_ids

    params["customer_ids"] = json_customer_ids

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

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/customer_addresses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CustomerAddressListResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = CustomerAddressListResponse.from_dict(response.json())

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
) -> Response[CustomerAddressListResponse | ErrorResponse]:
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
    entity_type: GetAllCustomerAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    customer_ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
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
) -> Response[CustomerAddressListResponse | ErrorResponse]:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllCustomerAddressesEntityType | Unset):
        ids (list[int] | Unset):
        customer_ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomerAddressListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        customer_ids=customer_ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
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
    entity_type: GetAllCustomerAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    customer_ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
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
) -> CustomerAddressListResponse | ErrorResponse | None:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllCustomerAddressesEntityType | Unset):
        ids (list[int] | Unset):
        customer_ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomerAddressListResponse | ErrorResponse
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        customer_ids=customer_ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
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
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    entity_type: GetAllCustomerAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    customer_ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
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
) -> Response[CustomerAddressListResponse | ErrorResponse]:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllCustomerAddressesEntityType | Unset):
        ids (list[int] | Unset):
        customer_ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomerAddressListResponse | ErrorResponse]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        entity_type=entity_type,
        ids=ids,
        customer_ids=customer_ids,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
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
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    entity_type: GetAllCustomerAddressesEntityType | Unset = UNSET,
    ids: list[int] | Unset = UNSET,
    customer_ids: list[int] | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
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
) -> CustomerAddressListResponse | ErrorResponse | None:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        entity_type (GetAllCustomerAddressesEntityType | Unset):
        ids (list[int] | Unset):
        customer_ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomerAddressListResponse | ErrorResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            entity_type=entity_type,
            ids=ids,
            customer_ids=customer_ids,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
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
        )
    ).parsed
