from http import HTTPStatus
from typing import Any, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.create_purchase_order_request import CreatePurchaseOrderRequest
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.outsourced_purchase_order import OutsourcedPurchaseOrder
from ...models.regular_purchase_order import RegularPurchaseOrder


def _get_kwargs(
    *,
    body: CreatePurchaseOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/purchase_orders",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
    | None
):
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_purchase_order_type_0 = (
                    RegularPurchaseOrder.from_dict(data)
                )

                return componentsschemas_purchase_order_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_purchase_order_type_1 = OutsourcedPurchaseOrder.from_dict(
                data
            )

            return componentsschemas_purchase_order_type_1

        response_200 = _parse_response_200(response.json())

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
) -> Response[
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
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
    body: CreatePurchaseOrderRequest,
) -> Response[
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
]:
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest): Request payload for creating a new purchase order to
            procure materials or products from suppliers Example: {'order_no': 'PO-2024-0156',
            'entity_type': 'regular', 'supplier_id': 4001, 'currency': 'USD', 'status':
            'NOT_RECEIVED', 'order_created_date': '2024-01-15T09:30:00Z', 'location_id': 1,
            'additional_info': "Rush order - needed for Valentine's Day production run",
            'purchase_order_rows': [{'quantity': 250, 'price_per_unit': 2.85, 'variant_id': 501,
            'tax_rate_id': 1, 'purchase_uom': 'kg', 'purchase_uom_conversion_rate': 1.0,
            'arrival_date': '2024-08-20T14:45:00Z'}, {'quantity': 100, 'price_per_unit': 12.5,
            'variant_id': 502, 'tax_rate_id': 1, 'purchase_uom': 'pieces',
            'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
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
    body: CreatePurchaseOrderRequest,
) -> (
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
    | None
):
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest): Request payload for creating a new purchase order to
            procure materials or products from suppliers Example: {'order_no': 'PO-2024-0156',
            'entity_type': 'regular', 'supplier_id': 4001, 'currency': 'USD', 'status':
            'NOT_RECEIVED', 'order_created_date': '2024-01-15T09:30:00Z', 'location_id': 1,
            'additional_info': "Rush order - needed for Valentine's Day production run",
            'purchase_order_rows': [{'quantity': 250, 'price_per_unit': 2.85, 'variant_id': 501,
            'tax_rate_id': 1, 'purchase_uom': 'kg', 'purchase_uom_conversion_rate': 1.0,
            'arrival_date': '2024-08-20T14:45:00Z'}, {'quantity': 100, 'price_per_unit': 12.5,
            'variant_id': 502, 'tax_rate_id': 1, 'purchase_uom': 'pieces',
            'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRequest,
) -> Response[
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
]:
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest): Request payload for creating a new purchase order to
            procure materials or products from suppliers Example: {'order_no': 'PO-2024-0156',
            'entity_type': 'regular', 'supplier_id': 4001, 'currency': 'USD', 'status':
            'NOT_RECEIVED', 'order_created_date': '2024-01-15T09:30:00Z', 'location_id': 1,
            'additional_info': "Rush order - needed for Valentine's Day production run",
            'purchase_order_rows': [{'quantity': 250, 'price_per_unit': 2.85, 'variant_id': 501,
            'tax_rate_id': 1, 'purchase_uom': 'kg', 'purchase_uom_conversion_rate': 1.0,
            'arrival_date': '2024-08-20T14:45:00Z'}, {'quantity': 100, 'price_per_unit': 12.5,
            'variant_id': 502, 'tax_rate_id': 1, 'purchase_uom': 'pieces',
            'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreatePurchaseOrderRequest,
) -> (
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
    | None
):
    """Create a purchase order

     Creates a new purchase order object.

    Args:
        body (CreatePurchaseOrderRequest): Request payload for creating a new purchase order to
            procure materials or products from suppliers Example: {'order_no': 'PO-2024-0156',
            'entity_type': 'regular', 'supplier_id': 4001, 'currency': 'USD', 'status':
            'NOT_RECEIVED', 'order_created_date': '2024-01-15T09:30:00Z', 'location_id': 1,
            'additional_info': "Rush order - needed for Valentine's Day production run",
            'purchase_order_rows': [{'quantity': 250, 'price_per_unit': 2.85, 'variant_id': 501,
            'tax_rate_id': 1, 'purchase_uom': 'kg', 'purchase_uom_conversion_rate': 1.0,
            'arrival_date': '2024-08-20T14:45:00Z'}, {'quantity': 100, 'price_per_unit': 12.5,
            'variant_id': 502, 'tax_rate_id': 1, 'purchase_uom': 'pieces',
            'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}]}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
