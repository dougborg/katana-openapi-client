from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_order_fulfillments_response_401 import (
    GetAllSalesOrderFulfillmentsResponse401,
)
from ...models.get_all_sales_order_fulfillments_response_429 import (
    GetAllSalesOrderFulfillmentsResponse429,
)
from ...models.get_all_sales_order_fulfillments_response_500 import (
    GetAllSalesOrderFulfillmentsResponse500,
)
from ...models.sales_order_fulfillment_list_response import (
    SalesOrderFulfillmentListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_order_id"] = sales_order_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_fulfillments",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SalesOrderFulfillmentListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesOrderFulfillmentsResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesOrderFulfillmentsResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesOrderFulfillmentsResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
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
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
) -> Response[
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesOrderFulfillmentsResponse401, GetAllSalesOrderFulfillmentsResponse429, GetAllSalesOrderFulfillmentsResponse500, SalesOrderFulfillmentListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
) -> (
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
    | None
):
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesOrderFulfillmentsResponse401, GetAllSalesOrderFulfillmentsResponse429, GetAllSalesOrderFulfillmentsResponse500, SalesOrderFulfillmentListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
) -> Response[
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesOrderFulfillmentsResponse401, GetAllSalesOrderFulfillmentsResponse429, GetAllSalesOrderFulfillmentsResponse500, SalesOrderFulfillmentListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
) -> (
    GetAllSalesOrderFulfillmentsResponse401
    | GetAllSalesOrderFulfillmentsResponse429
    | GetAllSalesOrderFulfillmentsResponse500
    | SalesOrderFulfillmentListResponse
    | None
):
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesOrderFulfillmentsResponse401, GetAllSalesOrderFulfillmentsResponse429, GetAllSalesOrderFulfillmentsResponse500, SalesOrderFulfillmentListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            sales_order_id=sales_order_id,
        )
    ).parsed
