from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.update_customer_address_body import UpdateCustomerAddressBody
from ...models.update_customer_address_response_401 import (
    UpdateCustomerAddressResponse401,
)
from ...models.update_customer_address_response_404 import (
    UpdateCustomerAddressResponse404,
)
from ...models.update_customer_address_response_429 import (
    UpdateCustomerAddressResponse429,
)
from ...models.update_customer_address_response_500 import (
    UpdateCustomerAddressResponse500,
)
from ...types import Response


def _get_kwargs(
    id: int,
    *,
    body: UpdateCustomerAddressBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/customer_addresses/{id}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
    | None
):
    if response.status_code == 200:
        response_200 = cast(Any, None)
        return response_200
    if response.status_code == 401:
        response_401 = UpdateCustomerAddressResponse401.from_dict(response.json())

        return response_401
    if response.status_code == 404:
        response_404 = UpdateCustomerAddressResponse404.from_dict(response.json())

        return response_404
    if response.status_code == 429:
        response_429 = UpdateCustomerAddressResponse429.from_dict(response.json())

        return response_429
    if response.status_code == 500:
        response_500 = UpdateCustomerAddressResponse500.from_dict(response.json())

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
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
    body: UpdateCustomerAddressBody,
) -> Response[
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
]:
    """Update a customer address

     Updates a customer address.

    Args:
        id (int):
        body (UpdateCustomerAddressBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UpdateCustomerAddressResponse401, UpdateCustomerAddressResponse404, UpdateCustomerAddressResponse429, UpdateCustomerAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCustomerAddressBody,
) -> (
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
    | None
):
    """Update a customer address

     Updates a customer address.

    Args:
        id (int):
        body (UpdateCustomerAddressBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UpdateCustomerAddressResponse401, UpdateCustomerAddressResponse404, UpdateCustomerAddressResponse429, UpdateCustomerAddressResponse500]
    """

    return sync_detailed(
        id=id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCustomerAddressBody,
) -> Response[
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
]:
    """Update a customer address

     Updates a customer address.

    Args:
        id (int):
        body (UpdateCustomerAddressBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[Any, UpdateCustomerAddressResponse401, UpdateCustomerAddressResponse404, UpdateCustomerAddressResponse429, UpdateCustomerAddressResponse500]]
    """

    kwargs = _get_kwargs(
        id=id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateCustomerAddressBody,
) -> (
    Any
    | UpdateCustomerAddressResponse401
    | UpdateCustomerAddressResponse404
    | UpdateCustomerAddressResponse429
    | UpdateCustomerAddressResponse500
    | None
):
    """Update a customer address

     Updates a customer address.

    Args:
        id (int):
        body (UpdateCustomerAddressBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[Any, UpdateCustomerAddressResponse401, UpdateCustomerAddressResponse404, UpdateCustomerAddressResponse429, UpdateCustomerAddressResponse500]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
            body=body,
        )
    ).parsed
