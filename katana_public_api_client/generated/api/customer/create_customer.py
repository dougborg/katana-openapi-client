from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_customer_request import CreateCustomerRequest
from ...models.create_customer_response_401 import CreateCustomerResponse401
from ...models.create_customer_response_429 import CreateCustomerResponse429
from ...models.create_customer_response_500 import CreateCustomerResponse500
from ...models.customer import Customer
from ...types import Response


def _get_kwargs(
    *,
    body: CreateCustomerRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/customers",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
    | None
):
    if response.status_code == 200:
        response_200 = Customer.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateCustomerResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = CreateCustomerResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateCustomerResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
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
    body: CreateCustomerRequest,
) -> Response[
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
]:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateCustomerResponse401, CreateCustomerResponse429, CreateCustomerResponse500, Customer]]
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
    body: CreateCustomerRequest,
) -> (
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
    | None
):
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateCustomerResponse401, CreateCustomerResponse429, CreateCustomerResponse500, Customer]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerRequest,
) -> Response[
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
]:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateCustomerResponse401, CreateCustomerResponse429, CreateCustomerResponse500, Customer]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerRequest,
) -> (
    CreateCustomerResponse401
    | CreateCustomerResponse429
    | CreateCustomerResponse500
    | Customer
    | None
):
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateCustomerResponse401, CreateCustomerResponse429, CreateCustomerResponse500, Customer]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
