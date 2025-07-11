from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_sales_order_accounting_metadata_response_401 import (
    GetSalesOrderAccountingMetadataResponse401,
)
from ...models.get_sales_order_accounting_metadata_response_429 import (
    GetSalesOrderAccountingMetadataResponse429,
)
from ...models.get_sales_order_accounting_metadata_response_500 import (
    GetSalesOrderAccountingMetadataResponse500,
)
from ...models.sales_order_accounting_metadata_list_response import (
    SalesOrderAccountingMetadataListResponse,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    sales_order_id: Union[Unset, int] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    json_ids: Union[Unset, list[int]] = UNSET
    if not isinstance(ids, Unset):
        json_ids = ids

    params["ids"] = json_ids

    params["sales_order_id"] = sales_order_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_accounting_metadata",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
    ]
]:
    if response.status_code == 200:
        response_200 = SalesOrderAccountingMetadataListResponse.from_dict(
            response.json()
        )

        return response_200
    if response.status_code == 401:
        response_401 = GetSalesOrderAccountingMetadataResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetSalesOrderAccountingMetadataResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetSalesOrderAccountingMetadataResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
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
    ids: Union[Unset, list[int]] = UNSET,
    sales_order_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
    ]
]:
    """List sales order accounting metadata

     Retrieves accounting metadata for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSalesOrderAccountingMetadataResponse401, GetSalesOrderAccountingMetadataResponse429, GetSalesOrderAccountingMetadataResponse500, SalesOrderAccountingMetadataListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    sales_order_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
    ]
]:
    """List sales order accounting metadata

     Retrieves accounting metadata for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSalesOrderAccountingMetadataResponse401, GetSalesOrderAccountingMetadataResponse429, GetSalesOrderAccountingMetadataResponse500, SalesOrderAccountingMetadataListResponse]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    sales_order_id: Union[Unset, int] = UNSET,
) -> Response[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
    ]
]:
    """List sales order accounting metadata

     Retrieves accounting metadata for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[GetSalesOrderAccountingMetadataResponse401, GetSalesOrderAccountingMetadataResponse429, GetSalesOrderAccountingMetadataResponse500, SalesOrderAccountingMetadataListResponse]]
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
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    ids: Union[Unset, list[int]] = UNSET,
    sales_order_id: Union[Unset, int] = UNSET,
) -> Optional[
    Union[
        GetSalesOrderAccountingMetadataResponse401,
        GetSalesOrderAccountingMetadataResponse429,
        GetSalesOrderAccountingMetadataResponse500,
        SalesOrderAccountingMetadataListResponse,
    ]
]:
    """List sales order accounting metadata

     Retrieves accounting metadata for sales orders.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        ids (Union[Unset, list[int]]):
        sales_order_id (Union[Unset, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[GetSalesOrderAccountingMetadataResponse401, GetSalesOrderAccountingMetadataResponse429, GetSalesOrderAccountingMetadataResponse500, SalesOrderAccountingMetadataListResponse]
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
