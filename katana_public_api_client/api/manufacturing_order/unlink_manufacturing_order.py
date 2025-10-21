from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import Response
from ...models.error_response import ErrorResponse
from ...models.unlink_manufacturing_order_request import UnlinkManufacturingOrderRequest


def _get_kwargs(
    *,
    body: UnlinkManufacturingOrderRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/manufacturing_order_unlink",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ErrorResponse | None:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ErrorResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UnlinkManufacturingOrderRequest,
) -> Response[Any | ErrorResponse]:
    """Unlink a manufacturing order from sales order row

     Unlinks the manufacturing order from a particular sales order row.

    Args:
        body (UnlinkManufacturingOrderRequest): Request to unlink a manufacturing order from its
            associated sales order row, removing the direct connection while preserving both orders.
            Example: {'sales_order_row_id': 2501}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ErrorResponse]]
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
    body: UnlinkManufacturingOrderRequest,
) -> Any | ErrorResponse | None:
    """Unlink a manufacturing order from sales order row

     Unlinks the manufacturing order from a particular sales order row.

    Args:
        body (UnlinkManufacturingOrderRequest): Request to unlink a manufacturing order from its
            associated sales order row, removing the direct connection while preserving both orders.
            Example: {'sales_order_row_id': 2501}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ErrorResponse]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UnlinkManufacturingOrderRequest,
) -> Response[Any | ErrorResponse]:
    """Unlink a manufacturing order from sales order row

     Unlinks the manufacturing order from a particular sales order row.

    Args:
        body (UnlinkManufacturingOrderRequest): Request to unlink a manufacturing order from its
            associated sales order row, removing the direct connection while preserving both orders.
            Example: {'sales_order_row_id': 2501}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, ErrorResponse]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: UnlinkManufacturingOrderRequest,
) -> Any | ErrorResponse | None:
    """Unlink a manufacturing order from sales order row

     Unlinks the manufacturing order from a particular sales order row.

    Args:
        body (UnlinkManufacturingOrderRequest): Request to unlink a manufacturing order from its
            associated sales order row, removing the direct connection while preserving both orders.
            Example: {'sales_order_row_id': 2501}.


    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, ErrorResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
