from http import HTTPStatus
from typing import Any, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.detailed_error_response import DetailedErrorResponse
from ...models.error_response import ErrorResponse
from ...models.outsourced_purchase_order import OutsourcedPurchaseOrder
from ...models.regular_purchase_order import RegularPurchaseOrder
from ...models.update_purchase_order_request import UpdatePurchaseOrderRequest


def _get_kwargs(
    id: int,
    *,
    body: UpdatePurchaseOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/purchase_orders/{id}",
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
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdatePurchaseOrderRequest,
) -> Response[
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
]:
    """Update a purchase order

     Updates the specified purchase order by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRequest): Request payload for updating an existing purchase
            order's details, status, and line items Example: {'order_no': 'PO-2024-0156-REVISED',
            'expected_arrival_date': '2024-02-20', 'status': 'PARTIALLY_RECEIVED', 'additional_info':
            'Delivery delayed due to weather - updated schedule'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
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
    body: UpdatePurchaseOrderRequest,
) -> (
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
    | None
):
    """Update a purchase order

     Updates the specified purchase order by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRequest): Request payload for updating an existing purchase
            order's details, status, and line items Example: {'order_no': 'PO-2024-0156-REVISED',
            'expected_arrival_date': '2024-02-20', 'status': 'PARTIALLY_RECEIVED', 'additional_info':
            'Delivery delayed due to weather - updated schedule'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
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
    body: UpdatePurchaseOrderRequest,
) -> Response[
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
]:
    """Update a purchase order

     Updates the specified purchase order by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRequest): Request payload for updating an existing purchase
            order's details, status, and line items Example: {'order_no': 'PO-2024-0156-REVISED',
            'expected_arrival_date': '2024-02-20', 'status': 'PARTIALLY_RECEIVED', 'additional_info':
            'Delivery delayed due to weather - updated schedule'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]]
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
    body: UpdatePurchaseOrderRequest,
) -> (
    DetailedErrorResponse
    | ErrorResponse
    | Union["OutsourcedPurchaseOrder", "RegularPurchaseOrder"]
    | None
):
    """Update a purchase order

     Updates the specified purchase order by setting the values of the parameters passed.
        Any parameters not provided will be left unchanged.

    Args:
        id (int):
        body (UpdatePurchaseOrderRequest): Request payload for updating an existing purchase
            order's details, status, and line items Example: {'order_no': 'PO-2024-0156-REVISED',
            'expected_arrival_date': '2024-02-20', 'status': 'PARTIALLY_RECEIVED', 'additional_info':
            'Delivery delayed due to weather - updated schedule'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[DetailedErrorResponse, ErrorResponse, Union['OutsourcedPurchaseOrder', 'RegularPurchaseOrder']]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
