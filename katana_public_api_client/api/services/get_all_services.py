import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.service_list_response import ServiceListResponse


def _get_kwargs(
    *,
    ids: list[int] | Unset = UNSET,
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    category_name: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
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

    params["name"] = name

    params["uom"] = uom

    params["is_sellable"] = is_sellable

    params["category_name"] = category_name

    params["include_deleted"] = include_deleted

    params["include_archived"] = include_archived

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
        "url": "/services",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ServiceListResponse | None:
    if response.status_code == 200:
        response_200 = ServiceListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | ServiceListResponse]:
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
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    category_name: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ServiceListResponse]:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        category_name (str | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        Response[ErrorResponse | ServiceListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        category_name=category_name,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    category_name: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ServiceListResponse | None:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        category_name (str | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        ErrorResponse | ServiceListResponse
    """

    return sync_detailed(
        client=client,
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        category_name=category_name,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    category_name: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | ServiceListResponse]:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        category_name (str | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        Response[ErrorResponse | ServiceListResponse]
    """

    kwargs = _get_kwargs(
        ids=ids,
        name=name,
        uom=uom,
        is_sellable=is_sellable,
        category_name=category_name,
        include_deleted=include_deleted,
        include_archived=include_archived,
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
    name: str | Unset = UNSET,
    uom: str | Unset = UNSET,
    is_sellable: bool | Unset = UNSET,
    category_name: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    include_archived: bool | Unset = UNSET,
    limit: int | Unset = 50,
    page: int | Unset = 1,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | ServiceListResponse | None:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Args:
        ids (list[int] | Unset):
        name (str | Unset):
        uom (str | Unset):
        is_sellable (bool | Unset):
        category_name (str | Unset):
        include_deleted (bool | Unset):
        include_archived (bool | Unset):
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
        ErrorResponse | ServiceListResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            name=name,
            uom=uom,
            is_sellable=is_sellable,
            category_name=category_name,
            include_deleted=include_deleted,
            include_archived=include_archived,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
