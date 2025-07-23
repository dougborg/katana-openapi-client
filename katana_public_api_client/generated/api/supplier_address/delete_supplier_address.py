from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_supplier_address_response_401 import (
    DeleteSupplierAddressResponse401,
)
from ...models.delete_supplier_address_response_404 import (
    DeleteSupplierAddressResponse404,
)
from ...models.delete_supplier_address_response_429 import (
    DeleteSupplierAddressResponse429,
)
from ...models.delete_supplier_address_response_500 import (
    DeleteSupplierAddressResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/supplier_addresses/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
    | None
):
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204
    if response.status_code == 401:
        response_401 = DeleteSupplierAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = DeleteSupplierAddressResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = DeleteSupplierAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = DeleteSupplierAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
]:
    """Delete a supplier address

     Deletes a supplier address by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteSupplierAddressResponse401, DeleteSupplierAddressResponse404, DeleteSupplierAddressResponse429, DeleteSupplierAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
    | None
):
    """Delete a supplier address

     Deletes a supplier address by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteSupplierAddressResponse401, DeleteSupplierAddressResponse404, DeleteSupplierAddressResponse429, DeleteSupplierAddressResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
]:
    """Delete a supplier address

     Deletes a supplier address by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, DeleteSupplierAddressResponse401, DeleteSupplierAddressResponse404, DeleteSupplierAddressResponse429, DeleteSupplierAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
) -> (
    Any
    | DeleteSupplierAddressResponse401
    | DeleteSupplierAddressResponse404
    | DeleteSupplierAddressResponse429
    | DeleteSupplierAddressResponse500
    | None
):
    """Delete a supplier address

     Deletes a supplier address by id.

    Args:
        id (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, DeleteSupplierAddressResponse401, DeleteSupplierAddressResponse404, DeleteSupplierAddressResponse429, DeleteSupplierAddressResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
