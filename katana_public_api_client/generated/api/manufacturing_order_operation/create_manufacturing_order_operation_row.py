from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_manufacturing_order_operation_row_request import CreateManufacturingOrderOperationRowRequest
from ...models.error_response import ErrorResponse
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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    if response.status_code == 200:
        response_200 = ManufacturingOrderOperationRow.from_dict(response.json())

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateManufacturingOrderOperationRowRequest,
) -> Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]
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
    client: Union[AuthenticatedClient, Client],
    body: CreateManufacturingOrderOperationRowRequest,
) -> Optional[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, ManufacturingOrderOperationRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateManufacturingOrderOperationRowRequest,
) -> Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: CreateManufacturingOrderOperationRowRequest,
) -> Optional[Union[ErrorResponse, ManufacturingOrderOperationRow]]:
    """Create a manufacturing order operation row

     Add an operation row to an existing manufacturing order. Operation rows cannot be added when the
      manufacturing order status is DONE.

    Args:
        body (CreateManufacturingOrderOperationRowRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, ManufacturingOrderOperationRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
