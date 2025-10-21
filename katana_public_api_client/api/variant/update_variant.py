from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.update_variant_request import UpdateVariantRequest
from ...models.variant import Variant


def _get_kwargs(
    id: int,
    *,
    body: UpdateVariantRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/variants/{id}",
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
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVariantRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Variant]:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest): Request payload for updating product variant details
            including pricing, configuration, and inventory information Example: {'sku': 'KNF-PRO-8PC-
            UPD', 'sales_price': 319.99, 'purchase_price': 160.0, 'product_id': 101, 'material_id':
            None, 'supplier_item_codes': ['SUP-KNF-8PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 5, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '8-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Premium Steel'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '7 years'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Variant]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVariantRequest,
) -> DetailedErrorResponse | ErrorResponse | Variant | None:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest): Request payload for updating product variant details
            including pricing, configuration, and inventory information Example: {'sku': 'KNF-PRO-8PC-
            UPD', 'sales_price': 319.99, 'purchase_price': 160.0, 'product_id': 101, 'material_id':
            None, 'supplier_item_codes': ['SUP-KNF-8PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 5, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '8-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Premium Steel'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '7 years'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Variant]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVariantRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Variant]:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest): Request payload for updating product variant details
            including pricing, configuration, and inventory information Example: {'sku': 'KNF-PRO-8PC-
            UPD', 'sales_price': 319.99, 'purchase_price': 160.0, 'product_id': 101, 'material_id':
            None, 'supplier_item_codes': ['SUP-KNF-8PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 5, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '8-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Premium Steel'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '7 years'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Variant]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateVariantRequest,
) -> DetailedErrorResponse | ErrorResponse | Variant | None:
    """Update a variant

     Updates the specified variant by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateVariantRequest): Request payload for updating product variant details
            including pricing, configuration, and inventory information Example: {'sku': 'KNF-PRO-8PC-
            UPD', 'sales_price': 319.99, 'purchase_price': 160.0, 'product_id': 101, 'material_id':
            None, 'supplier_item_codes': ['SUP-KNF-8PC-002'], 'internal_barcode': 'INT-KNF-002',
            'registered_barcode': '789123456790', 'lead_time': 5, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '8-piece'},
            {'config_name': 'Handle Material', 'config_value': 'Premium Steel'}], 'custom_fields':
            [{'field_name': 'Warranty Period', 'field_value': '7 years'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Variant]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
