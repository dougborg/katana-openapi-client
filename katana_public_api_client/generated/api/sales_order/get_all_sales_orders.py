from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_orders_response_401 import GetAllSalesOrdersResponse401
from ...models.get_all_sales_orders_response_429 import GetAllSalesOrdersResponse429
from ...models.get_all_sales_orders_response_500 import GetAllSalesOrdersResponse500
from ...models.get_all_sales_orders_status import GetAllSalesOrdersStatus
from ...models.sales_order_list_response import SalesOrderListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    customer_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSalesOrdersStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["order_no"] = order_no

    params["customer_id"] = customer_id

    params["location_id"] = location_id

    json_status: Unset | str = UNSET
    if not isinstance(status, Unset):
        json_status = status.value

    params["status"] = json_status

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_orders",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SalesOrderListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesOrdersResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesOrdersResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesOrdersResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
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
    order_no: Unset | str = UNSET,
    customer_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSalesOrdersStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
]:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        customer_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesOrdersStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesOrdersResponse401, GetAllSalesOrdersResponse429, GetAllSalesOrdersResponse500, SalesOrderListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
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
    order_no: Unset | str = UNSET,
    customer_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSalesOrdersStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
    | None
):
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        customer_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesOrdersStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesOrdersResponse401, GetAllSalesOrdersResponse429, GetAllSalesOrdersResponse500, SalesOrderListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
        status=status,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    order_no: Unset | str = UNSET,
    customer_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSalesOrdersStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
]:
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        customer_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesOrdersStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetAllSalesOrdersResponse401, GetAllSalesOrdersResponse429, GetAllSalesOrdersResponse500, SalesOrderListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
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
    order_no: Unset | str = UNSET,
    customer_id: Unset | int = UNSET,
    location_id: Unset | int = UNSET,
    status: Unset | GetAllSalesOrdersStatus = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> (
    GetAllSalesOrdersResponse401
    | GetAllSalesOrdersResponse429
    | GetAllSalesOrdersResponse500
    | SalesOrderListResponse
    | None
):
    """List all sales orders

     Returns a list of sales orders you've previously created.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        order_no (Union[Unset, str]):
        customer_id (Union[Unset, int]):
        location_id (Union[Unset, int]):
        status (Union[Unset, GetAllSalesOrdersStatus]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetAllSalesOrdersResponse401, GetAllSalesOrdersResponse429, GetAllSalesOrdersResponse500, SalesOrderListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            order_no=order_no,
            customer_id=customer_id,
            location_id=location_id,
            status=status,
            include_deleted=include_deleted,
        )
    ).parsed
