from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_variant_request import CreateVariantRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.variant import Variant


def _get_kwargs(
    *,
    body: CreateVariantRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/variants",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | Variant | None:
    if response.status_code == 200:
        response_200 = Variant.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | Variant]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVariantRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Variant]:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest): Request payload for creating a new product or material
            variant with specific SKU and configuration attributes Example: {'sku': 'KNF-PRO-12PC-WD',
            'sales_price': 399.99, 'purchase_price': 200.0, 'product_id': 101, 'material_id': None,
            'supplier_item_codes': ['SUP-KNF-12PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 10, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Wood'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '5 years'}, {'field_name': 'Care
            Instructions', 'field_value': 'Hand wash only'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Variant]]
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
    body: CreateVariantRequest,
) -> DetailedErrorResponse | ErrorResponse | Variant | None:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest): Request payload for creating a new product or material
            variant with specific SKU and configuration attributes Example: {'sku': 'KNF-PRO-12PC-WD',
            'sales_price': 399.99, 'purchase_price': 200.0, 'product_id': 101, 'material_id': None,
            'supplier_item_codes': ['SUP-KNF-12PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 10, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Wood'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '5 years'}, {'field_name': 'Care
            Instructions', 'field_value': 'Hand wash only'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Variant]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVariantRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Variant]:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest): Request payload for creating a new product or material
            variant with specific SKU and configuration attributes Example: {'sku': 'KNF-PRO-12PC-WD',
            'sales_price': 399.99, 'purchase_price': 200.0, 'product_id': 101, 'material_id': None,
            'supplier_item_codes': ['SUP-KNF-12PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 10, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Wood'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '5 years'}, {'field_name': 'Care
            Instructions', 'field_value': 'Hand wash only'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Variant]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateVariantRequest,
) -> DetailedErrorResponse | ErrorResponse | Variant | None:
    """Create a variant

     Creates a new variant object. Note that you can create variants for both products and materials.
        In order for Katana to know which one you are creating,
        you have to specify either product_id or material_id, not both.

    Args:
        body (CreateVariantRequest): Request payload for creating a new product or material
            variant with specific SKU and configuration attributes Example: {'sku': 'KNF-PRO-12PC-WD',
            'sales_price': 399.99, 'purchase_price': 200.0, 'product_id': 101, 'material_id': None,
            'supplier_item_codes': ['SUP-KNF-12PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 10, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Wood'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '5 years'}, {'field_name': 'Care
            Instructions', 'field_value': 'Hand wash only'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Variant]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
