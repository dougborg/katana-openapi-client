import datetime
from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.supplier_address_list_response import SupplierAddressListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    ids: Union[Unset, list[int]] = UNSET,
    supplier_ids: Union[Unset, list[int]] = UNSET,
    line_1: Union[Unset, str] = UNSET,
    line_2: Union[Unset, str] = UNSET,
    city: Union[Unset, str] = UNSET,
    state: Union[Unset, str] = UNSET,
    zip_: Union[Unset, str] = UNSET,
    country: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    created_at_min: Union[Unset, datetime.datetime] = UNSET,
    created_at_max: Union[Unset, datetime.datetime] = UNSET,
    updated_at_min: Union[Unset, datetime.datetime] = UNSET,
    updated_at_max: Union[Unset, datetime.datetime] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    json_supplier_ids: Union[Unset, list[int]] = UNSET
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

    json_created_at_min: Union[Unset, str] = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: Union[Unset, str] = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: Union[Unset, str] = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: Union[Unset, str] = UNSET
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, SupplierAddressListResponse]]:
    if response.status_code == 200:
        response_200 = SupplierAddressListResponse.from_dict(response.json())

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, SupplierAddressListResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    ids: Union[Unset, list[int]] = UNSET,
    supplier_ids: Union[Unset, list[int]] = UNSET,
    line_1: Union[Unset, str] = UNSET,
    line_2: Union[Unset, str] = UNSET,
    city: Union[Unset, str] = UNSET,
    state: Union[Unset, str] = UNSET,
    zip_: Union[Unset, str] = UNSET,
    country: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    created_at_min: Union[Unset, datetime.datetime] = UNSET,
    created_at_max: Union[Unset, datetime.datetime] = UNSET,
    updated_at_min: Union[Unset, datetime.datetime] = UNSET,
    updated_at_max: Union[Unset, datetime.datetime] = UNSET,
) -> Response[Union[ErrorResponse, SupplierAddressListResponse]]:
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
        Response[Union[ErrorResponse, SupplierAddressListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    ids: Union[Unset, list[int]] = UNSET,
    supplier_ids: Union[Unset, list[int]] = UNSET,
    line_1: Union[Unset, str] = UNSET,
    line_2: Union[Unset, str] = UNSET,
    city: Union[Unset, str] = UNSET,
    state: Union[Unset, str] = UNSET,
    zip_: Union[Unset, str] = UNSET,
    country: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    created_at_min: Union[Unset, datetime.datetime] = UNSET,
    created_at_max: Union[Unset, datetime.datetime] = UNSET,
    updated_at_min: Union[Unset, datetime.datetime] = UNSET,
    updated_at_max: Union[Unset, datetime.datetime] = UNSET,
) -> Optional[Union[ErrorResponse, SupplierAddressListResponse]]:
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
        Union[ErrorResponse, SupplierAddressListResponse]
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
    client: Union[AuthenticatedClient, Client],
    ids: Union[Unset, list[int]] = UNSET,
    supplier_ids: Union[Unset, list[int]] = UNSET,
    line_1: Union[Unset, str] = UNSET,
    line_2: Union[Unset, str] = UNSET,
    city: Union[Unset, str] = UNSET,
    state: Union[Unset, str] = UNSET,
    zip_: Union[Unset, str] = UNSET,
    country: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    created_at_min: Union[Unset, datetime.datetime] = UNSET,
    created_at_max: Union[Unset, datetime.datetime] = UNSET,
    updated_at_min: Union[Unset, datetime.datetime] = UNSET,
    updated_at_max: Union[Unset, datetime.datetime] = UNSET,
) -> Response[Union[ErrorResponse, SupplierAddressListResponse]]:
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
        Response[Union[ErrorResponse, SupplierAddressListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    ids: Union[Unset, list[int]] = UNSET,
    supplier_ids: Union[Unset, list[int]] = UNSET,
    line_1: Union[Unset, str] = UNSET,
    line_2: Union[Unset, str] = UNSET,
    city: Union[Unset, str] = UNSET,
    state: Union[Unset, str] = UNSET,
    zip_: Union[Unset, str] = UNSET,
    country: Union[Unset, str] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    created_at_min: Union[Unset, datetime.datetime] = UNSET,
    created_at_max: Union[Unset, datetime.datetime] = UNSET,
    updated_at_min: Union[Unset, datetime.datetime] = UNSET,
    updated_at_max: Union[Unset, datetime.datetime] = UNSET,
) -> Optional[Union[ErrorResponse, SupplierAddressListResponse]]:
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
        Union[ErrorResponse, SupplierAddressListResponse]
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
