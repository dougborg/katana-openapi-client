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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    tracking_carrier: str | Unset = UNSET,
    tracking_method: str | Unset = UNSET,
    tracking_number: str | Unset = UNSET,
    tracking_url: str | Unset = UNSET,
    picked_date_min: str | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    tracking_carrier: str | Unset = UNSET,
    tracking_method: str | Unset = UNSET,
    tracking_number: str | Unset = UNSET,
    tracking_url: str | Unset = UNSET,
    picked_date_min: str | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderFulfillmentListResponse]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        sales_order_id (int | Unset):
        status (str | Unset):
        tracking_carrier (str | Unset):
        tracking_method (str | Unset):
        tracking_number (str | Unset):
        tracking_url (str | Unset):
        picked_date_min (str | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderFulfillmentListResponse]
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    tracking_carrier: str | Unset = UNSET,
    tracking_method: str | Unset = UNSET,
    tracking_number: str | Unset = UNSET,
    tracking_url: str | Unset = UNSET,
    picked_date_min: str | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> ErrorResponse | SalesOrderFulfillmentListResponse | None:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        sales_order_id (int | Unset):
        status (str | Unset):
        tracking_carrier (str | Unset):
        tracking_method (str | Unset):
        tracking_number (str | Unset):
        tracking_url (str | Unset):
        picked_date_min (str | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderFulfillmentListResponse
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    tracking_carrier: str | Unset = UNSET,
    tracking_method: str | Unset = UNSET,
    tracking_number: str | Unset = UNSET,
    tracking_url: str | Unset = UNSET,
    picked_date_min: str | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> Response[ErrorResponse | SalesOrderFulfillmentListResponse]:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        sales_order_id (int | Unset):
        status (str | Unset):
        tracking_carrier (str | Unset):
        tracking_method (str | Unset):
        tracking_number (str | Unset):
        tracking_url (str | Unset):
        picked_date_min (str | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[ErrorResponse | SalesOrderFulfillmentListResponse]
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
    limit: int | Unset = UNSET,
    page: int | Unset = UNSET,
    sales_order_id: int | Unset = UNSET,
    status: str | Unset = UNSET,
    tracking_carrier: str | Unset = UNSET,
    tracking_method: str | Unset = UNSET,
    tracking_number: str | Unset = UNSET,
    tracking_url: str | Unset = UNSET,
    picked_date_min: str | Unset = UNSET,
    created_at_min: datetime.datetime | Unset = UNSET,
    created_at_max: datetime.datetime | Unset = UNSET,
    updated_at_min: datetime.datetime | Unset = UNSET,
    updated_at_max: datetime.datetime | Unset = UNSET,
    include_deleted: bool | Unset = UNSET,
) -> ErrorResponse | SalesOrderFulfillmentListResponse | None:
    """List sales order fulfillments

     Returns a list of sales order fulfillments.

    Args:
        limit (int | Unset):  Default: 50.
        page (int | Unset):  Default: 1.
        sales_order_id (int | Unset):
        status (str | Unset):
        tracking_carrier (str | Unset):
        tracking_method (str | Unset):
        tracking_number (str | Unset):
        tracking_url (str | Unset):
        picked_date_min (str | Unset):
        created_at_min (datetime.datetime | Unset):
        created_at_max (datetime.datetime | Unset):
        updated_at_min (datetime.datetime | Unset):
        updated_at_max (datetime.datetime | Unset):
        include_deleted (bool | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        ErrorResponse | SalesOrderFulfillmentListResponse
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
