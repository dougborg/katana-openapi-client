import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_supplier_addresses_response_401 import (
    GetSupplierAddressesResponse401,
)
from ...models.get_supplier_addresses_response_429 import (
    GetSupplierAddressesResponse429,
)
from ...models.get_supplier_addresses_response_500 import (
    GetSupplierAddressesResponse500,
)
from ...models.supplier_address_list_response import SupplierAddressListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Unset | list[int] = UNSET,
    supplier_ids: Unset | list[int] = UNSET,
    line_1: Unset | str = UNSET,
    line_2: Unset | str = UNSET,
    city: Unset | str = UNSET,
    state: Unset | str = UNSET,
    zip_: Unset | str = UNSET,
    country: Unset | str = UNSET,
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

    json_supplier_ids: Unset | list[int] = UNSET
    if not isinstance(supplier_ids, Unset):
        json_supplier_ids = supplier_ids

    params["supplier_ids"] = json_supplier_ids

    params["line_1"] = line_1

    params["line_2"] = line_2

    params["city"] = city

    params["state"] = state

    params["zip"] = zip_

    params["country"] = country

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
        "url": "/supplier_addresses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SupplierAddressListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetSupplierAddressesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetSupplierAddressesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetSupplierAddressesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
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
    supplier_ids: Unset | list[int] = UNSET,
    line_1: Unset | str = UNSET,
    line_2: Unset | str = UNSET,
    city: Unset | str = UNSET,
    state: Unset | str = UNSET,
    zip_: Unset | str = UNSET,
    country: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
]:
    """List all supplier addresses

     Returns a list of supplier addresses you've previously created.
       The supplier addresses are returned in sorted order, with the most recent supplier addresses
    appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        supplier_ids (Union[Unset, list[int]]):
        line_1 (Union[Unset, str]):
        line_2 (Union[Unset, str]):
        city (Union[Unset, str]):
        state (Union[Unset, str]):
        zip_ (Union[Unset, str]):
        country (Union[Unset, str]):
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
        Response[Union[GetSupplierAddressesResponse401, GetSupplierAddressesResponse429, GetSupplierAddressesResponse500, SupplierAddressListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        supplier_ids=supplier_ids,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
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
    supplier_ids: Unset | list[int] = UNSET,
    line_1: Unset | str = UNSET,
    line_2: Unset | str = UNSET,
    city: Unset | str = UNSET,
    state: Unset | str = UNSET,
    zip_: Unset | str = UNSET,
    country: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
    | None
):
    """List all supplier addresses

     Returns a list of supplier addresses you've previously created.
       The supplier addresses are returned in sorted order, with the most recent supplier addresses
    appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        supplier_ids (Union[Unset, list[int]]):
        line_1 (Union[Unset, str]):
        line_2 (Union[Unset, str]):
        city (Union[Unset, str]):
        state (Union[Unset, str]):
        zip_ (Union[Unset, str]):
        country (Union[Unset, str]):
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
        Union[GetSupplierAddressesResponse401, GetSupplierAddressesResponse429, GetSupplierAddressesResponse500, SupplierAddressListResponse]
    """

    return sync_detailed(
        client=client,
        ids=ids,
        supplier_ids=supplier_ids,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
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
    supplier_ids: Unset | list[int] = UNSET,
    line_1: Unset | str = UNSET,
    line_2: Unset | str = UNSET,
    city: Unset | str = UNSET,
    state: Unset | str = UNSET,
    zip_: Unset | str = UNSET,
    country: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> Response[
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
]:
    """List all supplier addresses

     Returns a list of supplier addresses you've previously created.
       The supplier addresses are returned in sorted order, with the most recent supplier addresses
    appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        supplier_ids (Union[Unset, list[int]]):
        line_1 (Union[Unset, str]):
        line_2 (Union[Unset, str]):
        city (Union[Unset, str]):
        state (Union[Unset, str]):
        zip_ (Union[Unset, str]):
        country (Union[Unset, str]):
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
        Response[Union[GetSupplierAddressesResponse401, GetSupplierAddressesResponse429, GetSupplierAddressesResponse500, SupplierAddressListResponse]]
    """

    kwargs = _get_kwargs(
        ids=ids,
        supplier_ids=supplier_ids,
        line_1=line_1,
        line_2=line_2,
        city=city,
        state=state,
        zip_=zip_,
        country=country,
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
    supplier_ids: Unset | list[int] = UNSET,
    line_1: Unset | str = UNSET,
    line_2: Unset | str = UNSET,
    city: Unset | str = UNSET,
    state: Unset | str = UNSET,
    zip_: Unset | str = UNSET,
    country: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
) -> (
    GetSupplierAddressesResponse401
    | GetSupplierAddressesResponse429
    | GetSupplierAddressesResponse500
    | SupplierAddressListResponse
    | None
):
    """List all supplier addresses

     Returns a list of supplier addresses you've previously created.
       The supplier addresses are returned in sorted order, with the most recent supplier addresses
    appearing first.

    Args:
        ids (Union[Unset, list[int]]):
        supplier_ids (Union[Unset, list[int]]):
        line_1 (Union[Unset, str]):
        line_2 (Union[Unset, str]):
        city (Union[Unset, str]):
        state (Union[Unset, str]):
        zip_ (Union[Unset, str]):
        country (Union[Unset, str]):
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
        Union[GetSupplierAddressesResponse401, GetSupplierAddressesResponse429, GetSupplierAddressesResponse500, SupplierAddressListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            ids=ids,
            supplier_ids=supplier_ids,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        )
    ).parsed
