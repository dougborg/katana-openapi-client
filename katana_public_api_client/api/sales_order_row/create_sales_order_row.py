from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_sales_order_row_request import CreateSalesOrderRowRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_order_row import SalesOrderRow


def _get_kwargs(
    *,
    body: CreateSalesOrderRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_order_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRow | None:
    if response.status_code == 200:
        response_200 = SalesOrderRow.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRow]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRow]:
    """Create a sales order row

     Creates a new sales order row (line item).

    Args:
        body (CreateSalesOrderRowRequest): Request payload for creating a new sales order row
            (line item) Example: {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2,
            'price_per_unit': 599.99, 'tax_rate_id': 301, 'location_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderRow]]
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
    body: CreateSalesOrderRowRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRow | None:
    """Create a sales order row

     Creates a new sales order row (line item).

    Args:
        body (CreateSalesOrderRowRequest): Request payload for creating a new sales order row
            (line item) Example: {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2,
            'price_per_unit': 599.99, 'tax_rate_id': 301, 'location_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderRow]:
    """Create a sales order row

     Creates a new sales order row (line item).

    Args:
        body (CreateSalesOrderRowRequest): Request payload for creating a new sales order row
            (line item) Example: {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2,
            'price_per_unit': 599.99, 'tax_rate_id': 301, 'location_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderRowRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderRow | None:
    """Create a sales order row

     Creates a new sales order row (line item).

    Args:
        body (CreateSalesOrderRowRequest): Request payload for creating a new sales order row
            (line item) Example: {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2,
            'price_per_unit': 599.99, 'tax_rate_id': 301, 'location_id': 1}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
