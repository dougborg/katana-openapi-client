from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_sales_return_request import CreateSalesReturnRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_return import SalesReturn


def _get_kwargs(
    *,
    body: CreateSalesReturnRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_returns",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    if response.status_code == 200:
        response_200 = SalesReturn.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesReturnRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest): Request payload for creating a new sales return to
            process customer product returns and refunds Example: {'customer_id': 1001,
            'sales_order_id': 2001, 'order_no': 'SR-2023-001', 'return_location_id': 1, 'currency':
            'USD', 'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported
            damaged items during shipping', 'sales_return_rows': [{'variant_id': 2002, 'quantity': 2,
            'return_reason_id': 1, 'notes': 'Packaging was damaged', 'unit_price': 25.0,
            'total_price': 50.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesReturn]]
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
    body: CreateSalesReturnRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest): Request payload for creating a new sales return to
            process customer product returns and refunds Example: {'customer_id': 1001,
            'sales_order_id': 2001, 'order_no': 'SR-2023-001', 'return_location_id': 1, 'currency':
            'USD', 'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported
            damaged items during shipping', 'sales_return_rows': [{'variant_id': 2002, 'quantity': 2,
            'return_reason_id': 1, 'notes': 'Packaging was damaged', 'unit_price': 25.0,
            'total_price': 50.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesReturn]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesReturnRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesReturn]:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest): Request payload for creating a new sales return to
            process customer product returns and refunds Example: {'customer_id': 1001,
            'sales_order_id': 2001, 'order_no': 'SR-2023-001', 'return_location_id': 1, 'currency':
            'USD', 'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported
            damaged items during shipping', 'sales_return_rows': [{'variant_id': 2002, 'quantity': 2,
            'return_reason_id': 1, 'notes': 'Packaging was damaged', 'unit_price': 25.0,
            'total_price': 50.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesReturn]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesReturnRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesReturn | None:
    """Create a sales return

     Creates a new sales return object.

    Args:
        body (CreateSalesReturnRequest): Request payload for creating a new sales return to
            process customer product returns and refunds Example: {'customer_id': 1001,
            'sales_order_id': 2001, 'order_no': 'SR-2023-001', 'return_location_id': 1, 'currency':
            'USD', 'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported
            damaged items during shipping', 'sales_return_rows': [{'variant_id': 2002, 'quantity': 2,
            'return_reason_id': 1, 'notes': 'Packaging was damaged', 'unit_price': 25.0,
            'total_price': 50.0}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesReturn]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
