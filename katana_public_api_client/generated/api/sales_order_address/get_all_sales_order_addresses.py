from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.get_all_sales_order_addresses_entity_type import GetAllSalesOrderAddressesEntityType
from ...models.sales_order_address_list_response import SalesOrderAddressListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    entity_type: Union[Unset, GetAllSalesOrderAddressesEntityType] = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_order_id"] = sales_order_id

    json_entity_type: Union[Unset, str] = UNSET
    if not isinstance(entity_type, Unset):
        json_entity_type = entity_type.value

    params["entity_type"] = json_entity_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/sales_order_addresses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, SalesOrderAddressListResponse]]:
    if response.status_code == 200:
        response_200 = SalesOrderAddressListResponse.from_dict(response.json())

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
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, SalesOrderAddressListResponse]]:
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
    entity_type: Union[Unset, GetAllSalesOrderAddressesEntityType] = UNSET,
) -> Response[Union[ErrorResponse, SalesOrderAddressListResponse]]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllSalesOrderAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderAddressListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        entity_type=entity_type,
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
    entity_type: Union[Unset, GetAllSalesOrderAddressesEntityType] = UNSET,
) -> Optional[Union[ErrorResponse, SalesOrderAddressListResponse]]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllSalesOrderAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderAddressListResponse]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        entity_type=entity_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    entity_type: Union[Unset, GetAllSalesOrderAddressesEntityType] = UNSET,
) -> Response[Union[ErrorResponse, SalesOrderAddressListResponse]]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllSalesOrderAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, SalesOrderAddressListResponse]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        sales_order_id=sales_order_id,
        entity_type=entity_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, int] = 50,
    page: Union[Unset, int] = 1,
    sales_order_id: Union[Unset, int] = UNSET,
    entity_type: Union[Unset, GetAllSalesOrderAddressesEntityType] = UNSET,
) -> Optional[Union[ErrorResponse, SalesOrderAddressListResponse]]:
    """List sales order addresses

     Returns a list of sales order addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        sales_order_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllSalesOrderAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, SalesOrderAddressListResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            sales_order_id=sales_order_id,
            entity_type=entity_type,
        )
    ).parsed
