from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_manufacturing_order_request import CreateManufacturingOrderRequest
from ...models.error_response import ErrorResponse
from ...models.manufacturing_order import ManufacturingOrder


def _get_kwargs(
    *,
    body: CreateManufacturingOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_orders",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrder | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrder.from_dict(response.json())

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
) -> Response[ErrorResponse | ManufacturingOrder]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRequest,
) -> Response[ErrorResponse | ManufacturingOrder]:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest): Request payload for creating a new manufacturing
            order to initiate production of products or components. Example: {'variant_id': 2101,
            'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for
            new product launch'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, ManufacturingOrder]]
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
    body: CreateManufacturingOrderRequest,
) -> ErrorResponse | ManufacturingOrder | None:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest): Request payload for creating a new manufacturing
            order to initiate production of products or components. Example: {'variant_id': 2101,
            'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for
            new product launch'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, ManufacturingOrder]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRequest,
) -> Response[ErrorResponse | ManufacturingOrder]:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest): Request payload for creating a new manufacturing
            order to initiate production of products or components. Example: {'variant_id': 2101,
            'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for
            new product launch'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, ManufacturingOrder]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRequest,
) -> ErrorResponse | ManufacturingOrder | None:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest): Request payload for creating a new manufacturing
            order to initiate production of products or components. Example: {'variant_id': 2101,
            'planned_quantity': 50, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for
            new product launch'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, ManufacturingOrder]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
