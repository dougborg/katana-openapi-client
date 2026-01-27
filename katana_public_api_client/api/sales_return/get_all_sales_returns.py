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
    limit: int | Unset = 50,
    page: int | Unset = 1,
    ids: list[int] | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    return_order_no: str | Unset = UNSET,
    refund_status: GetAllSalesReturnsRefundStatus | Unset = UNSET,
    return_date_min: datetime.datetime | Unset = UNSET,
    return_date_max: datetime.datetime | Unset = UNSET,
    order_created_date_min: datetime.datetime | Unset = UNSET,
    order_created_date_max: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: list[int] | Unset = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["sales_order_id"] = sales_order_id

    params["status"] = status

    params["include_deleted"] = include_deleted

    json_created_at_min: str | Unset = UNSET
    if not isinstance(created_at_min, Unset):
        json_created_at_min = created_at_min.isoformat()
    params["created_at_min"] = json_created_at_min

    json_created_at_max: str | Unset = UNSET
    if not isinstance(created_at_max, Unset):
        json_created_at_max = created_at_max.isoformat()
    params["created_at_max"] = json_created_at_max

    json_updated_at_min: str | Unset = UNSET
    if not isinstance(updated_at_min, Unset):
        json_updated_at_min = updated_at_min.isoformat()
    params["updated_at_min"] = json_updated_at_min

    json_updated_at_max: str | Unset = UNSET
    if not isinstance(updated_at_max, Unset):
        json_updated_at_max = updated_at_max.isoformat()
    params["updated_at_max"] = json_updated_at_max

    params["return_order_no"] = return_order_no

    json_refund_status: str | Unset = UNSET
    if not isinstance(refund_status, Unset):
        json_refund_status = refund_status.value

    params["refund_status"] = json_refund_status

    json_return_date_min: str | Unset = UNSET
    if not isinstance(return_date_min, Unset):
        json_return_date_min = return_date_min.isoformat()
    params["return_date_min"] = json_return_date_min

    json_return_date_max: str | Unset = UNSET
    if not isinstance(return_date_max, Unset):
        json_return_date_max = return_date_max.isoformat()
    params["return_date_max"] = json_return_date_max

    json_order_created_date_min: str | Unset = UNSET
    if not isinstance(order_created_date_min, Unset):
        json_order_created_date_min = order_created_date_min.isoformat()
    params["order_created_date_min"] = json_order_created_date_min

    json_order_created_date_max: str | Unset = UNSET
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
    limit: int | Unset = 50,
    page: int | Unset = 1,
    ids: list[int] | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    return_order_no: str | Unset = UNSET,
    refund_status: GetAllSalesReturnsRefundStatus | Unset = UNSET,
    return_date_min: datetime.datetime | Unset = UNSET,
    return_date_max: datetime.datetime | Unset = UNSET,
    order_created_date_min: datetime.datetime | Unset = UNSET,
    order_created_date_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesReturnListResponse]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with
    the most recent sales return appearing first.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        sales_order_id (int | Unset):
        status (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        return_order_no (str | Unset):
        refund_status (GetAllSalesReturnsRefundStatus | Unset):
        return_date_min (datetime.datetime | Unset):
        return_date_max (datetime.datetime | Unset):
        order_created_date_min (datetime.datetime | Unset):
        order_created_date_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesReturnListResponse]
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
    limit: int | Unset = 50,
    page: int | Unset = 1,
    ids: list[int] | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    return_order_no: str | Unset = UNSET,
    refund_status: GetAllSalesReturnsRefundStatus | Unset = UNSET,
    return_date_min: datetime.datetime | Unset = UNSET,
    return_date_max: datetime.datetime | Unset = UNSET,
    order_created_date_min: datetime.datetime | Unset = UNSET,
    order_created_date_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesReturnListResponse | None:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with
    the most recent sales return appearing first.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        sales_order_id (int | Unset):
        status (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        return_order_no (str | Unset):
        refund_status (GetAllSalesReturnsRefundStatus | Unset):
        return_date_min (datetime.datetime | Unset):
        return_date_max (datetime.datetime | Unset):
        order_created_date_min (datetime.datetime | Unset):
        order_created_date_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesReturnListResponse
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
    limit: int | Unset = 50,
    page: int | Unset = 1,
    ids: list[int] | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    return_order_no: str | Unset = UNSET,
    refund_status: GetAllSalesReturnsRefundStatus | Unset = UNSET,
    return_date_min: datetime.datetime | Unset = UNSET,
    return_date_max: datetime.datetime | Unset = UNSET,
    order_created_date_min: datetime.datetime | Unset = UNSET,
    order_created_date_max: datetime.datetime | Unset = UNSET,
) -> Response[ErrorResponse | SalesReturnListResponse]:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with
    the most recent sales return appearing first.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        sales_order_id (int | Unset):
        status (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        return_order_no (str | Unset):
        refund_status (GetAllSalesReturnsRefundStatus | Unset):
        return_date_min (datetime.datetime | Unset):
        return_date_max (datetime.datetime | Unset):
        order_created_date_min (datetime.datetime | Unset):
        order_created_date_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesReturnListResponse]
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
    limit: int | Unset = 50,
    page: int | Unset = 1,
    ids: list[int] | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    return_order_no: str | Unset = UNSET,
    refund_status: GetAllSalesReturnsRefundStatus | Unset = UNSET,
    return_date_min: datetime.datetime | Unset = UNSET,
    return_date_max: datetime.datetime | Unset = UNSET,
    order_created_date_min: datetime.datetime | Unset = UNSET,
    order_created_date_max: datetime.datetime | Unset = UNSET,
) -> ErrorResponse | SalesReturnListResponse | None:
    """List all sales returns

     Returns a list of sales returns you've previously created. The sales returns are returned in sorted
    order, with
    the most recent sales return appearing first.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        ids (list[int] | Unset):
        sales_order_id (int | Unset):
        status (str | Unset):
        include_deleted (bool | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        return_order_no (str | Unset):
        refund_status (GetAllSalesReturnsRefundStatus | Unset):
        return_date_min (datetime.datetime | Unset):
        return_date_max (datetime.datetime | Unset):
        order_created_date_min (datetime.datetime | Unset):
        order_created_date_max (datetime.datetime | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesReturnListResponse
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
