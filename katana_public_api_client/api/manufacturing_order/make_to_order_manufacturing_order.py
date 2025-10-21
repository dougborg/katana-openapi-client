from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.make_to_order_manufacturing_order_request import (
    MakeToOrderManufacturingOrderRequest,
)
from ...models.manufacturing_order import ManufacturingOrder


def _get_kwargs(
    *,
    body: MakeToOrderManufacturingOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_make_to_order",
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
    body: MakeToOrderManufacturingOrderRequest,
) -> Response[ErrorResponse | ManufacturingOrder]:
    """Create a make-to-order manufacturing order

     Creates a new manufacturing order object that is linked to a specific sales order row.

    Args:
        body (MakeToOrderManufacturingOrderRequest): Request to create a manufacturing order
            directly from a sales order row, linking production to customer demand for make-to-order
            manufacturing. Example: {'sales_order_row_id': 2501, 'create_subassemblies': True}.

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
    body: MakeToOrderManufacturingOrderRequest,
) -> ErrorResponse | ManufacturingOrder | None:
    """Create a make-to-order manufacturing order

     Creates a new manufacturing order object that is linked to a specific sales order row.

    Args:
        body (MakeToOrderManufacturingOrderRequest): Request to create a manufacturing order
            directly from a sales order row, linking production to customer demand for make-to-order
            manufacturing. Example: {'sales_order_row_id': 2501, 'create_subassemblies': True}.

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
    body: MakeToOrderManufacturingOrderRequest,
) -> Response[ErrorResponse | ManufacturingOrder]:
    """Create a make-to-order manufacturing order

     Creates a new manufacturing order object that is linked to a specific sales order row.

    Args:
        body (MakeToOrderManufacturingOrderRequest): Request to create a manufacturing order
            directly from a sales order row, linking production to customer demand for make-to-order
            manufacturing. Example: {'sales_order_row_id': 2501, 'create_subassemblies': True}.

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
    body: MakeToOrderManufacturingOrderRequest,
) -> ErrorResponse | ManufacturingOrder | None:
    """Create a make-to-order manufacturing order

     Creates a new manufacturing order object that is linked to a specific sales order row.

    Args:
        body (MakeToOrderManufacturingOrderRequest): Request to create a manufacturing order
            directly from a sales order row, linking production to customer demand for make-to-order
            manufacturing. Example: {'sales_order_row_id': 2501, 'create_subassemblies': True}.

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
