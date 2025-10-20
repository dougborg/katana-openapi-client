from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.batch import Batch
from ...models.batch_response import BatchResponse
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse


def _get_kwargs(
    *,
    body: Batch,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/batches",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> BatchResponse | DetailedErrorResponse | ErrorResponse | None:
    if response.status_code == 200:
        response_200 = BatchResponse.from_dict(response.json())

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
) -> Response[BatchResponse | DetailedErrorResponse | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: Batch,
) -> Response[BatchResponse | DetailedErrorResponse | ErrorResponse]:
    """Create a batch

     Creates a batch object.

    Args:
        body (Batch): Core batch business properties Example: {'batch_number': 'BAT-2024-001',
            'expiration_date': '2025-10-23T10:37:05.085Z', 'batch_created_date':
            '2024-01-15T08:00:00.000Z', 'variant_id': 1001, 'batch_barcode': '0317'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchResponse, DetailedErrorResponse, ErrorResponse]]
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
    body: Batch,
) -> BatchResponse | DetailedErrorResponse | ErrorResponse | None:
    """Create a batch

     Creates a batch object.

    Args:
        body (Batch): Core batch business properties Example: {'batch_number': 'BAT-2024-001',
            'expiration_date': '2025-10-23T10:37:05.085Z', 'batch_created_date':
            '2024-01-15T08:00:00.000Z', 'variant_id': 1001, 'batch_barcode': '0317'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchResponse, DetailedErrorResponse, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: Batch,
) -> Response[BatchResponse | DetailedErrorResponse | ErrorResponse]:
    """Create a batch

     Creates a batch object.

    Args:
        body (Batch): Core batch business properties Example: {'batch_number': 'BAT-2024-001',
            'expiration_date': '2025-10-23T10:37:05.085Z', 'batch_created_date':
            '2024-01-15T08:00:00.000Z', 'variant_id': 1001, 'batch_barcode': '0317'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[BatchResponse, DetailedErrorResponse, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: Batch,
) -> BatchResponse | DetailedErrorResponse | ErrorResponse | None:
    """Create a batch

     Creates a batch object.

    Args:
        body (Batch): Core batch business properties Example: {'batch_number': 'BAT-2024-001',
            'expiration_date': '2025-10-23T10:37:05.085Z', 'batch_created_date':
            '2024-01-15T08:00:00.000Z', 'variant_id': 1001, 'batch_barcode': '0317'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[BatchResponse, DetailedErrorResponse, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
