from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_all_sales_order_addresses_entity_type import (
    GetAllSalesOrderAddressesEntityType,
)
from ...models.get_all_sales_order_addresses_response_401 import (
    GetAllSalesOrderAddressesResponse401,
)
from ...models.get_all_sales_order_addresses_response_429 import (
    GetAllSalesOrderAddressesResponse429,
)
from ...models.get_all_sales_order_addresses_response_500 import (
    GetAllSalesOrderAddressesResponse500,
)
from ...models.sales_order_address_list_response import SalesOrderAddressListResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    entity_type: Unset | GetAllSalesOrderAddressesEntityType = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["sales_order_id"] = sales_order_id

    json_entity_type: Unset | str = UNSET
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
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
    | None
):
    if response.status_code == 200:
        response_200 = SalesOrderAddressListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllSalesOrderAddressesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllSalesOrderAddressesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllSalesOrderAddressesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
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
    sales_order_id: Unset | int = UNSET,
    entity_type: Unset | GetAllSalesOrderAddressesEntityType = UNSET,
) -> Response[
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
]:
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
        Response[Union[GetAllSalesOrderAddressesResponse401, GetAllSalesOrderAddressesResponse429, GetAllSalesOrderAddressesResponse500, SalesOrderAddressListResponse]]
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
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    entity_type: Unset | GetAllSalesOrderAddressesEntityType = UNSET,
) -> (
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
    | None
):
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
        Union[GetAllSalesOrderAddressesResponse401, GetAllSalesOrderAddressesResponse429, GetAllSalesOrderAddressesResponse500, SalesOrderAddressListResponse]
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
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    entity_type: Unset | GetAllSalesOrderAddressesEntityType = UNSET,
) -> Response[
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
]:
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
        Response[Union[GetAllSalesOrderAddressesResponse401, GetAllSalesOrderAddressesResponse429, GetAllSalesOrderAddressesResponse500, SalesOrderAddressListResponse]]
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
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    sales_order_id: Unset | int = UNSET,
    entity_type: Unset | GetAllSalesOrderAddressesEntityType = UNSET,
) -> (
    GetAllSalesOrderAddressesResponse401
    | GetAllSalesOrderAddressesResponse429
    | GetAllSalesOrderAddressesResponse500
    | SalesOrderAddressListResponse
    | None
):
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
        Union[GetAllSalesOrderAddressesResponse401, GetAllSalesOrderAddressesResponse429, GetAllSalesOrderAddressesResponse500, SalesOrderAddressListResponse]
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
