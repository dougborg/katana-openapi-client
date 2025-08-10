from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.storage_bin_list_response import StorageBinListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    location_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    bin_name: Union[Unset, str] = UNSET,
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, StorageBinListResponse]]:
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, StorageBinListResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    location_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    bin_name: Union[Unset, str] = UNSET,
) -> Response[Union[ErrorResponse, StorageBinListResponse]]:
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
    client: Union[AuthenticatedClient, Client],
    location_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    bin_name: Union[Unset, str] = UNSET,
) -> Optional[Union[ErrorResponse, StorageBinListResponse]]:
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
    client: Union[AuthenticatedClient, Client],
    location_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    bin_name: Union[Unset, str] = UNSET,
) -> Response[Union[ErrorResponse, StorageBinListResponse]]:
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
    client: Union[AuthenticatedClient, Client],
    location_id: Union[Unset, int] = UNSET,
    include_deleted: Union[Unset, bool] = UNSET,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    bin_name: Union[Unset, str] = UNSET,
) -> Optional[Union[ErrorResponse, StorageBinListResponse]]:
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
