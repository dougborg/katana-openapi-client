from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sales_order_shipping_fees_response_401 import (
    GetSalesOrderShippingFeesResponse401,
)
from ...models.get_sales_order_shipping_fees_response_429 import (
    GetSalesOrderShippingFeesResponse429,
)
from ...models.get_sales_order_shipping_fees_response_500 import (
    GetSalesOrderShippingFeesResponse500,
)
from ...models.sales_order_shipping_fee_list_response import (
    SalesOrderShippingFeeListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["sales_order_id"] = sales_order_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_shipping_fee",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SalesOrderShippingFeeListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetSalesOrderShippingFeesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetSalesOrderShippingFeesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetSalesOrderShippingFeesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
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
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
) -> Response[
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
]:
    """List sales order shipping fees

     Retrieves shipping fees for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesOrderShippingFeesResponse401, GetSalesOrderShippingFeesResponse429, GetSalesOrderShippingFeesResponse500, SalesOrderShippingFeeListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
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
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
) -> (
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
    | None
):
    """List sales order shipping fees

     Retrieves shipping fees for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesOrderShippingFeesResponse401, GetSalesOrderShippingFeesResponse429, GetSalesOrderShippingFeesResponse500, SalesOrderShippingFeeListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        sales_order_id=sales_order_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
) -> Response[
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
]:
    """List sales order shipping fees

     Retrieves shipping fees for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetSalesOrderShippingFeesResponse401, GetSalesOrderShippingFeesResponse429, GetSalesOrderShippingFeesResponse500, SalesOrderShippingFeeListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        sales_order_id=sales_order_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
) -> (
    GetSalesOrderShippingFeesResponse401
    | GetSalesOrderShippingFeesResponse429
    | GetSalesOrderShippingFeesResponse500
    | SalesOrderShippingFeeListResponse
    | None
):
    """List sales order shipping fees

     Retrieves shipping fees for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetSalesOrderShippingFeesResponse401, GetSalesOrderShippingFeesResponse429, GetSalesOrderShippingFeesResponse500, SalesOrderShippingFeeListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            sales_order_id=sales_order_id,
        )
    ).parsed
