from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_supplier_address_request import CreateSupplierAddressRequest
from ...models.create_supplier_address_response_401 import (
    CreateSupplierAddressResponse401,
)
from ...models.create_supplier_address_response_422 import (
    CreateSupplierAddressResponse422,
)
from ...models.create_supplier_address_response_429 import (
    CreateSupplierAddressResponse429,
)
from ...models.create_supplier_address_response_500 import (
    CreateSupplierAddressResponse500,
)
from ...models.supplier_address import SupplierAddress
from ...types import Response


def _get_kwargs(
    *,
    body: CreateSupplierAddressRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/supplier_addresses",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
    | None
):
    if response.status_code == 200:
        response_200 = SupplierAddress.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = CreateSupplierAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 422:
        response_422 = CreateSupplierAddressResponse422.from_dict(response.json())

        return response_422
    if response.status_code == 429:
        response_429 = CreateSupplierAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = CreateSupplierAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
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
    body: CreateSupplierAddressRequest,
) -> Response[
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
]:
    """Create a supplier address

     Add an address to an existing supplier. If the new address is the first one, it is assigned as
      the default. (A Supplier can have only one address for now)

    Args:
        body (CreateSupplierAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSupplierAddressResponse401, CreateSupplierAddressResponse422, CreateSupplierAddressResponse429, CreateSupplierAddressResponse500, SupplierAddress]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierAddressRequest,
) -> (
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
    | None
):
    """Create a supplier address

     Add an address to an existing supplier. If the new address is the first one, it is assigned as
      the default. (A Supplier can have only one address for now)

    Args:
        body (CreateSupplierAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSupplierAddressResponse401, CreateSupplierAddressResponse422, CreateSupplierAddressResponse429, CreateSupplierAddressResponse500, SupplierAddress]
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierAddressRequest,
) -> Response[
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
]:
    """Create a supplier address

     Add an address to an existing supplier. If the new address is the first one, it is assigned as
      the default. (A Supplier can have only one address for now)

    Args:
        body (CreateSupplierAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[CreateSupplierAddressResponse401, CreateSupplierAddressResponse422, CreateSupplierAddressResponse429, CreateSupplierAddressResponse500, SupplierAddress]]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateSupplierAddressRequest,
) -> (
    CreateSupplierAddressResponse401
    | CreateSupplierAddressResponse422
    | CreateSupplierAddressResponse429
    | CreateSupplierAddressResponse500
    | SupplierAddress
    | None
):
    """Create a supplier address

     Add an address to an existing supplier. If the new address is the first one, it is assigned as
      the default. (A Supplier can have only one address for now)

    Args:
        body (CreateSupplierAddressRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[CreateSupplierAddressResponse401, CreateSupplierAddressResponse422, CreateSupplierAddressResponse429, CreateSupplierAddressResponse500, SupplierAddress]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
