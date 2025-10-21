from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_sales_order_request import CreateSalesOrderRequest
from ...models.error_response import ErrorResponse
from ...models.sales_order import SalesOrder


def _get_kwargs(
    *,
    body: CreateSalesOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_orders",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesOrder | None:
    if response.status_code == 200:
        response_200 = SalesOrder.from_dict(response.json())

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
) -> Response[ErrorResponse | SalesOrder]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRequest,
) -> Response[ErrorResponse | SalesOrder]:
    """Create a sales order

     Creates a new sales order object.

    Args:
        body (CreateSalesOrderRequest): Request payload for creating a new sales order with
            customer information, order lines, and delivery details Example: {'order_no':
            'SO-2024-002', 'customer_id': 1501, 'sales_order_rows': [{'quantity': 3, 'variant_id':
            2101, 'tax_rate_id': 301, 'location_id': 1, 'price_per_unit': 599.99, 'total_discount':
            50.0, 'attributes': [{'key': 'engrave_text', 'value': 'Professional Kitchen'}, {'key':
            'rush_order', 'value': 'true'}]}], 'tracking_number': None, 'tracking_number_url': None,
            'addresses': [{'entity_type': 'billing', 'first_name': 'David', 'last_name': 'Wilson',
            'company': "Wilson's Catering", 'line_1': '456 Commerce Ave', 'city': 'Seattle', 'state':
            'WA', 'zip': '98101', 'country': 'US'}, {'entity_type': 'shipping', 'first_name': 'David',
            'last_name': 'Wilson', 'company': "Wilson's Catering", 'line_1': '789 Industrial Blvd',
            'city': 'Seattle', 'state': 'WA', 'zip': '98102', 'country': 'US'}], 'order_created_date':
            '2024-01-16T09:00:00Z', 'delivery_date': '2024-01-23T15:00:00Z', 'currency': 'USD',
            'location_id': 1, 'status': 'PENDING', 'additional_info': 'Customer prefers morning
            delivery', 'customer_ref': 'WC-ORDER-2024-003', 'ecommerce_order_type': 'wholesale',
            'ecommerce_store_name': 'B2B Portal', 'ecommerce_order_id': 'B2B-7891-2024'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrder]]
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
    body: CreateSalesOrderRequest,
) -> ErrorResponse | SalesOrder | None:
    """Create a sales order

     Creates a new sales order object.

    Args:
        body (CreateSalesOrderRequest): Request payload for creating a new sales order with
            customer information, order lines, and delivery details Example: {'order_no':
            'SO-2024-002', 'customer_id': 1501, 'sales_order_rows': [{'quantity': 3, 'variant_id':
            2101, 'tax_rate_id': 301, 'location_id': 1, 'price_per_unit': 599.99, 'total_discount':
            50.0, 'attributes': [{'key': 'engrave_text', 'value': 'Professional Kitchen'}, {'key':
            'rush_order', 'value': 'true'}]}], 'tracking_number': None, 'tracking_number_url': None,
            'addresses': [{'entity_type': 'billing', 'first_name': 'David', 'last_name': 'Wilson',
            'company': "Wilson's Catering", 'line_1': '456 Commerce Ave', 'city': 'Seattle', 'state':
            'WA', 'zip': '98101', 'country': 'US'}, {'entity_type': 'shipping', 'first_name': 'David',
            'last_name': 'Wilson', 'company': "Wilson's Catering", 'line_1': '789 Industrial Blvd',
            'city': 'Seattle', 'state': 'WA', 'zip': '98102', 'country': 'US'}], 'order_created_date':
            '2024-01-16T09:00:00Z', 'delivery_date': '2024-01-23T15:00:00Z', 'currency': 'USD',
            'location_id': 1, 'status': 'PENDING', 'additional_info': 'Customer prefers morning
            delivery', 'customer_ref': 'WC-ORDER-2024-003', 'ecommerce_order_type': 'wholesale',
            'ecommerce_store_name': 'B2B Portal', 'ecommerce_order_id': 'B2B-7891-2024'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrder]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRequest,
) -> Response[ErrorResponse | SalesOrder]:
    """Create a sales order

     Creates a new sales order object.

    Args:
        body (CreateSalesOrderRequest): Request payload for creating a new sales order with
            customer information, order lines, and delivery details Example: {'order_no':
            'SO-2024-002', 'customer_id': 1501, 'sales_order_rows': [{'quantity': 3, 'variant_id':
            2101, 'tax_rate_id': 301, 'location_id': 1, 'price_per_unit': 599.99, 'total_discount':
            50.0, 'attributes': [{'key': 'engrave_text', 'value': 'Professional Kitchen'}, {'key':
            'rush_order', 'value': 'true'}]}], 'tracking_number': None, 'tracking_number_url': None,
            'addresses': [{'entity_type': 'billing', 'first_name': 'David', 'last_name': 'Wilson',
            'company': "Wilson's Catering", 'line_1': '456 Commerce Ave', 'city': 'Seattle', 'state':
            'WA', 'zip': '98101', 'country': 'US'}, {'entity_type': 'shipping', 'first_name': 'David',
            'last_name': 'Wilson', 'company': "Wilson's Catering", 'line_1': '789 Industrial Blvd',
            'city': 'Seattle', 'state': 'WA', 'zip': '98102', 'country': 'US'}], 'order_created_date':
            '2024-01-16T09:00:00Z', 'delivery_date': '2024-01-23T15:00:00Z', 'currency': 'USD',
            'location_id': 1, 'status': 'PENDING', 'additional_info': 'Customer prefers morning
            delivery', 'customer_ref': 'WC-ORDER-2024-003', 'ecommerce_order_type': 'wholesale',
            'ecommerce_store_name': 'B2B Portal', 'ecommerce_order_id': 'B2B-7891-2024'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrder]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRequest,
) -> ErrorResponse | SalesOrder | None:
    """Create a sales order

     Creates a new sales order object.

    Args:
        body (CreateSalesOrderRequest): Request payload for creating a new sales order with
            customer information, order lines, and delivery details Example: {'order_no':
            'SO-2024-002', 'customer_id': 1501, 'sales_order_rows': [{'quantity': 3, 'variant_id':
            2101, 'tax_rate_id': 301, 'location_id': 1, 'price_per_unit': 599.99, 'total_discount':
            50.0, 'attributes': [{'key': 'engrave_text', 'value': 'Professional Kitchen'}, {'key':
            'rush_order', 'value': 'true'}]}], 'tracking_number': None, 'tracking_number_url': None,
            'addresses': [{'entity_type': 'billing', 'first_name': 'David', 'last_name': 'Wilson',
            'company': "Wilson's Catering", 'line_1': '456 Commerce Ave', 'city': 'Seattle', 'state':
            'WA', 'zip': '98101', 'country': 'US'}, {'entity_type': 'shipping', 'first_name': 'David',
            'last_name': 'Wilson', 'company': "Wilson's Catering", 'line_1': '789 Industrial Blvd',
            'city': 'Seattle', 'state': 'WA', 'zip': '98102', 'country': 'US'}], 'order_created_date':
            '2024-01-16T09:00:00Z', 'delivery_date': '2024-01-23T15:00:00Z', 'currency': 'USD',
            'location_id': 1, 'status': 'PENDING', 'additional_info': 'Customer prefers morning
            delivery', 'customer_ref': 'WC-ORDER-2024-003', 'ecommerce_order_type': 'wholesale',
            'ecommerce_store_name': 'B2B Portal', 'ecommerce_order_id': 'B2B-7891-2024'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrder]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
