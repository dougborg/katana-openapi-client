from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_service_response_401 import GetServiceResponse401
from ...models.get_service_response_429 import GetServiceResponse429
from ...models.get_service_response_500 import GetServiceResponse500
from ...models.service import Service
from ...types import Response


def _get_kwargs(
    service_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/services/{service_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
    | None
):
    if response.status_code == 200:
        response_200 = Service.from_dict(response.json())

        return response_200
    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404
    if response.status_code == 401:
        response_401 = GetServiceResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetServiceResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetServiceResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
]:
    """Get Service

     Retrieve a single Service by its ID. (See: [Get
    Service](https://developer.katanamrp.com/reference/getservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, GetServiceResponse401, GetServiceResponse429, GetServiceResponse500, Service]]
    """

    kwargs = _get_kwargs(
        service_id=service_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
    | None
):
    """Get Service

     Retrieve a single Service by its ID. (See: [Get
    Service](https://developer.katanamrp.com/reference/getservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, GetServiceResponse401, GetServiceResponse429, GetServiceResponse500, Service]
    """

    return sync_detailed(
        service_id=service_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
]:
    """Get Service

     Retrieve a single Service by its ID. (See: [Get
    Service](https://developer.katanamrp.com/reference/getservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, GetServiceResponse401, GetServiceResponse429, GetServiceResponse500, Service]]
    """

    kwargs = _get_kwargs(
        service_id=service_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    service_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | GetServiceResponse401
    | GetServiceResponse429
    | GetServiceResponse500
    | Service
    | None
):
    """Get Service

     Retrieve a single Service by its ID. (See: [Get
    Service](https://developer.katanamrp.com/reference/getservice))

    Args:
        service_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, GetServiceResponse401, GetServiceResponse429, GetServiceResponse500, Service]
    """

    return (
        await asyncio_detailed(
            service_id=service_id,
            client=client,
        )
    ).parsed
