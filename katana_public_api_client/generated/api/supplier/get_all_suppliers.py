import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_suppliers_response_401 import GetAllSuppliersResponse401
from ...models.get_all_suppliers_response_429 import GetAllSuppliersResponse429
from ...models.get_all_suppliers_response_500 import GetAllSuppliersResponse500
from ...models.supplier_list_response import SupplierListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: Unset | str = UNSET,
    ids: Unset | list[int] = UNSET,
    email: Unset | str = UNSET,
    phone: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["name"] = name

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["email"] = email

    params["phone"] = phone

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
        "url": "/suppliers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SupplierListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSuppliersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSuppliersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSuppliersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
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
    name: Unset | str = UNSET,
    ids: Unset | list[int] = UNSET,
    email: Unset | str = UNSET,
    phone: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
]:
    """List all suppliers

     Returns a list of suppliers you've previously created. The suppliers are returned in sorted order,
        with the most recent suppliers appearing first.

    Args:
        name (Union[Unset, str]):
        ids (Union[Unset, list[int]]):
        email (Union[Unset, str]):
        phone (Union[Unset, str]):
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
        Response[Union[GetAllSuppliersResponse401, GetAllSuppliersResponse429, GetAllSuppliersResponse500, SupplierListResponse]]
    """

    kwargs = _get_kwargs(
        name=name,
        ids=ids,
        email=email,
        phone=phone,
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
    name: Unset | str = UNSET,
    ids: Unset | list[int] = UNSET,
    email: Unset | str = UNSET,
    phone: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
    | None
):
    """List all suppliers

     Returns a list of suppliers you've previously created. The suppliers are returned in sorted order,
        with the most recent suppliers appearing first.

    Args:
        name (Union[Unset, str]):
        ids (Union[Unset, list[int]]):
        email (Union[Unset, str]):
        phone (Union[Unset, str]):
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
        Union[GetAllSuppliersResponse401, GetAllSuppliersResponse429, GetAllSuppliersResponse500, SupplierListResponse]
    """

    return sync_detailed(
        client=client,
        name=name,
        ids=ids,
        email=email,
        phone=phone,
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
    name: Unset | str = UNSET,
    ids: Unset | list[int] = UNSET,
    email: Unset | str = UNSET,
    phone: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
]:
    """List all suppliers

     Returns a list of suppliers you've previously created. The suppliers are returned in sorted order,
        with the most recent suppliers appearing first.

    Args:
        name (Union[Unset, str]):
        ids (Union[Unset, list[int]]):
        email (Union[Unset, str]):
        phone (Union[Unset, str]):
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
        Response[Union[GetAllSuppliersResponse401, GetAllSuppliersResponse429, GetAllSuppliersResponse500, SupplierListResponse]]
    """

    kwargs = _get_kwargs(
        name=name,
        ids=ids,
        email=email,
        phone=phone,
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
    name: Unset | str = UNSET,
    ids: Unset | list[int] = UNSET,
    email: Unset | str = UNSET,
    phone: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetAllSuppliersResponse401
    | GetAllSuppliersResponse429
    | GetAllSuppliersResponse500
    | SupplierListResponse
    | None
):
    """List all suppliers

     Returns a list of suppliers you've previously created. The suppliers are returned in sorted order,
        with the most recent suppliers appearing first.

    Args:
        name (Union[Unset, str]):
        ids (Union[Unset, list[int]]):
        email (Union[Unset, str]):
        phone (Union[Unset, str]):
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
        Union[GetAllSuppliersResponse401, GetAllSuppliersResponse429, GetAllSuppliersResponse500, SupplierListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            ids=ids,
            email=email,
            phone=phone,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
