from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_customer_address_request import CreateCustomerAddressRequest
from ...models.create_customer_address_response_401 import (
    CreateCustomerAddressResponse401,
)
from ...models.create_customer_address_response_422 import (
    CreateCustomerAddressResponse422,
)
from ...models.create_customer_address_response_429 import (
    CreateCustomerAddressResponse429,
)
from ...models.create_customer_address_response_500 import (
    CreateCustomerAddressResponse500,
)
from ...models.customer_address import CustomerAddress
from ...types import Response


def _get_kwargs(
    *,
    body: CreateCustomerAddressRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/customer_addresses",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
    | None
):
    if response.status_code == 200:
        response_200 = CustomerAddress.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateCustomerAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateCustomerAddressResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateCustomerAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateCustomerAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
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
    body: CreateCustomerAddressRequest,
) -> Response[
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
]:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateCustomerAddressResponse401, CreateCustomerAddressResponse422, CreateCustomerAddressResponse429, CreateCustomerAddressResponse500, CustomerAddress]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerAddressRequest,
) -> (
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
    | None
):
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateCustomerAddressResponse401, CreateCustomerAddressResponse422, CreateCustomerAddressResponse429, CreateCustomerAddressResponse500, CustomerAddress]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerAddressRequest,
) -> Response[
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
]:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateCustomerAddressResponse401, CreateCustomerAddressResponse422, CreateCustomerAddressResponse429, CreateCustomerAddressResponse500, CustomerAddress]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerAddressRequest,
) -> (
    CreateCustomerAddressResponse401
    | CreateCustomerAddressResponse422
    | CreateCustomerAddressResponse429
    | CreateCustomerAddressResponse500
    | CustomerAddress
    | None
):
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateCustomerAddressResponse401, CreateCustomerAddressResponse422, CreateCustomerAddressResponse429, CreateCustomerAddressResponse500, CustomerAddress]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
