from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_production_request import (
    CreateManufacturingOrderProductionRequest,
)
from ...models.error_response import ErrorResponse
from ...models.manufacturing_order_production import ManufacturingOrderProduction
from ...types import Response


def _get_kwargs(
    *,
    body: CreateManufacturingOrderProductionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_productions",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrderProduction | None:
    if response.status_code == 200:
        response_200 = ManufacturingOrderProduction.from_dict(response.json())

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
) -> Response[ErrorResponse | ManufacturingOrderProduction]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderProductionRequest,
) -> Response[ErrorResponse | ManufacturingOrderProduction]:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest): Request object for creating a new
            manufacturing order production Example: {'manufacturing_order_id': 21400, 'quantity': 5,
            'production_date': '2021-09-01T07:49:29.000Z', 'ingredients': [], 'operations': []}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderProduction]]
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
    body: CreateManufacturingOrderProductionRequest,
) -> ErrorResponse | ManufacturingOrderProduction | None:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest): Request object for creating a new
            manufacturing order production Example: {'manufacturing_order_id': 21400, 'quantity': 5,
            'production_date': '2021-09-01T07:49:29.000Z', 'ingredients': [], 'operations': []}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderProduction]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderProductionRequest,
) -> Response[ErrorResponse | ManufacturingOrderProduction]:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest): Request object for creating a new
            manufacturing order production Example: {'manufacturing_order_id': 21400, 'quantity': 5,
            'production_date': '2021-09-01T07:49:29.000Z', 'ingredients': [], 'operations': []}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderProduction]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderProductionRequest,
) -> ErrorResponse | ManufacturingOrderProduction | None:
    """Create a manufacturing order production

     Creates a new manufacturing order production object.

    Args:
        body (CreateManufacturingOrderProductionRequest): Request object for creating a new
            manufacturing order production Example: {'manufacturing_order_id': 21400, 'quantity': 5,
            'production_date': '2021-09-01T07:49:29.000Z', 'ingredients': [], 'operations': []}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderProduction]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
