import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.get_all_sales_returns_refund_status import GetAllSalesReturnsRefundStatus
from ...models.sales_return_list_response import SalesReturnListResponse


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    return_order_no: Unset | str = UNSET,
    refund_status: Unset | GetAllSalesReturnsRefundStatus = UNSET,
    return_date_min: Unset | datetime.datetime = UNSET,
    return_date_max: Unset | datetime.datetime = UNSET,
    order_created_date_min: Unset | datetime.datetime = UNSET,
    order_created_date_max: Unset | datetime.datetime = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Unset | list[int] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["sales_order_id"] = sales_order_id

    params["status"] = status

    params["include_deleted"] = include_deleted

    json_created_at_min: Unset | str = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: Unset | str = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: Unset | str = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: Unset | str = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params["return_order_no"] = return_order_no

    json_refund_status: Unset | str = UNSET
    if not isinstance(refund_status, Unset):
        json_refund_status = refund_status.value

    params["refund_status"] = json_refund_status

    json_return_date_min: Unset | str = UNSET
    if not isinstance(return_date_min, Unset):
        json_return_date_min = return_date_min.isoformat()
    params["return_date_min"] = json_return_date_min

    json_return_date_max: Unset | str = UNSET
    if not isinstance(return_date_max, Unset):
        json_return_date_max = return_date_max.isoformat()
    params["return_date_max"] = json_return_date_max

    json_order_created_date_min: Unset | str = UNSET
    if not isinstance(order_created_date_min, Unset):
        json_order_created_date_min = order_created_date_min.isoformat()
    params["order_created_date_min"] = json_order_created_date_min

    json_order_created_date_max: Unset | str = UNSET
    if not isinstance(order_created_date_max, Unset):
        json_order_created_date_max = order_created_date_max.isoformat()
    params["order_created_date_max"] = json_order_created_date_max

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_returns",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesReturnListResponse | None:
    if response.status_code == 200:
        response_200 = SalesReturnListResponse.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

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
) -> Response[ErrorResponse | SalesReturnListResponse]:
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
    status: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    return_order_no: Unset | str = UNSET,
    refund_status: Unset | GetAllSalesReturnsRefundStatus = UNSET,
    return_date_min: Unset | datetime.datetime = UNSET,
    return_date_max: Unset | datetime.datetime = UNSET,
    order_created_date_min: Unset | datetime.datetime = UNSET,
    order_created_date_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | SalesReturnListResponse]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        return_order_no (Union[Unset, str]):
        refund_status (Union[Unset, GetAllSalesReturnsRefundStatus]):
        return_date_min (Union[Unset, datetime.datetime]):
        return_date_max (Union[Unset, datetime.datetime]):
        order_created_date_min (Union[Unset, datetime.datetime]):
        order_created_date_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, SalesReturnListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        return_order_no=return_order_no,
        refund_status=refund_status,
        return_date_min=return_date_min,
        return_date_max=return_date_max,
        order_created_date_min=order_created_date_min,
        order_created_date_max=order_created_date_max,
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
    status: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    return_order_no: Unset | str = UNSET,
    refund_status: Unset | GetAllSalesReturnsRefundStatus = UNSET,
    return_date_min: Unset | datetime.datetime = UNSET,
    return_date_max: Unset | datetime.datetime = UNSET,
    order_created_date_min: Unset | datetime.datetime = UNSET,
    order_created_date_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | SalesReturnListResponse | None:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        return_order_no (Union[Unset, str]):
        refund_status (Union[Unset, GetAllSalesReturnsRefundStatus]):
        return_date_min (Union[Unset, datetime.datetime]):
        return_date_max (Union[Unset, datetime.datetime]):
        order_created_date_min (Union[Unset, datetime.datetime]):
        order_created_date_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, SalesReturnListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        ids=ids,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        return_order_no=return_order_no,
        refund_status=refund_status,
        return_date_min=return_date_min,
        return_date_max=return_date_max,
        order_created_date_min=order_created_date_min,
        order_created_date_max=order_created_date_max,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    ids: Unset | list[int] = UNSET,
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    return_order_no: Unset | str = UNSET,
    refund_status: Unset | GetAllSalesReturnsRefundStatus = UNSET,
    return_date_min: Unset | datetime.datetime = UNSET,
    return_date_max: Unset | datetime.datetime = UNSET,
    order_created_date_min: Unset | datetime.datetime = UNSET,
    order_created_date_max: Unset | datetime.datetime = UNSET,
) -> Response[ErrorResponse | SalesReturnListResponse]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        return_order_no (Union[Unset, str]):
        refund_status (Union[Unset, GetAllSalesReturnsRefundStatus]):
        return_date_min (Union[Unset, datetime.datetime]):
        return_date_max (Union[Unset, datetime.datetime]):
        order_created_date_min (Union[Unset, datetime.datetime]):
        order_created_date_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[ErrorResponse, SalesReturnListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        ids=ids,
        sales_order_id=sales_order_id,
        status=status,
        include_deleted=include_deleted,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        return_order_no=return_order_no,
        refund_status=refund_status,
        return_date_min=return_date_min,
        return_date_max=return_date_max,
        order_created_date_min=order_created_date_min,
        order_created_date_max=order_created_date_max,
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
    status: Unset | str = UNSET,
    include_deleted: Unset | bool = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    return_order_no: Unset | str = UNSET,
    refund_status: Unset | GetAllSalesReturnsRefundStatus = UNSET,
    return_date_min: Unset | datetime.datetime = UNSET,
    return_date_max: Unset | datetime.datetime = UNSET,
    order_created_date_min: Unset | datetime.datetime = UNSET,
    order_created_date_max: Unset | datetime.datetime = UNSET,
) -> ErrorResponse | SalesReturnListResponse | None:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with the most recent sales return appearing first.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        include_deleted (Union[Unset, bool]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        return_order_no (Union[Unset, str]):
        refund_status (Union[Unset, GetAllSalesReturnsRefundStatus]):
        return_date_min (Union[Unset, datetime.datetime]):
        return_date_max (Union[Unset, datetime.datetime]):
        order_created_date_min (Union[Unset, datetime.datetime]):
        order_created_date_max (Union[Unset, datetime.datetime]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[ErrorResponse, SalesReturnListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            ids=ids,
            sales_order_id=sales_order_id,
            status=status,
            include_deleted=include_deleted,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            return_order_no=return_order_no,
            refund_status=refund_status,
            return_date_min=return_date_min,
            return_date_max=return_date_max,
            order_created_date_min=order_created_date_min,
            order_created_date_max=order_created_date_max,
        )
    ).parsed
