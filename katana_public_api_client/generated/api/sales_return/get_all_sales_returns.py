from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_returns_response_401 import GetAllSalesReturnsResponse401
from ...models.get_all_sales_returns_response_429 import GetAllSalesReturnsResponse429
from ...models.get_all_sales_returns_response_500 import GetAllSalesReturnsResponse500
from ...models.get_all_sales_returns_status import GetAllSalesReturnsStatus
from ...models.sales_return_list_response import SalesReturnListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    customer_id: Unset | int = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | GetAllSalesReturnsStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["customer_id"] = customer_id

    params["sales_order_id"] = sales_order_id

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_returns",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SalesReturnListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesReturnsResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesReturnsResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesReturnsResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
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
    customer_id: Unset | int = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | GetAllSalesReturnsStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        customer_id (Union[Unset, int]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesReturnsStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesReturnsResponse401, GetAllSalesReturnsResponse429, GetAllSalesReturnsResponse500, SalesReturnListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
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
    customer_id: Unset | int = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | GetAllSalesReturnsStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
    | None
):
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        customer_id (Union[Unset, int]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesReturnsStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesReturnsResponse401, GetAllSalesReturnsResponse429, GetAllSalesReturnsResponse500, SalesReturnListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    customer_id: Unset | int = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | GetAllSalesReturnsStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        customer_id (Union[Unset, int]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesReturnsStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesReturnsResponse401, GetAllSalesReturnsResponse429, GetAllSalesReturnsResponse500, SalesReturnListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        customer_id=customer_id,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    customer_id: Unset | int = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | GetAllSalesReturnsStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllSalesReturnsResponse401
    | GetAllSalesReturnsResponse429
    | GetAllSalesReturnsResponse500
    | SalesReturnListResponse
    | None
):
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        customer_id (Union[Unset, int]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesReturnsStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesReturnsResponse401, GetAllSalesReturnsResponse429, GetAllSalesReturnsResponse500, SalesReturnListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            customer_id=customer_id,
            sales_order_id=sales_order_id,
            status=status,
            include_deleted=include_deleted,
        )
    ).parsed
