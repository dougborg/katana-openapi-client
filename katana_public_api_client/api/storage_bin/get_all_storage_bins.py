from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.storage_bin_list_response import StorageBinListResponse


def _get_kwargs(
    *,
    location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    bin_name: Unset | str = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["location_id"] = location_id

    params["include_deleted"] = include_deleted

    params["limit"] = limit

    params["page"] = page

    params["bin_name"] = bin_name

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/bin_locations",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | StorageBinListResponse | None:
    if response.status_code == 200:
        response_200 = StorageBinListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | StorageBinListResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    bin_name: Unset | str = UNSET,
) -> Response[ErrorResponse | StorageBinListResponse]:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with the most recent storage bin appearing first.

    Args:
        location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        bin_name (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, StorageBinListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        bin_name=bin_name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    bin_name: Unset | str = UNSET,
) -> ErrorResponse | StorageBinListResponse | None:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with the most recent storage bin appearing first.

    Args:
        location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        bin_name (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, StorageBinListResponse]
    """

    return sync_detailed(
        client=client,
        location_id=location_id,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        bin_name=bin_name,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    bin_name: Unset | str = UNSET,
) -> Response[ErrorResponse | StorageBinListResponse]:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with the most recent storage bin appearing first.

    Args:
        location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        bin_name (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, StorageBinListResponse]]
    """

    kwargs = _get_kwargs(
        location_id=location_id,
        include_deleted=include_deleted,
        limit=limit,
        page=page,
        bin_name=bin_name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    location_id: Unset | int = UNSET,
    include_deleted: Unset | bool = UNSET,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    bin_name: Unset | str = UNSET,
) -> ErrorResponse | StorageBinListResponse | None:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with the most recent storage bin appearing first.

    Args:
        location_id (Union[Unset, int]):
        include_deleted (Union[Unset, bool]):
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        bin_name (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, StorageBinListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            location_id=location_id,
            include_deleted=include_deleted,
            limit=limit,
            page=page,
            bin_name=bin_name,
        )
    ).parsed
