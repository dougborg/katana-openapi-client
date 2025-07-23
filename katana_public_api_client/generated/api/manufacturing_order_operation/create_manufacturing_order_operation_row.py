from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_operation_row_request import (
    CreateManufacturingOrderOperationRowRequest,
)
from ...models.create_manufacturing_order_operation_row_response_401 import (
    CreateManufacturingOrderOperationRowResponse401,
)
from ...models.create_manufacturing_order_operation_row_response_429 import (
    CreateManufacturingOrderOperationRowResponse429,
)
from ...models.create_manufacturing_order_operation_row_response_500 import (
    CreateManufacturingOrderOperationRowResponse500,
)
from ...models.manufacturing_order_operation_row import ManufacturingOrderOperationRow
from ...types import Response


def _get_kwargs(
    *,
    body: CreateManufacturingOrderOperationRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_operation_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderOperationRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateManufacturingOrderOperationRowResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = CreateManufacturingOrderOperationRowResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = CreateManufacturingOrderOperationRowResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
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
    body: CreateManufacturingOrderOperationRowRequest,
) -> Response[
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderOperationRowResponse401, CreateManufacturingOrderOperationRowResponse429, CreateManufacturingOrderOperationRowResponse500, ManufacturingOrderOperationRow]]
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
    body: CreateManufacturingOrderOperationRowRequest,
) -> (
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
    | None
):
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderOperationRowResponse401, CreateManufacturingOrderOperationRowResponse429, CreateManufacturingOrderOperationRowResponse500, ManufacturingOrderOperationRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderOperationRowRequest,
) -> Response[
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateManufacturingOrderOperationRowResponse401, CreateManufacturingOrderOperationRowResponse429, CreateManufacturingOrderOperationRowResponse500, ManufacturingOrderOperationRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateManufacturingOrderOperationRowRequest,
) -> (
    CreateManufacturingOrderOperationRowResponse401
    | CreateManufacturingOrderOperationRowResponse429
    | CreateManufacturingOrderOperationRowResponse500
    | ManufacturingOrderOperationRow
    | None
):
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateManufacturingOrderOperationRowResponse401, CreateManufacturingOrderOperationRowResponse429, CreateManufacturingOrderOperationRowResponse500, ManufacturingOrderOperationRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
