from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.manufacturing_order_production import ManufacturingOrderProduction
from ...models.update_manufacturing_order_production_request import (
    UpdateManufacturingOrderProductionRequest,
)


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderProductionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_productions/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrderProduction.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

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
) -> Response[DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction]:
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
    body: UpdateManufacturingOrderProductionRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction]:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest): Request payload for updating an existing
            production run within a manufacturing order, modifying production quantities and material
            usage. Example: {'quantity': 30, 'production_date': '2024-01-21T16:00:00Z', 'ingredients':
            [{'id': 4002, 'location_id': 1, 'variant_id': 3102, 'manufacturing_order_id': 3001,
            'manufacturing_order_recipe_row_id': 3202, 'production_id': 3502, 'quantity': 60.0,
            'production_date': '2024-01-21T16:00:00Z', 'cost': 150.0}], 'operations': [{'id': 3802,
            'manufacturing_order_id': 3001, 'operation_id': 402, 'time': 18.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, ManufacturingOrderProduction]]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction | None:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest): Request payload for updating an existing
            production run within a manufacturing order, modifying production quantities and material
            usage. Example: {'quantity': 30, 'production_date': '2024-01-21T16:00:00Z', 'ingredients':
            [{'id': 4002, 'location_id': 1, 'variant_id': 3102, 'manufacturing_order_id': 3001,
            'manufacturing_order_recipe_row_id': 3202, 'production_id': 3502, 'quantity': 60.0,
            'production_date': '2024-01-21T16:00:00Z', 'cost': 150.0}], 'operations': [{'id': 3802,
            'manufacturing_order_id': 3001, 'operation_id': 402, 'time': 18.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, ManufacturingOrderProduction]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction]:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest): Request payload for updating an existing
            production run within a manufacturing order, modifying production quantities and material
            usage. Example: {'quantity': 30, 'production_date': '2024-01-21T16:00:00Z', 'ingredients':
            [{'id': 4002, 'location_id': 1, 'variant_id': 3102, 'manufacturing_order_id': 3001,
            'manufacturing_order_recipe_row_id': 3202, 'production_id': 3502, 'quantity': 60.0,
            'production_date': '2024-01-21T16:00:00Z', 'cost': 150.0}], 'operations': [{'id': 3802,
            'manufacturing_order_id': 3001, 'operation_id': 402, 'time': 18.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, ManufacturingOrderProduction]]
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
    body: UpdateManufacturingOrderProductionRequest,
) -> DetailedErrorResponse | ErrorResponse | ManufacturingOrderProduction | None:
    """Update a manufacturing order production

     Updates the specified manufacturing order production by setting the values of the parameters passed.
      Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdateManufacturingOrderProductionRequest): Request payload for updating an existing
            production run within a manufacturing order, modifying production quantities and material
            usage. Example: {'quantity': 30, 'production_date': '2024-01-21T16:00:00Z', 'ingredients':
            [{'id': 4002, 'location_id': 1, 'variant_id': 3102, 'manufacturing_order_id': 3001,
            'manufacturing_order_recipe_row_id': 3202, 'production_id': 3502, 'quantity': 60.0,
            'production_date': '2024-01-21T16:00:00Z', 'cost': 150.0}], 'operations': [{'id': 3802,
            'manufacturing_order_id': 3001, 'operation_id': 402, 'time': 18.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, ManufacturingOrderProduction]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
