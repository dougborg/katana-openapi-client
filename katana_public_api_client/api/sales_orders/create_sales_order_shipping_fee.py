from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_sales_order_shipping_fee_request import (
    CreateSalesOrderShippingFeeRequest,
)
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.sales_order_shipping_fee import SalesOrderShippingFee


def _get_kwargs(
    *,
    body: CreateSalesOrderShippingFeeRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/sales_order_shipping_fee",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee | None:
    if response.status_code == 200:
        response_200 = SalesOrderShippingFee.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderShippingFeeRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee]:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest): Request payload for adding a shipping fee to an
            existing sales order Example: {'sales_order_id': 2001, 'amount': 25.99, 'description':
            'Express Shipping - Next Day Delivery', 'tax_rate_id': 301}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderShippingFee]]
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
    body: CreateSalesOrderShippingFeeRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee | None:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest): Request payload for adding a shipping fee to an
            existing sales order Example: {'sales_order_id': 2001, 'amount': 25.99, 'description':
            'Express Shipping - Next Day Delivery', 'tax_rate_id': 301}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderShippingFee]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderShippingFeeRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee]:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest): Request payload for adding a shipping fee to an
            existing sales order Example: {'sales_order_id': 2001, 'amount': 25.99, 'description':
            'Express Shipping - Next Day Delivery', 'tax_rate_id': 301}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, SalesOrderShippingFee]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderShippingFeeRequest,
) -> DetailedErrorResponse | ErrorResponse | SalesOrderShippingFee | None:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest): Request payload for adding a shipping fee to an
            existing sales order Example: {'sales_order_id': 2001, 'amount': 25.99, 'description':
            'Express Shipping - Next Day Delivery', 'tax_rate_id': 301}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, SalesOrderShippingFee]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
