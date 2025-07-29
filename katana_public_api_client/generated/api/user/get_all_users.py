from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_users_response_401 import GetAllUsersResponse401
from ...models.get_all_users_response_429 import GetAllUsersResponse429
from ...models.get_all_users_response_500 import GetAllUsersResponse500
from ...models.user_list_response import UserListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    role: Union[Unset, str] = UNSET,
    status: Union[Unset, str] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["role"] = role

    params["status"] = status

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/users",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    if response.status_code == 200:
        response_200 = UserListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllUsersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllUsersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllUsersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    role: Union[Unset, str] = UNSET,
    status: Union[Unset, str] = UNSET,
) -> Response[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    """List all users

     Returns a list of active users in your account.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        role (Union[Unset, str]):
        status (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllUsersResponse401, GetAllUsersResponse429, GetAllUsersResponse500, UserListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        role=role,
        status=status,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    role: Union[Unset, str] = UNSET,
    status: Union[Unset, str] = UNSET,
) -> Optional[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    """List all users

     Returns a list of active users in your account.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        role (Union[Unset, str]):
        status (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllUsersResponse401, GetAllUsersResponse429, GetAllUsersResponse500, UserListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        role=role,
        status=status,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    role: Union[Unset, str] = UNSET,
    status: Union[Unset, str] = UNSET,
) -> Response[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    """List all users

     Returns a list of active users in your account.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        role (Union[Unset, str]):
        status (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllUsersResponse401, GetAllUsersResponse429, GetAllUsersResponse500, UserListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        role=role,
        status=status,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    role: Union[Unset, str] = UNSET,
    status: Union[Unset, str] = UNSET,
) -> Optional[
    Union[
        GetAllUsersResponse401,
        GetAllUsersResponse429,
        GetAllUsersResponse500,
        UserListResponse,
    ]
]:
    """List all users

     Returns a list of active users in your account.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        role (Union[Unset, str]):
        status (Union[Unset, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllUsersResponse401, GetAllUsersResponse429, GetAllUsersResponse500, UserListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            role=role,
            status=status,
        )
    ).parsed
