from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.material import Material
from ...models.update_material_request import UpdateMaterialRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdateMaterialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/materials/{id}",
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
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateMaterialRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Material]:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest): Request payload for updating an existing raw material's
            properties and specifications Example: {'name': 'Stainless Steel Sheet 304 - Updated',
            'uom': 'm²', 'category_name': 'Premium Raw Materials', 'default_supplier_id': 1502,
            'additional_info': 'Food-grade stainless steel, 1.5mm thickness - Updated specifications',
            'batch_tracked': True, 'is_sellable': False, 'is_archived': False, 'purchase_uom':
            'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'id': 101, 'name': 'Grade',
            'values': ['304', '316', '430']}, {'name': 'Finish', 'values': ['Brushed', 'Mirror',
            'Matte']}], 'custom_field_collection_id': 201}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Material]]
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
    body: UpdateMaterialRequest,
) -> DetailedErrorResponse | ErrorResponse | Material | None:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest): Request payload for updating an existing raw material's
            properties and specifications Example: {'name': 'Stainless Steel Sheet 304 - Updated',
            'uom': 'm²', 'category_name': 'Premium Raw Materials', 'default_supplier_id': 1502,
            'additional_info': 'Food-grade stainless steel, 1.5mm thickness - Updated specifications',
            'batch_tracked': True, 'is_sellable': False, 'is_archived': False, 'purchase_uom':
            'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'id': 101, 'name': 'Grade',
            'values': ['304', '316', '430']}, {'name': 'Finish', 'values': ['Brushed', 'Mirror',
            'Matte']}], 'custom_field_collection_id': 201}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Material]
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
    body: UpdateMaterialRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | Material]:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest): Request payload for updating an existing raw material's
            properties and specifications Example: {'name': 'Stainless Steel Sheet 304 - Updated',
            'uom': 'm²', 'category_name': 'Premium Raw Materials', 'default_supplier_id': 1502,
            'additional_info': 'Food-grade stainless steel, 1.5mm thickness - Updated specifications',
            'batch_tracked': True, 'is_sellable': False, 'is_archived': False, 'purchase_uom':
            'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'id': 101, 'name': 'Grade',
            'values': ['304', '316', '430']}, {'name': 'Finish', 'values': ['Brushed', 'Mirror',
            'Matte']}], 'custom_field_collection_id': 201}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Material]]
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
    body: UpdateMaterialRequest,
) -> DetailedErrorResponse | ErrorResponse | Material | None:
    """Update a material

     Updates the specified material by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateMaterialRequest): Request payload for updating an existing raw material's
            properties and specifications Example: {'name': 'Stainless Steel Sheet 304 - Updated',
            'uom': 'm²', 'category_name': 'Premium Raw Materials', 'default_supplier_id': 1502,
            'additional_info': 'Food-grade stainless steel, 1.5mm thickness - Updated specifications',
            'batch_tracked': True, 'is_sellable': False, 'is_archived': False, 'purchase_uom':
            'sheet', 'purchase_uom_conversion_rate': 2.0, 'configs': [{'id': 101, 'name': 'Grade',
            'values': ['304', '316', '430']}, {'name': 'Finish', 'values': ['Brushed', 'Mirror',
            'Matte']}], 'custom_field_collection_id': 201}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Material]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
