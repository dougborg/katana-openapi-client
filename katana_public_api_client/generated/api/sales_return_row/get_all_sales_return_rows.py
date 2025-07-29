from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_return_rows_response_401 import (
    GetAllSalesReturnRowsResponse401,
)
from ...models.get_all_sales_return_rows_response_429 import (
    GetAllSalesReturnRowsResponse429,
)
from ...models.get_all_sales_return_rows_response_500 import (
    GetAllSalesReturnRowsResponse500,
)
from ...models.sales_return_row_list_response import SalesReturnRowListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_return_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_return_id"] = sales_return_id

    params["variant_id"] = variant_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_return_rows",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
    ]
]:
    if response.status_code == 200:
        response_200 = SalesReturnRowListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesReturnRowsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesReturnRowsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesReturnRowsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
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
    sales_return_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
    ]
]:
    """List all sales return rows

     Returns a list of sales return rows you've previously created. The sales return rows are returned in
    sorted order, with the most recent sales return row appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_return_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSalesReturnRowsResponse401, GetAllSalesReturnRowsResponse429, GetAllSalesReturnRowsResponse500, SalesReturnRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_return_id=sales_return_id,
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
    sales_return_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
    ]
]:
    """List all sales return rows

     Returns a list of sales return rows you've previously created. The sales return rows are returned in
    sorted order, with the most recent sales return row appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_return_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSalesReturnRowsResponse401, GetAllSalesReturnRowsResponse429, GetAllSalesReturnRowsResponse500, SalesReturnRowListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        sales_return_id=sales_return_id,
        variant_id=variant_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_return_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
    ]
]:
    """List all sales return rows

     Returns a list of sales return rows you've previously created. The sales return rows are returned in
    sorted order, with the most recent sales return row appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_return_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetAllSalesReturnRowsResponse401, GetAllSalesReturnRowsResponse429, GetAllSalesReturnRowsResponse500, SalesReturnRowListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_return_id=sales_return_id,
        variant_id=variant_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_return_id: Union[Unset, int] = UNSET,
    variant_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetAllSalesReturnRowsResponse401,
        GetAllSalesReturnRowsResponse429,
        GetAllSalesReturnRowsResponse500,
        SalesReturnRowListResponse,
    ]
]:
    """List all sales return rows

     Returns a list of sales return rows you've previously created. The sales return rows are returned in
    sorted order, with the most recent sales return row appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_return_id (Union[Unset, int]):
        variant_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetAllSalesReturnRowsResponse401, GetAllSalesReturnRowsResponse429, GetAllSalesReturnRowsResponse500, SalesReturnRowListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            sales_return_id=sales_return_id,
            variant_id=variant_id,
        )
    ).parsed
