from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_order_rows_response_401 import (
    GetAllSalesOrderRowsResponse401,
)
from ...models.get_all_sales_order_rows_response_429 import (
    GetAllSalesOrderRowsResponse429,
)
from ...models.get_all_sales_order_rows_response_500 import (
    GetAllSalesOrderRowsResponse500,
)
from ...models.sales_order_row_list_response import SalesOrderRowListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_order_id"] = sales_order_id

    params["variant_id"] = variant_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    if response.status_code == 200:
        response_200 = SalesOrderRowListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesOrderRowsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesOrderRowsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesOrderRowsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSalesOrderRowsResponse401, GetAllSalesOrderRowsResponse429, GetAllSalesOrderRowsResponse500, SalesOrderRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        variant_id=variant_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSalesOrderRowsResponse401, GetAllSalesOrderRowsResponse429, GetAllSalesOrderRowsResponse500, SalesOrderRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        variant_id=variant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSalesOrderRowsResponse401, GetAllSalesOrderRowsResponse429, GetAllSalesOrderRowsResponse500, SalesOrderRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        variant_id=variant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetAllSalesOrderRowsResponse401,
        GetAllSalesOrderRowsResponse429,
        GetAllSalesOrderRowsResponse500,
        SalesOrderRowListResponse,
    ]
]:
    """List sales order rows

     Returns a list of sales order rows.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSalesOrderRowsResponse401, GetAllSalesOrderRowsResponse429, GetAllSalesOrderRowsResponse500, SalesOrderRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            sales_order_id=sales_order_id,
            variant_id=variant_id,
        )
    ).parsed
