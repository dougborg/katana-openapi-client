from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_purchase_order_row_request import CreatePurchaseOrderRowRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.purchase_order_row import PurchaseOrderRow


def _get_kwargs(
    *,
    body: CreatePurchaseOrderRowRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/purchase_order_rows",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DetailedErrorResponse | ErrorResponse | PurchaseOrderRow | None:
    if response.status_code == 200:
        response_200 = PurchaseOrderRow.from_dict(response.json())

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
) -> Response[DetailedErrorResponse | ErrorResponse | PurchaseOrderRow]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | PurchaseOrderRow]:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest): Request payload for adding a new line item to an
            existing purchase order Example: {'purchase_order_id': 156, 'quantity': 50, 'variant_id':
            503, 'tax_rate_id': 1, 'group_id': 1, 'price_per_unit': 8.75,
            'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces', 'arrival_date':
            '2024-02-15T10:00:00Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, PurchaseOrderRow]]
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
    body: CreatePurchaseOrderRowRequest,
) -> DetailedErrorResponse | ErrorResponse | PurchaseOrderRow | None:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest): Request payload for adding a new line item to an
            existing purchase order Example: {'purchase_order_id': 156, 'quantity': 50, 'variant_id':
            503, 'tax_rate_id': 1, 'group_id': 1, 'price_per_unit': 8.75,
            'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces', 'arrival_date':
            '2024-02-15T10:00:00Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, PurchaseOrderRow]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRowRequest,
) -> Response[DetailedErrorResponse | ErrorResponse | PurchaseOrderRow]:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest): Request payload for adding a new line item to an
            existing purchase order Example: {'purchase_order_id': 156, 'quantity': 50, 'variant_id':
            503, 'tax_rate_id': 1, 'group_id': 1, 'price_per_unit': 8.75,
            'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces', 'arrival_date':
            '2024-02-15T10:00:00Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, PurchaseOrderRow]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRowRequest,
) -> DetailedErrorResponse | ErrorResponse | PurchaseOrderRow | None:
    """Create a purchase order row

     Creates a new purchase order row object.

    Args:
        body (CreatePurchaseOrderRowRequest): Request payload for adding a new line item to an
            existing purchase order Example: {'purchase_order_id': 156, 'quantity': 50, 'variant_id':
            503, 'tax_rate_id': 1, 'group_id': 1, 'price_per_unit': 8.75,
            'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces', 'arrival_date':
            '2024-02-15T10:00:00Z'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, PurchaseOrderRow]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
