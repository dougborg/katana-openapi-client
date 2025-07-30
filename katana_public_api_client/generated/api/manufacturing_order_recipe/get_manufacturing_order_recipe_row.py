from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_manufacturing_order_recipe_row_response_401 import (
    GetManufacturingOrderRecipeRowResponse401,
)
from ...models.get_manufacturing_order_recipe_row_response_429 import (
    GetManufacturingOrderRecipeRowResponse429,
)
from ...models.get_manufacturing_order_recipe_row_response_500 import (
    GetManufacturingOrderRecipeRowResponse500,
)
from ...models.manufacturing_order_recipe_row import ManufacturingOrderRecipeRow
from ...types import Response


def _get_kwargs(
    id: float,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/manufacturing_order_recipe_rows/{id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> (
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    if response.status_code == 200:
        response_200 = ManufacturingOrderRecipeRow.from_dict(response.json())

        return response_200
    if response.status_code == 401:
        response_401 = GetManufacturingOrderRecipeRowResponse401.from_dict(
            response.json()
        )

        return response_401
    if response.status_code == 429:
        response_429 = GetManufacturingOrderRecipeRowResponse429.from_dict(
            response.json()
        )

        return response_429
    if response.status_code == 500:
        response_500 = GetManufacturingOrderRecipeRowResponse500.from_dict(
            response.json()
        )

        return response_500
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
]:
    """Retrieve a manufacturing order recipe row

     Retrieves the details of an existing manufacturing order recipe row.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderRecipeRowResponse401, GetManufacturingOrderRecipeRowResponse429, GetManufacturingOrderRecipeRowResponse500, ManufacturingOrderRecipeRow]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    """Retrieve a manufacturing order recipe row

     Retrieves the details of an existing manufacturing order recipe row.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderRecipeRowResponse401, GetManufacturingOrderRecipeRowResponse429, GetManufacturingOrderRecipeRowResponse500, ManufacturingOrderRecipeRow]
    """

    return sync_detailed(
        id=id,
        client=client,
    ).parsed


async def asyncio_detailed(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
]:
    """Retrieve a manufacturing order recipe row

     Retrieves the details of an existing manufacturing order recipe row.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Response[Union[GetManufacturingOrderRecipeRowResponse401, GetManufacturingOrderRecipeRowResponse429, GetManufacturingOrderRecipeRowResponse500, ManufacturingOrderRecipeRow]]
    """

    kwargs = _get_kwargs(
        id=id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: float,
    *,
    client: AuthenticatedClient | Client,
) -> (
    GetManufacturingOrderRecipeRowResponse401
    | GetManufacturingOrderRecipeRowResponse429
    | GetManufacturingOrderRecipeRowResponse500
    | ManufacturingOrderRecipeRow
    | None
):
    """Retrieve a manufacturing order recipe row

     Retrieves the details of an existing manufacturing order recipe row.

    Args:
        id (float):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.


    Returns:
        Union[GetManufacturingOrderRecipeRowResponse401, GetManufacturingOrderRecipeRowResponse429, GetManufacturingOrderRecipeRowResponse500, ManufacturingOrderRecipeRow]
    """

    return (
        await asyncio_detailed(
            id=id,
            client=client,
        )
    ).parsed
