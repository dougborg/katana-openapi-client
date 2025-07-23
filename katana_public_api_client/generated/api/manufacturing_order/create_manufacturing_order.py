from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_request import CreateManufacturingOrderRequest
from ...models.create_manufacturing_order_response_401 import (
    CreateManufacturingOrderResponse401,
)
from ...models.create_manufacturing_order_response_429 import (
    CreateManufacturingOrderResponse429,
)
from ...models.create_manufacturing_order_response_500 import (
    CreateManufacturingOrderResponse500,
)
from ...models.manufacturing_order import ManufacturingOrder
from ...types import Response


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
) -> (
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrder.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateManufacturingOrderResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = CreateManufacturingOrderResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateManufacturingOrderResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
]:
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
) -> Response[
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
]:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderResponse401, CreateManufacturingOrderResponse429, CreateManufacturingOrderResponse500, ManufacturingOrder]]
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
) -> (
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderResponse401, CreateManufacturingOrderResponse429, CreateManufacturingOrderResponse500, ManufacturingOrder]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderRequest,
) -> Response[
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
]:
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderResponse401, CreateManufacturingOrderResponse429, CreateManufacturingOrderResponse500, ManufacturingOrder]]
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
) -> (
    CreateManufacturingOrderResponse401
    | CreateManufacturingOrderResponse429
    | CreateManufacturingOrderResponse500
    | ManufacturingOrder
    | None
):
    """Create a manufacturing order

     Creates a new manufacturing order object. Manufacturing order recipe and
      operation rows are created automatically based on the product recipe and operations.

    Args:
        body (CreateManufacturingOrderRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderResponse401, CreateManufacturingOrderResponse429, CreateManufacturingOrderResponse500, ManufacturingOrder]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
