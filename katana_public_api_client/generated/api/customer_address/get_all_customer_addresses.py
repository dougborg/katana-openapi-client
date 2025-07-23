from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.customer_address_list_response import CustomerAddressListResponse
from ...models.get_all_customer_addresses_entity_type import (
    GetAllCustomerAddressesEntityType,
)
from ...models.get_all_customer_addresses_response_401 import (
    GetAllCustomerAddressesResponse401,
)
from ...models.get_all_customer_addresses_response_429 import (
    GetAllCustomerAddressesResponse429,
)
from ...models.get_all_customer_addresses_response_500 import (
    GetAllCustomerAddressesResponse500,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    customer_id: Unset | int = UNSET,
    entity_type: Unset | GetAllCustomerAddressesEntityType = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["limit"] = limit

    params["page"] = page

    params["customer_id"] = customer_id

    json_entity_type: Unset | str = UNSET
    if not isinstance(entity_type, Unset):
        json_entity_type = entity_type.value

    params["entity_type"] = json_entity_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/customer_addresses",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
    | None
):
    if response.status_code == 200:
        response_200 = CustomerAddressListResponse.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetAllCustomerAddressesResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 429:
        response_429 = GetAllCustomerAddressesResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = GetAllCustomerAddressesResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
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
    customer_id: Unset | int = UNSET,
    entity_type: Unset | GetAllCustomerAddressesEntityType = UNSET,
) -> Response[
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
]:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        customer_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllCustomerAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddressListResponse, GetAllCustomerAddressesResponse401, GetAllCustomerAddressesResponse429, GetAllCustomerAddressesResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        customer_id=customer_id,
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
    customer_id: Unset | int = UNSET,
    entity_type: Unset | GetAllCustomerAddressesEntityType = UNSET,
) -> (
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
    | None
):
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        customer_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllCustomerAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddressListResponse, GetAllCustomerAddressesResponse401, GetAllCustomerAddressesResponse429, GetAllCustomerAddressesResponse500]
    """

    return sync_detailed(
        client=client,
        limit=limit,
        page=page,
        customer_id=customer_id,
        entity_type=entity_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    customer_id: Unset | int = UNSET,
    entity_type: Unset | GetAllCustomerAddressesEntityType = UNSET,
) -> Response[
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
]:
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        customer_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllCustomerAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CustomerAddressListResponse, GetAllCustomerAddressesResponse401, GetAllCustomerAddressesResponse429, GetAllCustomerAddressesResponse500]]
    """

    kwargs = _get_kwargs(
        limit=limit,
        page=page,
        customer_id=customer_id,
        entity_type=entity_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    limit: Unset | int = 50,
    page: Unset | int = 1,
    customer_id: Unset | int = UNSET,
    entity_type: Unset | GetAllCustomerAddressesEntityType = UNSET,
) -> (
    CustomerAddressListResponse
    | GetAllCustomerAddressesResponse401
    | GetAllCustomerAddressesResponse429
    | GetAllCustomerAddressesResponse500
    | None
):
    """List customer addresses

     Returns a list of customer addresses.

    Args:
        limit (Union[Unset, int]):  Default: 50.
        page (Union[Unset, int]):  Default: 1.
        customer_id (Union[Unset, int]):
        entity_type (Union[Unset, GetAllCustomerAddressesEntityType]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CustomerAddressListResponse, GetAllCustomerAddressesResponse401, GetAllCustomerAddressesResponse429, GetAllCustomerAddressesResponse500]
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            page=page,
            customer_id=customer_id,
            entity_type=entity_type,
        )
    ).parsed
