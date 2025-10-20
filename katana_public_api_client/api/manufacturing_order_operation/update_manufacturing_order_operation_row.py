from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.manufacturing_order_operation_row import ManufacturingOrderOperationRow
from ...models.update_manufacturing_order_operation_row_request import (
    UpdateManufacturingOrderOperationRowRequest,
)


def _get_kwargs(
    id: int,
    *,
    body: UpdateManufacturingOrderOperationRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/manufacturing_order_operation_rows/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | ManufacturingOrderOperationRow | None:
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
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | ManufacturingOrderOperationRow]:
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
    body: UpdateManufacturingOrderOperationRowRequest,
) -> Response[ErrorResponse | ManufacturingOrderOperationRow]:
    """Update a manufacturing order operation row

     Updates the specified manufacturing order operation row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged. Only completed_by_operators and
    total_actual_time can be
        updated when the manufacturing order status is DONE

    Args:
        id (int):
        body (UpdateManufacturingOrderOperationRowRequest): Request payload for updating a
            manufacturing order operation row with actual completion data Example:
            {'completed_by_operators': [{'id': 101, 'name': 'John Smith'}], 'total_actual_time':
            52.3}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]
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
    body: UpdateManufacturingOrderOperationRowRequest,
) -> ErrorResponse | ManufacturingOrderOperationRow | None:
    """Update a manufacturing order operation row

     Updates the specified manufacturing order operation row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged. Only completed_by_operators and
    total_actual_time can be
        updated when the manufacturing order status is DONE

    Args:
        id (int):
        body (UpdateManufacturingOrderOperationRowRequest): Request payload for updating a
            manufacturing order operation row with actual completion data Example:
            {'completed_by_operators': [{'id': 101, 'name': 'John Smith'}], 'total_actual_time':
            52.3}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderOperationRow]
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
    body: UpdateManufacturingOrderOperationRowRequest,
) -> Response[ErrorResponse | ManufacturingOrderOperationRow]:
    """Update a manufacturing order operation row

     Updates the specified manufacturing order operation row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged. Only completed_by_operators and
    total_actual_time can be
        updated when the manufacturing order status is DONE

    Args:
        id (int):
        body (UpdateManufacturingOrderOperationRowRequest): Request payload for updating a
            manufacturing order operation row with actual completion data Example:
            {'completed_by_operators': [{'id': 101, 'name': 'John Smith'}], 'total_actual_time':
            52.3}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, ManufacturingOrderOperationRow]]
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
    body: UpdateManufacturingOrderOperationRowRequest,
) -> ErrorResponse | ManufacturingOrderOperationRow | None:
    """Update a manufacturing order operation row

     Updates the specified manufacturing order operation row by setting the values of the parameters
    passed.
        Any parameters not provided will be left unchanged. Only completed_by_operators and
    total_actual_time can be
        updated when the manufacturing order status is DONE

    Args:
        id (int):
        body (UpdateManufacturingOrderOperationRowRequest): Request payload for updating a
            manufacturing order operation row with actual completion data Example:
            {'completed_by_operators': [{'id': 101, 'name': 'John Smith'}], 'total_actual_time':
            52.3}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, ManufacturingOrderOperationRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
