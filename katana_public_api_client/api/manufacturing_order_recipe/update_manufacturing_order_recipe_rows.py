from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.manufacturing_order_recipe_row import ManufacturingOrderRecipeRow
from ...models.update_manufacturing_order_recipe_row_request import (
    UpdateManufacturingOrderRecipeRowRequest,
)


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_recipe_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrderRecipeRow | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrderRecipeRow.from_dict(response.json())

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
) -> Response[ErrorResponse | ManufacturingOrderRecipeRow]:
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
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> Response[ErrorResponse | ManufacturingOrderRecipeRow]:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest): Request payload for updating a
            manufacturing order recipe row with actual consumption data and revised requirements
            Example: {'notes': 'Used organic ingredients as requested by customer',
            'planned_quantity_per_unit': 0.3, 'total_actual_quantity': 6.2, 'ingredient_availability':
            'AVAILABLE', 'ingredient_expected_date': '2023-10-15T08:00:00Z', 'batch_transactions':
            [{'batch_id': 301, 'quantity': 3.5}, {'batch_id': 302, 'quantity': 2.7}], 'cost': 15.25}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderRecipeRow]]
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
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> ErrorResponse | ManufacturingOrderRecipeRow | None:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest): Request payload for updating a
            manufacturing order recipe row with actual consumption data and revised requirements
            Example: {'notes': 'Used organic ingredients as requested by customer',
            'planned_quantity_per_unit': 0.3, 'total_actual_quantity': 6.2, 'ingredient_availability':
            'AVAILABLE', 'ingredient_expected_date': '2023-10-15T08:00:00Z', 'batch_transactions':
            [{'batch_id': 301, 'quantity': 3.5}, {'batch_id': 302, 'quantity': 2.7}], 'cost': 15.25}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderRecipeRow]
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
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> Response[ErrorResponse | ManufacturingOrderRecipeRow]:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest): Request payload for updating a
            manufacturing order recipe row with actual consumption data and revised requirements
            Example: {'notes': 'Used organic ingredients as requested by customer',
            'planned_quantity_per_unit': 0.3, 'total_actual_quantity': 6.2, 'ingredient_availability':
            'AVAILABLE', 'ingredient_expected_date': '2023-10-15T08:00:00Z', 'batch_transactions':
            [{'batch_id': 301, 'quantity': 3.5}, {'batch_id': 302, 'quantity': 2.7}], 'cost': 15.25}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderRecipeRow]]
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
    body: UpdateManufacturingOrderRecipeRowRequest,
) -> ErrorResponse | ManufacturingOrderRecipeRow | None:
    """Update a manufacturing order recipe row

     Updates the specified manufacturing order recipe row by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged. Recipe rows cannot be updated when
      the manufacturing order status is DONE.

    Args:
        id (int):
        body (UpdateManufacturingOrderRecipeRowRequest): Request payload for updating a
            manufacturing order recipe row with actual consumption data and revised requirements
            Example: {'notes': 'Used organic ingredients as requested by customer',
            'planned_quantity_per_unit': 0.3, 'total_actual_quantity': 6.2, 'ingredient_availability':
            'AVAILABLE', 'ingredient_expected_date': '2023-10-15T08:00:00Z', 'batch_transactions':
            [{'batch_id': 301, 'quantity': 3.5}, {'batch_id': 302, 'quantity': 2.7}], 'cost': 15.25}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderRecipeRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
