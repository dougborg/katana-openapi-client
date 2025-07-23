from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_customer_address_response_401 import (
    DeleteCustomerAddressResponse401,
)
from ...models.delete_customer_address_response_404 import (
    DeleteCustomerAddressResponse404,
)
from ...models.delete_customer_address_response_429 import (
    DeleteCustomerAddressResponse429,
)
from ...models.delete_customer_address_response_500 import (
    DeleteCustomerAddressResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/customer_addresses/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
    | None
):
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200
    if response.status_code == 401:
        response_401 = DeleteCustomerAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteCustomerAddressResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteCustomerAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteCustomerAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
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
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
]:
    """Delete a customer address

     Deletes a customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteCustomerAddressResponse401, DeleteCustomerAddressResponse404, DeleteCustomerAddressResponse429, DeleteCustomerAddressResponse500]]
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
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
    | None
):
    """Delete a customer address

     Deletes a customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteCustomerAddressResponse401, DeleteCustomerAddressResponse404, DeleteCustomerAddressResponse429, DeleteCustomerAddressResponse500]
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
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
]:
    """Delete a customer address

     Deletes a customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteCustomerAddressResponse401, DeleteCustomerAddressResponse404, DeleteCustomerAddressResponse429, DeleteCustomerAddressResponse500]]
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
    Any
    | DeleteCustomerAddressResponse401
    | DeleteCustomerAddressResponse404
    | DeleteCustomerAddressResponse429
    | DeleteCustomerAddressResponse500
    | None
):
    """Delete a customer address

     Deletes a customer address.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteCustomerAddressResponse401, DeleteCustomerAddressResponse404, DeleteCustomerAddressResponse429, DeleteCustomerAddressResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
