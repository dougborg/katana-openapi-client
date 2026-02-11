import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.customer_list_response import CustomerListResponse
from ...models.error_response import ErrorResponse


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
    name: str | Unset = UNSET,
    email: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    company: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    category: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    reference_id: str | Unset = UNSET,
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

    params["name"] = name

    params["email"] = email

    params["first_name"] = first_name

    params["last_name"] = last_name

    params["company"] = company

    params["phone"] = phone

    params["category"] = category

    params["currency"] = currency

    params["reference_id"] = reference_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/customers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> CustomerListResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = CustomerListResponse.from_dict(response.json())

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
) -> Response[CustomerListResponse | ErrorResponse]:
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
    name: str | Unset = UNSET,
    email: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    company: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    category: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    reference_id: str | Unset = UNSET,
) -> Response[CustomerListResponse | ErrorResponse]:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        name (str | Unset):
        email (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        company (str | Unset):
        phone (str | Unset):
        category (str | Unset):
        currency (str | Unset):
        reference_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomerListResponse | ErrorResponse]
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
        name=name,
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        phone=phone,
        category=category,
        currency=currency,
        reference_id=reference_id,
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
    name: str | Unset = UNSET,
    email: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    company: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    category: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    reference_id: str | Unset = UNSET,
) -> CustomerListResponse | ErrorResponse | None:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        name (str | Unset):
        email (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        company (str | Unset):
        phone (str | Unset):
        category (str | Unset):
        currency (str | Unset):
        reference_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomerListResponse | ErrorResponse
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
        name=name,
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        phone=phone,
        category=category,
        currency=currency,
        reference_id=reference_id,
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
    name: str | Unset = UNSET,
    email: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    company: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    category: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    reference_id: str | Unset = UNSET,
) -> Response[CustomerListResponse | ErrorResponse]:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        name (str | Unset):
        email (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        company (str | Unset):
        phone (str | Unset):
        category (str | Unset):
        currency (str | Unset):
        reference_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[CustomerListResponse | ErrorResponse]
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
        name=name,
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        phone=phone,
        category=category,
        currency=currency,
        reference_id=reference_id,
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
    name: str | Unset = UNSET,
    email: str | Unset = UNSET,
    first_name: str | Unset = UNSET,
    last_name: str | Unset = UNSET,
    company: str | Unset = UNSET,
    phone: str | Unset = UNSET,
    category: str | Unset = UNSET,
    currency: str | Unset = UNSET,
    reference_id: str | Unset = UNSET,
) -> CustomerListResponse | ErrorResponse | None:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        name (str | Unset):
        email (str | Unset):
        first_name (str | Unset):
        last_name (str | Unset):
        company (str | Unset):
        phone (str | Unset):
        category (str | Unset):
        currency (str | Unset):
        reference_id (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        CustomerListResponse | ErrorResponse
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
            name=name,
            email=email,
            first_name=first_name,
            last_name=last_name,
            company=company,
            phone=phone,
            category=category,
            currency=currency,
            reference_id=reference_id,
        )
    ).parsed
