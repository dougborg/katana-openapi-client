from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_location_response_401 import GetLocationResponse401
from ...models.get_location_response_404 import GetLocationResponse404
from ...models.get_location_response_429 import GetLocationResponse429
from ...models.get_location_response_500 import GetLocationResponse500
from ...models.location import Location
from ...types import Response


def _get_kwargs(
    id: float,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/locations/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
    | None
):
    if response.status_code == 200:
        response_200 = Location.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetLocationResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = GetLocationResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = GetLocationResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetLocationResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
]:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetLocationResponse401, GetLocationResponse404, GetLocationResponse429, GetLocationResponse500, Location]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
    | None
):
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetLocationResponse401, GetLocationResponse404, GetLocationResponse429, GetLocationResponse500, Location]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
]:
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetLocationResponse401, GetLocationResponse404, GetLocationResponse429, GetLocationResponse500, Location]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetLocationResponse401
    | GetLocationResponse404
    | GetLocationResponse429
    | GetLocationResponse500
    | Location
    | None
):
    """Retrieve a location

     Retrieves the details of an existing location based on ID.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetLocationResponse401, GetLocationResponse404, GetLocationResponse429, GetLocationResponse500, Location]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
