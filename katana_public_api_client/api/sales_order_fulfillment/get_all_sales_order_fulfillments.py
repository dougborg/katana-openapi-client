import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...client_types import UNSET, Response, Unset
from ...models.error_response import ErrorResponse
from ...models.sales_order_fulfillment_list_response import (
    SalesOrderFulfillmentListResponse,
)


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    tracking_carrier: Unset | str = UNSET,
    tracking_method: Unset | str = UNSET,
    tracking_number: Unset | str = UNSET,
    tracking_url: Unset | str = UNSET,
    picked_date_min: Unset | str = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_order_id"] = sales_order_id

    params["status"] = status

    params["tracking_carrier"] = tracking_carrier

    params["tracking_method"] = tracking_method

    params["tracking_number"] = tracking_number

    params["tracking_url"] = tracking_url

    params["picked_date_min"] = picked_date_min

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

    params["include_deleted"] = include_deleted

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_fulfillments",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | SalesOrderFulfillmentListResponse | None:
    if response.status_code == 200:
        response_200 = SalesOrderFulfillmentListResponse.from_dict(response.json())

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
) -> Response[ErrorResponse | SalesOrderFulfillmentListResponse]:
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
    status: Unset | str = UNSET,
    tracking_carrier: Unset | str = UNSET,
    tracking_method: Unset | str = UNSET,
    tracking_number: Unset | str = UNSET,
    tracking_url: Unset | str = UNSET,
    picked_date_min: Unset | str = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[ErrorResponse | SalesOrderFulfillmentListResponse]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        tracking_carrier (Union[Unset, str]):
        tracking_method (Union[Unset, str]):
        tracking_number (Union[Unset, str]):
        tracking_url (Union[Unset, str]):
        picked_date_min (Union[Unset, str]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderFulfillmentListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        status=status,
        tracking_carrier=tracking_carrier,
        tracking_method=tracking_method,
        tracking_number=tracking_number,
        tracking_url=tracking_url,
        picked_date_min=picked_date_min,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
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
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    tracking_carrier: Unset | str = UNSET,
    tracking_method: Unset | str = UNSET,
    tracking_number: Unset | str = UNSET,
    tracking_url: Unset | str = UNSET,
    picked_date_min: Unset | str = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> ErrorResponse | SalesOrderFulfillmentListResponse | None:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        tracking_carrier (Union[Unset, str]):
        tracking_method (Union[Unset, str]):
        tracking_number (Union[Unset, str]):
        tracking_url (Union[Unset, str]):
        picked_date_min (Union[Unset, str]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderFulfillmentListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        status=status,
        tracking_carrier=tracking_carrier,
        tracking_method=tracking_method,
        tracking_number=tracking_number,
        tracking_url=tracking_url,
        picked_date_min=picked_date_min,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    tracking_carrier: Unset | str = UNSET,
    tracking_method: Unset | str = UNSET,
    tracking_number: Unset | str = UNSET,
    tracking_url: Unset | str = UNSET,
    picked_date_min: Unset | str = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> Response[ErrorResponse | SalesOrderFulfillmentListResponse]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        tracking_carrier (Union[Unset, str]):
        tracking_method (Union[Unset, str]):
        tracking_number (Union[Unset, str]):
        tracking_url (Union[Unset, str]):
        picked_date_min (Union[Unset, str]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderFulfillmentListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        status=status,
        tracking_carrier=tracking_carrier,
        tracking_method=tracking_method,
        tracking_number=tracking_number,
        tracking_url=tracking_url,
        picked_date_min=picked_date_min,
        created_at_min=created_at_min,
        created_at_max=created_at_max,
        updated_at_min=updated_at_min,
        updated_at_max=updated_at_max,
        include_deleted=include_deleted,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    status: Unset | str = UNSET,
    tracking_carrier: Unset | str = UNSET,
    tracking_method: Unset | str = UNSET,
    tracking_number: Unset | str = UNSET,
    tracking_url: Unset | str = UNSET,
    picked_date_min: Unset | str = UNSET,
    created_at_min: Unset | datetime.datetime = UNSET,
    created_at_max: Unset | datetime.datetime = UNSET,
    updated_at_min: Unset | datetime.datetime = UNSET,
    updated_at_max: Unset | datetime.datetime = UNSET,
    include_deleted: Unset | bool = UNSET,
) -> ErrorResponse | SalesOrderFulfillmentListResponse | None:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        status (Union[Unset, str]):
        tracking_carrier (Union[Unset, str]):
        tracking_method (Union[Unset, str]):
        tracking_number (Union[Unset, str]):
        tracking_url (Union[Unset, str]):
        picked_date_min (Union[Unset, str]):
        created_at_min (Union[Unset, datetime.datetime]):
        created_at_max (Union[Unset, datetime.datetime]):
        updated_at_min (Union[Unset, datetime.datetime]):
        updated_at_max (Union[Unset, datetime.datetime]):
        include_deleted (Union[Unset, bool]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderFulfillmentListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            sales_order_id=sales_order_id,
            status=status,
            tracking_carrier=tracking_carrier,
            tracking_method=tracking_method,
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            picked_date_min=picked_date_min,
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
            include_deleted=include_deleted,
        )
    ).parsed
