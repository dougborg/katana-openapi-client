from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_sales_order_address_request import CreateSalesOrderAddressRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_order_address import SalesOrderAddress


def _get_kwargs(
    *,
    body: CreateSalesOrderAddressRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_order_addresses",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesOrderAddress | None:
    if response.status_code == 200:
        response_200 = SalesOrderAddress.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderAddress]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderAddressRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderAddress]:
    """Create a sales order address

     Creates a new sales order address (billing or shipping).

    Args:
        body (CreateSalesOrderAddressRequest): Request payload for creating a new sales order
            address Example: {'sales_order_id': 2001, 'entity_type': 'shipping', 'first_name': 'John',
            'last_name': 'Johnson', 'company': "Johnson's Restaurant", 'address_line_1': '123 Main
            Street', 'city': 'Portland', 'state': 'OR', 'zip': '97201', 'country': 'US', 'phone':
            '+1-555-0123'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderAddress]]
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
    body: CreateSalesOrderAddressRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderAddress | None:
    """Create a sales order address

     Creates a new sales order address (billing or shipping).

    Args:
        body (CreateSalesOrderAddressRequest): Request payload for creating a new sales order
            address Example: {'sales_order_id': 2001, 'entity_type': 'shipping', 'first_name': 'John',
            'last_name': 'Johnson', 'company': "Johnson's Restaurant", 'address_line_1': '123 Main
            Street', 'city': 'Portland', 'state': 'OR', 'zip': '97201', 'country': 'US', 'phone':
            '+1-555-0123'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderAddress]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderAddressRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderAddress]:
    """Create a sales order address

     Creates a new sales order address (billing or shipping).

    Args:
        body (CreateSalesOrderAddressRequest): Request payload for creating a new sales order
            address Example: {'sales_order_id': 2001, 'entity_type': 'shipping', 'first_name': 'John',
            'last_name': 'Johnson', 'company': "Johnson's Restaurant", 'address_line_1': '123 Main
            Street', 'city': 'Portland', 'state': 'OR', 'zip': '97201', 'country': 'US', 'phone':
            '+1-555-0123'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderAddress]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderAddressRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderAddress | None:
    """Create a sales order address

     Creates a new sales order address (billing or shipping).

    Args:
        body (CreateSalesOrderAddressRequest): Request payload for creating a new sales order
            address Example: {'sales_order_id': 2001, 'entity_type': 'shipping', 'first_name': 'John',
            'last_name': 'Johnson', 'company': "Johnson's Restaurant", 'address_line_1': '123 Main
            Street', 'city': 'Portland', 'state': 'OR', 'zip': '97201', 'country': 'US', 'phone':
            '+1-555-0123'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderAddress]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
