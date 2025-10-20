from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_customer_address_request import CreateCustomerAddressRequest
from ...models.customer_address import CustomerAddress
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse


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
) -> CustomerAddress | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = CustomerAddress.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = DetailedErrorResponse.from_dict(response.json())

        return response_422

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
) -> Response[CustomerAddress | DetailedErrorResponse | ErrorResponse]:
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
) -> Response[CustomerAddress | DetailedErrorResponse | ErrorResponse]:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest): Request payload for creating a new customer address
            with complete contact and location information Example: {'customer_id': 2003,
            'entity_type': 'shipping', 'first_name': 'Maria', 'last_name': 'Garcia', 'company': 'Cafe
            Central', 'phone': '+1-555-0127', 'line_1': '789 Main Street', 'line_2': 'Unit 5', 'city':
            'San Francisco', 'state': 'CA', 'zip': '94102', 'country': 'USA', 'is_default': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddress, DetailedErrorResponse, ErrorResponse]]
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
) -> CustomerAddress | DetailedErrorResponse | ErrorResponse | None:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest): Request payload for creating a new customer address
            with complete contact and location information Example: {'customer_id': 2003,
            'entity_type': 'shipping', 'first_name': 'Maria', 'last_name': 'Garcia', 'company': 'Cafe
            Central', 'phone': '+1-555-0127', 'line_1': '789 Main Street', 'line_2': 'Unit 5', 'city':
            'San Francisco', 'state': 'CA', 'zip': '94102', 'country': 'USA', 'is_default': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddress, DetailedErrorResponse, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateCustomerAddressRequest,
) -> Response[CustomerAddress | DetailedErrorResponse | ErrorResponse]:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest): Request payload for creating a new customer address
            with complete contact and location information Example: {'customer_id': 2003,
            'entity_type': 'shipping', 'first_name': 'Maria', 'last_name': 'Garcia', 'company': 'Cafe
            Central', 'phone': '+1-555-0127', 'line_1': '789 Main Street', 'line_2': 'Unit 5', 'city':
            'San Francisco', 'state': 'CA', 'zip': '94102', 'country': 'USA', 'is_default': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddress, DetailedErrorResponse, ErrorResponse]]
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
) -> CustomerAddress | DetailedErrorResponse | ErrorResponse | None:
    """Create a customer address

     Creates a new customer address.

    Args:
        body (CreateCustomerAddressRequest): Request payload for creating a new customer address
            with complete contact and location information Example: {'customer_id': 2003,
            'entity_type': 'shipping', 'first_name': 'Maria', 'last_name': 'Garcia', 'company': 'Cafe
            Central', 'phone': '+1-555-0127', 'line_1': '789 Main Street', 'line_2': 'Unit 5', 'city':
            'San Francisco', 'state': 'CA', 'zip': '94102', 'country': 'USA', 'is_default': True}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddress, DetailedErrorResponse, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
