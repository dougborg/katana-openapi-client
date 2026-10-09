from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.product import Product
from ...models.update_product_request import UpdateProductRequest
from ...models.update_product_x_custom_fields_format import (
    UpdateProductXCustomFieldsFormat,
)


def _get_kwargs(
    id: int,
    *,
    body: UpdateProductRequest,
    x_custom_fields_format: UpdateProductXCustomFieldsFormat | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_custom_fields_format, Unset):
        headers["X-Custom-Fields-Format"] = str(x_custom_fields_format)

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/products/{id}".format(
            id=quote(str(id), safe=""),
        ),
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
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    x_custom_fields_format: UpdateProductXCustomFieldsFormat | Unset = UNSET,
) -> Response[DetailedErrorResponse | ErrorResponse | Product]:
    """Update a product

     Updates the specified product by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        x_custom_fields_format (UpdateProductXCustomFieldsFormat | Unset):
        body (UpdateProductRequest): Request payload for updating an existing finished product's
            properties, configurations, and manufacturing specifications Example: {'name':
            'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Premium Kitchenware',
            'is_sellable': True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly':
            False, 'is_archived': False, 'default_supplier_id': 1501, 'additional_info': 'High-carbon
            stainless steel with ergonomic handles, dishwasher safe', 'batch_tracked': False,
            'serial_tracked': True, 'operations_in_sequence': True, 'purchase_uom': 'set',
            'purchase_uom_conversion_rate': 1.0, 'custom_field_collection_id': 5, 'configs': [{'name':
            'Piece Count', 'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material',
            'values': ['Wood', 'Steel', 'Composite']}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | Product]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    x_custom_fields_format: UpdateProductXCustomFieldsFormat | Unset = UNSET,
) -> DetailedErrorResponse | ErrorResponse | Product | None:
    """Update a product

     Updates the specified product by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        x_custom_fields_format (UpdateProductXCustomFieldsFormat | Unset):
        body (UpdateProductRequest): Request payload for updating an existing finished product's
            properties, configurations, and manufacturing specifications Example: {'name':
            'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Premium Kitchenware',
            'is_sellable': True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly':
            False, 'is_archived': False, 'default_supplier_id': 1501, 'additional_info': 'High-carbon
            stainless steel with ergonomic handles, dishwasher safe', 'batch_tracked': False,
            'serial_tracked': True, 'operations_in_sequence': True, 'purchase_uom': 'set',
            'purchase_uom_conversion_rate': 1.0, 'custom_field_collection_id': 5, 'configs': [{'name':
            'Piece Count', 'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material',
            'values': ['Wood', 'Steel', 'Composite']}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | Product
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    x_custom_fields_format: UpdateProductXCustomFieldsFormat | Unset = UNSET,
) -> Response[DetailedErrorResponse | ErrorResponse | Product]:
    """Update a product

     Updates the specified product by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        x_custom_fields_format (UpdateProductXCustomFieldsFormat | Unset):
        body (UpdateProductRequest): Request payload for updating an existing finished product's
            properties, configurations, and manufacturing specifications Example: {'name':
            'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Premium Kitchenware',
            'is_sellable': True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly':
            False, 'is_archived': False, 'default_supplier_id': 1501, 'additional_info': 'High-carbon
            stainless steel with ergonomic handles, dishwasher safe', 'batch_tracked': False,
            'serial_tracked': True, 'operations_in_sequence': True, 'purchase_uom': 'set',
            'purchase_uom_conversion_rate': 1.0, 'custom_field_collection_id': 5, 'configs': [{'name':
            'Piece Count', 'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material',
            'values': ['Wood', 'Steel', 'Composite']}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[DetailedErrorResponse | ErrorResponse | Product]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
        x_custom_fields_format=x_custom_fields_format,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateProductRequest,
    x_custom_fields_format: UpdateProductXCustomFieldsFormat | Unset = UNSET,
) -> DetailedErrorResponse | ErrorResponse | Product | None:
    """Update a product

     Updates the specified product by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        x_custom_fields_format (UpdateProductXCustomFieldsFormat | Unset):
        body (UpdateProductRequest): Request payload for updating an existing finished product's
            properties, configurations, and manufacturing specifications Example: {'name':
            'Professional Kitchen Knife Set', 'uom': 'set', 'category_name': 'Premium Kitchenware',
            'is_sellable': True, 'is_producible': True, 'is_purchasable': False, 'is_auto_assembly':
            False, 'is_archived': False, 'default_supplier_id': 1501, 'additional_info': 'High-carbon
            stainless steel with ergonomic handles, dishwasher safe', 'batch_tracked': False,
            'serial_tracked': True, 'operations_in_sequence': True, 'purchase_uom': 'set',
            'purchase_uom_conversion_rate': 1.0, 'custom_field_collection_id': 5, 'configs': [{'name':
            'Piece Count', 'values': ['6-piece', '8-piece', '12-piece']}, {'name': 'Handle Material',
            'values': ['Wood', 'Steel', 'Composite']}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        DetailedErrorResponse | ErrorResponse | Product
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
            x_custom_fields_format=x_custom_fields_format,
        )
    ).parsed
