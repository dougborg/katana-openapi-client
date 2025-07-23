from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.customer_list_response import CustomerListResponse
from ...models.get_all_customers_response_401 import GetAllCustomersResponse401
from ...models.get_all_customers_response_429 import GetAllCustomersResponse429
from ...models.get_all_customers_response_500 import GetAllCustomersResponse500
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    email: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["name"] = name

    params["email"] = email

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/customers",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CustomerListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllCustomersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllCustomersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllCustomersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    email: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
]:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        email (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerListResponse, GetAllCustomersResponse401, GetAllCustomersResponse429, GetAllCustomersResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        email=email,
        include_deleted=include_deleted,
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
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    email: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
    | None
):
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        email (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerListResponse, GetAllCustomersResponse401, GetAllCustomersResponse429, GetAllCustomersResponse500]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        email=email,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    email: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
]:
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        email (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerListResponse, GetAllCustomersResponse401, GetAllCustomersResponse429, GetAllCustomersResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        name=name,
        email=email,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    name: Unset | str = UNSET,
    email: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    CustomerListResponse
    | GetAllCustomersResponse401
    | GetAllCustomersResponse429
    | GetAllCustomersResponse500
    | None
):
    """List all customers

     Returns a list of customers you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        name (Union[Unset, str]):
        email (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerListResponse, GetAllCustomersResponse401, GetAllCustomersResponse429, GetAllCustomersResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            name=name,
            email=email,
            include_deleted=include_deleted,
        )
    ).parsed
