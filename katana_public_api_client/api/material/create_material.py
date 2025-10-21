from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_material_request import CreateMaterialRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.material import Material


def _get_kwargs(
    *,
    body: CreateMaterialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/materials",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | Material | None:
    if response.status_code == 200:
        response_200 = Material.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | Material]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMaterialRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Material]:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest): Request payload for creating a new raw material with
            variants and specifications Example: {'name': 'Stainless Steel Sheet 304', 'uom': 'm²',
            'category_name': 'Raw Materials', 'default_supplier_id': 1501, 'additional_info': 'Food-
            grade stainless steel, 1.5mm thickness', 'batch_tracked': True, 'is_sellable': False,
            'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'name':
            'Grade', 'values': ['304', '316']}, {'name': 'Thickness', 'values': ['1.5mm', '2.0mm',
            '3.0mm']}], 'variants': [{'sku': 'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price':
            45.0, 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name':
            'Grade', 'config_value': '304'}, {'config_name': 'Thickness', 'config_value':
            '1.5mm'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Material]]
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
    body: CreateMaterialRequest,
) -> DetailedErrorResponse | ErrorResponse | Material | None:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest): Request payload for creating a new raw material with
            variants and specifications Example: {'name': 'Stainless Steel Sheet 304', 'uom': 'm²',
            'category_name': 'Raw Materials', 'default_supplier_id': 1501, 'additional_info': 'Food-
            grade stainless steel, 1.5mm thickness', 'batch_tracked': True, 'is_sellable': False,
            'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'name':
            'Grade', 'values': ['304', '316']}, {'name': 'Thickness', 'values': ['1.5mm', '2.0mm',
            '3.0mm']}], 'variants': [{'sku': 'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price':
            45.0, 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name':
            'Grade', 'config_value': '304'}, {'config_name': 'Thickness', 'config_value':
            '1.5mm'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Material]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMaterialRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Material]:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest): Request payload for creating a new raw material with
            variants and specifications Example: {'name': 'Stainless Steel Sheet 304', 'uom': 'm²',
            'category_name': 'Raw Materials', 'default_supplier_id': 1501, 'additional_info': 'Food-
            grade stainless steel, 1.5mm thickness', 'batch_tracked': True, 'is_sellable': False,
            'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'name':
            'Grade', 'values': ['304', '316']}, {'name': 'Thickness', 'values': ['1.5mm', '2.0mm',
            '3.0mm']}], 'variants': [{'sku': 'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price':
            45.0, 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name':
            'Grade', 'config_value': '304'}, {'config_name': 'Thickness', 'config_value':
            '1.5mm'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Material]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateMaterialRequest,
) -> DetailedErrorResponse | ErrorResponse | Material | None:
    """Create a material

     Creates a material object.

    Args:
        body (CreateMaterialRequest): Request payload for creating a new raw material with
            variants and specifications Example: {'name': 'Stainless Steel Sheet 304', 'uom': 'm²',
            'category_name': 'Raw Materials', 'default_supplier_id': 1501, 'additional_info': 'Food-
            grade stainless steel, 1.5mm thickness', 'batch_tracked': True, 'is_sellable': False,
            'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'name':
            'Grade', 'values': ['304', '316']}, {'name': 'Thickness', 'values': ['1.5mm', '2.0mm',
            '3.0mm']}], 'variants': [{'sku': 'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price':
            45.0, 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name':
            'Grade', 'config_value': '304'}, {'config_name': 'Thickness', 'config_value':
            '1.5mm'}]}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Material]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
