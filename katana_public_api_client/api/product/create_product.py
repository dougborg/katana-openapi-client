from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_product_request import CreateProductRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.product import Product


def _get_kwargs(
    *,
    body: CreateProductRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/products",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | Product | None:
    if response.status_code == 200:
        response_200 = Product.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | Product]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateProductRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Product]:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest): Request payload for creating a new finished product with
            variants, configurations, and manufacturing specifications Example: {'name': 'Professional
            Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchen Equipment', 'is_sellable':
            True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False,
            'additional_info': 'High-quality steel construction with ergonomic handles',
            'batch_tracked': False, 'serial_tracked': True, 'operations_in_sequence': True,
            'lead_time': 14, 'minimum_order_quantity': 1, 'configs': [{'name': 'Piece Count',
            'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values':
            ['Steel', 'Wooden', 'Composite']}], 'variants': [{'sku': 'KNF-PRO-8PC-STL', 'sales_price':
            299.99, 'purchase_price': 150.0, 'supplier_item_codes': ['KNF-8PC-STEEL-001'],
            'lead_time': 14, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Piece
            Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Product]]
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
    body: CreateProductRequest,
) -> DetailedErrorResponse | ErrorResponse | Product | None:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest): Request payload for creating a new finished product with
            variants, configurations, and manufacturing specifications Example: {'name': 'Professional
            Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchen Equipment', 'is_sellable':
            True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False,
            'additional_info': 'High-quality steel construction with ergonomic handles',
            'batch_tracked': False, 'serial_tracked': True, 'operations_in_sequence': True,
            'lead_time': 14, 'minimum_order_quantity': 1, 'configs': [{'name': 'Piece Count',
            'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values':
            ['Steel', 'Wooden', 'Composite']}], 'variants': [{'sku': 'KNF-PRO-8PC-STL', 'sales_price':
            299.99, 'purchase_price': 150.0, 'supplier_item_codes': ['KNF-8PC-STEEL-001'],
            'lead_time': 14, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Piece
            Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Product]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateProductRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Product]:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest): Request payload for creating a new finished product with
            variants, configurations, and manufacturing specifications Example: {'name': 'Professional
            Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchen Equipment', 'is_sellable':
            True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False,
            'additional_info': 'High-quality steel construction with ergonomic handles',
            'batch_tracked': False, 'serial_tracked': True, 'operations_in_sequence': True,
            'lead_time': 14, 'minimum_order_quantity': 1, 'configs': [{'name': 'Piece Count',
            'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values':
            ['Steel', 'Wooden', 'Composite']}], 'variants': [{'sku': 'KNF-PRO-8PC-STL', 'sales_price':
            299.99, 'purchase_price': 150.0, 'supplier_item_codes': ['KNF-8PC-STEEL-001'],
            'lead_time': 14, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Piece
            Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Product]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateProductRequest,
) -> DetailedErrorResponse | ErrorResponse | Product | None:
    """Create a product

     Creates a product object.

    Args:
        body (CreateProductRequest): Request payload for creating a new finished product with
            variants, configurations, and manufacturing specifications Example: {'name': 'Professional
            Kitchen Knife Set', 'uom': 'set', 'category_name': 'Kitchen Equipment', 'is_sellable':
            True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly': False,
            'additional_info': 'High-quality steel construction with ergonomic handles',
            'batch_tracked': False, 'serial_tracked': True, 'operations_in_sequence': True,
            'lead_time': 14, 'minimum_order_quantity': 1, 'configs': [{'name': 'Piece Count',
            'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material', 'values':
            ['Steel', 'Wooden', 'Composite']}], 'variants': [{'sku': 'KNF-PRO-8PC-STL', 'sales_price':
            299.99, 'purchase_price': 150.0, 'supplier_item_codes': ['KNF-8PC-STEEL-001'],
            'lead_time': 14, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Piece
            Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Product]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
