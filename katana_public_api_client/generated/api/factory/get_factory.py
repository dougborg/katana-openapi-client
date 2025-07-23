from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.factory import Factory
from ...models.get_factory_response_401 import GetFactoryResponse401
from ...models.get_factory_response_429 import GetFactoryResponse429
from ...models.get_factory_response_500 import GetFactoryResponse500
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/factory",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Factory
    | GetFactoryResponse401
    | GetFactoryResponse429
    | GetFactoryResponse500
    | None
):
    if response.status_code == 200:
        response_200 = Factory.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetFactoryResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetFactoryResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetFactoryResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Factory | GetFactoryResponse401 | GetFactoryResponse429 | GetFactoryResponse500
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
) -> Response[
    Factory | GetFactoryResponse401 | GetFactoryResponse429 | GetFactoryResponse500
]:
    """Retrieve the current factory

     Returns the general information about the factory.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Factory, GetFactoryResponse401, GetFactoryResponse429, GetFactoryResponse500]]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> (
    Factory
    | GetFactoryResponse401
    | GetFactoryResponse429
    | GetFactoryResponse500
    | None
):
    """Retrieve the current factory

     Returns the general information about the factory.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Factory, GetFactoryResponse401, GetFactoryResponse429, GetFactoryResponse500]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Factory | GetFactoryResponse401 | GetFactoryResponse429 | GetFactoryResponse500
]:
    """Retrieve the current factory

     Returns the general information about the factory.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Factory, GetFactoryResponse401, GetFactoryResponse429, GetFactoryResponse500]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    Factory
    | GetFactoryResponse401
    | GetFactoryResponse429
    | GetFactoryResponse500
    | None
):
    """Retrieve the current factory

     Returns the general information about the factory.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Factory, GetFactoryResponse401, GetFactoryResponse429, GetFactoryResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
