from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_customer_request import CreateCustomerRequest
from ...models.customer import Customer
from ...models.error_response import ErrorResponse


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
) -> Customer | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = Customer.from_dict(response.json())

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
) -> Response[Customer | ErrorResponse]:
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
) -> Response[Customer | ErrorResponse]:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest): Request payload for creating a new customer with contact and
            business information Example: {'name': 'Gourmet Bistro Group', 'first_name': 'Elena',
            'last_name': 'Rodriguez', 'company': 'Gourmet Bistro Group Inc', 'email':
            'procurement@gourmetbistro.com', 'phone': '+1-555-0125', 'comment': 'Premium restaurant
            chain - priority orders', 'currency': 'USD', 'reference_id': 'GBG-2024-003', 'category':
            'Fine Dining', 'discount_rate': 7.5}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Customer, ErrorResponse]]
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
) -> Customer | ErrorResponse | None:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest): Request payload for creating a new customer with contact and
            business information Example: {'name': 'Gourmet Bistro Group', 'first_name': 'Elena',
            'last_name': 'Rodriguez', 'company': 'Gourmet Bistro Group Inc', 'email':
            'procurement@gourmetbistro.com', 'phone': '+1-555-0125', 'comment': 'Premium restaurant
            chain - priority orders', 'currency': 'USD', 'reference_id': 'GBG-2024-003', 'category':
            'Fine Dining', 'discount_rate': 7.5}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Customer, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerRequest,
) -> Response[Customer | ErrorResponse]:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest): Request payload for creating a new customer with contact and
            business information Example: {'name': 'Gourmet Bistro Group', 'first_name': 'Elena',
            'last_name': 'Rodriguez', 'company': 'Gourmet Bistro Group Inc', 'email':
            'procurement@gourmetbistro.com', 'phone': '+1-555-0125', 'comment': 'Premium restaurant
            chain - priority orders', 'currency': 'USD', 'reference_id': 'GBG-2024-003', 'category':
            'Fine Dining', 'discount_rate': 7.5}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[Customer, ErrorResponse]]
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
) -> Customer | ErrorResponse | None:
    """Create a customer

     Creates a new customer.

    Args:
        body (CreateCustomerRequest): Request payload for creating a new customer with contact and
            business information Example: {'name': 'Gourmet Bistro Group', 'first_name': 'Elena',
            'last_name': 'Rodriguez', 'company': 'Gourmet Bistro Group Inc', 'email':
            'procurement@gourmetbistro.com', 'phone': '+1-555-0125', 'comment': 'Premium restaurant
            chain - priority orders', 'currency': 'USD', 'reference_id': 'GBG-2024-003', 'category':
            'Fine Dining', 'discount_rate': 7.5}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[Customer, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
