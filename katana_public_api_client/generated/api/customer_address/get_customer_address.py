from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.customer_address import CustomerAddress
from ...models.get_customer_address_response_401 import GetCustomerAddressResponse401
from ...models.get_customer_address_response_404 import GetCustomerAddressResponse404
from ...models.get_customer_address_response_429 import GetCustomerAddressResponse429
from ...models.get_customer_address_response_500 import GetCustomerAddressResponse500
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/customer_addresses/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CustomerAddress.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetCustomerAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = GetCustomerAddressResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = GetCustomerAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetCustomerAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
]:
    """Get a customer address

     Returns a specific customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddress, GetCustomerAddressResponse401, GetCustomerAddressResponse404, GetCustomerAddressResponse429, GetCustomerAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
    | None
):
    """Get a customer address

     Returns a specific customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddress, GetCustomerAddressResponse401, GetCustomerAddressResponse404, GetCustomerAddressResponse429, GetCustomerAddressResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
]:
    """Get a customer address

     Returns a specific customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddress, GetCustomerAddressResponse401, GetCustomerAddressResponse404, GetCustomerAddressResponse429, GetCustomerAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    CustomerAddress
    | GetCustomerAddressResponse401
    | GetCustomerAddressResponse404
    | GetCustomerAddressResponse429
    | GetCustomerAddressResponse500
    | None
):
    """Get a customer address

     Returns a specific customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddress, GetCustomerAddressResponse401, GetCustomerAddressResponse404, GetCustomerAddressResponse429, GetCustomerAddressResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
