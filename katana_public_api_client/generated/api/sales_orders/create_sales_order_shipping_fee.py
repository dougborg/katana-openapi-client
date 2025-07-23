from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_sales_order_shipping_fee_request import (
    CreateSalesOrderShippingFeeRequest,
)
from ...models.create_sales_order_shipping_fee_response_400 import (
    CreateSalesOrderShippingFeeResponse400,
)
from ...models.create_sales_order_shipping_fee_response_401 import (
    CreateSalesOrderShippingFeeResponse401,
)
from ...models.create_sales_order_shipping_fee_response_422 import (
    CreateSalesOrderShippingFeeResponse422,
)
from ...models.create_sales_order_shipping_fee_response_429 import (
    CreateSalesOrderShippingFeeResponse429,
)
from ...models.create_sales_order_shipping_fee_response_500 import (
    CreateSalesOrderShippingFeeResponse500,
)
from ...models.sales_order_shipping_fee import SalesOrderShippingFee
from ...types import Response


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
) -> (
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
    | None
):
    if response.status_code == 201:
        response_201 = SalesOrderShippingFee.from_dict(response.json())

        return response_201
    if response.status_code == 400:
        response_400 = CreateSalesOrderShippingFeeResponse400.from_dict(response.json())

        return response_400
    if response.status_code == 401:
        response_401 = CreateSalesOrderShippingFeeResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateSalesOrderShippingFeeResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateSalesOrderShippingFeeResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateSalesOrderShippingFeeResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
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
    body: CreateSalesOrderShippingFeeRequest,
) -> Response[
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
]:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSalesOrderShippingFeeResponse400, CreateSalesOrderShippingFeeResponse401, CreateSalesOrderShippingFeeResponse422, CreateSalesOrderShippingFeeResponse429, CreateSalesOrderShippingFeeResponse500, SalesOrderShippingFee]]
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
) -> (
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
    | None
):
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSalesOrderShippingFeeResponse400, CreateSalesOrderShippingFeeResponse401, CreateSalesOrderShippingFeeResponse422, CreateSalesOrderShippingFeeResponse429, CreateSalesOrderShippingFeeResponse500, SalesOrderShippingFee]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSalesOrderShippingFeeRequest,
) -> Response[
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
]:
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSalesOrderShippingFeeResponse400, CreateSalesOrderShippingFeeResponse401, CreateSalesOrderShippingFeeResponse422, CreateSalesOrderShippingFeeResponse429, CreateSalesOrderShippingFeeResponse500, SalesOrderShippingFee]]
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
) -> (
    CreateSalesOrderShippingFeeResponse400
    | CreateSalesOrderShippingFeeResponse401
    | CreateSalesOrderShippingFeeResponse422
    | CreateSalesOrderShippingFeeResponse429
    | CreateSalesOrderShippingFeeResponse500
    | SalesOrderShippingFee
    | None
):
    """Create a sales order shipping fee

     Creates a sales order shipping fee and adds it to a sales order.

    Args:
        body (CreateSalesOrderShippingFeeRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSalesOrderShippingFeeResponse400, CreateSalesOrderShippingFeeResponse401, CreateSalesOrderShippingFeeResponse422, CreateSalesOrderShippingFeeResponse429, CreateSalesOrderShippingFeeResponse500, SalesOrderShippingFee]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
