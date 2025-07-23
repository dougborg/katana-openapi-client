from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_services_response_401 import GetAllServicesResponse401
from ...models.get_all_services_response_429 import GetAllServicesResponse429
from ...models.get_all_services_response_500 import GetAllServicesResponse500
from ...models.service_list_response import ServiceListResponse
from ...types import Response


def _get_kwargs() -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/services",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
    | None
):
    if response.status_code == 200:
        response_200 = ServiceListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllServicesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllServicesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllServicesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
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
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
]:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllServicesResponse401, GetAllServicesResponse429, GetAllServicesResponse500, ServiceListResponse]]
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
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
    | None
):
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllServicesResponse401, GetAllServicesResponse429, GetAllServicesResponse500, ServiceListResponse]
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
]:
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllServicesResponse401, GetAllServicesResponse429, GetAllServicesResponse500, ServiceListResponse]]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetAllServicesResponse401
    | GetAllServicesResponse429
    | GetAllServicesResponse500
    | ServiceListResponse
    | None
):
    """Get All Services

     Retrieve a list of all Service objects. (See: [Get All
    Services](https://developer.katanamrp.com/reference/getallservices))

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllServicesResponse401, GetAllServicesResponse429, GetAllServicesResponse500, ServiceListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
