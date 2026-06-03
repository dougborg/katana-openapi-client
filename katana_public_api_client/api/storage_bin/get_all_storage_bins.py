from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.storage_bin_response import StorageBinResponse


def _get_kwargs(
    *,
    location_id: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    bin_name: str | Unset = UNSET,
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
) -> ErrorResponse | list[StorageBinResponse] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = StorageBinResponse.from_dict(
                cast(Mapping[str, Any], response_200_item_data)
            )

            response_200.append(response_200_item)

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
) -> Response[ErrorResponse | list[StorageBinResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    location_id: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    bin_name: str | Unset = UNSET,
) -> Response[ErrorResponse | list[StorageBinResponse]]:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with
    the most recent storage bin appearing first.

    Args:
        location_id (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        bin_name (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | list[StorageBinResponse]]
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
    location_id: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    bin_name: str | Unset = UNSET,
) -> ErrorResponse | list[StorageBinResponse] | None:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with
    the most recent storage bin appearing first.

    Args:
        location_id (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        bin_name (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | list[StorageBinResponse]
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
    location_id: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    bin_name: str | Unset = UNSET,
) -> Response[ErrorResponse | list[StorageBinResponse]]:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with
    the most recent storage bin appearing first.

    Args:
        location_id (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        bin_name (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | list[StorageBinResponse]]
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
    location_id: int | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    bin_name: str | Unset = UNSET,
) -> ErrorResponse | list[StorageBinResponse] | None:
    """List all storage bins

     Returns a list of storage bins you've previously created. The storage bins are returned in sorted
    order, with
    the most recent storage bin appearing first.

    Args:
        location_id (int | Unset):
        include_deleted (bool | Unset):
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        bin_name (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | list[StorageBinResponse]
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
